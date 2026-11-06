"""Parser semantics, rejection boundaries and native generator routing, without Chrome."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/ai-diagrams/scripts'))
import importar as cli
import importar_dados as data
import importar_mermaid as mm


class ImportTests(unittest.TestCase):
    def test_all_localized_examples(self):
        expected = {'flowchart': 'bpmn', 'raias': 'raias', 'sequence': 'sequencia', 'state': 'estados', 'er': 'der',
                    'process': 'bpmn', 'schema': 'der', 'catalog': 'catalogo', 'comparison': 'comparacao'}
        for language in ('en', 'es', 'pt-BR'):
            for file in (ROOT / 'exemplos/importar' / language).iterdir():
                if not file.is_file() or file.suffix == '.json': continue
                with self.subTest(file=file):
                    kind, model = cli.parse(file, language)
                    self.assertEqual(kind, expected[file.stem])
                    if kind not in ('catalogo', 'comparacao'): self.assertEqual(model['idioma'], language)
        _, model = cli.parse(ROOT / 'exemplos/importar/en/er.mmd', 'en')
        self.assertEqual(model['tabelas']['public.ORDER']['colunas'][1], ['customer_id', 'uuid', 'FK', 'public.CUSTOMER', True])

    def test_plain_flowchart_gets_boundaries(self):
        kind, m = mm.parse('graph LR\nA[Request] --> B[Review]', cli.base('en'))
        self.assertEqual(kind, 'bpmn')
        self.assertEqual([n['type'] for n in m['nodes']], ['task', 'task', 'startEvent', 'endEvent'])
        self.assertEqual(len(m['flows']), 3)

    def test_sequence_nested_fragments(self):
        _, m = mm.parse('sequenceDiagram\nparticipant A\nparticipant B\nalt enabled\nloop retries\nA->>B: send\nend\nelse off\nB-->>A: stop\nend', cli.base('en'))
        self.assertEqual(m['mensagens'][0]['ramos'][0]['mensagens'][0]['fragmento'], 'loop')
        self.assertEqual(m['mensagens'][0]['ramos'][1]['mensagens'][0]['tipo'], 'resposta')

    def test_mermaid_errors_have_exact_lines(self):
        cases = [('flowchart LR\nA --> B\nstyle A fill:red', 3),
                 ('sequenceDiagram\nA->>B: hi\nactivate B', 3),
                 ('stateDiagram-v2\n[*] --> A\nstate A {', 3),
                 ('erDiagram\nA ||--|{ B : contains', 2),
                 ('%%{init: {}}%%\nflowchart LR\nA --> B', 1),
                 ('sequenceDiagram\nalt yes\nA->>B: hi', 2),
                 ('flowchart LR\nsubgraph one\nA\nend\nB\nA --> B', 5),
                 ('flowchart LR\nsubgraph one\nA\nB\nend\nA --> B\nB --> A', 3)]
        for text, line in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(mm.ImportError, 'MERMAID-NAO-SUPORTADO: linha ' + str(line) + ':'):
                    mm.parse(text, cli.base('en'))

    def test_sql_columns_constraints_and_metadata(self):
        _, m = data.sql('CREATE TABLE users (id uuid PRIMARY KEY); CREATE TABLE orders (id uuid PRIMARY KEY, user_id uuid NOT NULL, created timestamptz DEFAULT now(), FOREIGN KEY (user_id) REFERENCES users(id));', cli.base('en'))
        self.assertEqual(m['tabelas']['public.orders']['colunas'][1], ['user_id', 'uuid', 'FK', 'public.users', True])
        self.assertEqual(m['tabelas']['public.orders']['sql']['created']['default'], 'now()')
        _, existing = cli.parse(ROOT / 'exemplos/der-schema/ddl.sql', 'pt-BR')
        self.assertEqual(len(existing['tabelas']), 18)

    def test_sql_rejects_unsupported_and_unknown_refs(self):
        for text in ['DROP TABLE users;', 'CREATE TABLE users (id uuid CHECK (id IS NOT NULL));',
                     'CREATE TABLE users (id uuid REFERENCES missing);', 'CREATE TABLE users (id uuid, id uuid);',
                     'CREATE TABLE users (id uuid PRIMARY KEY REFERENCES other);']:
            with self.subTest(text=text), self.assertRaisesRegex(mm.ImportError, 'SQL-NAO-SUPORTADO'):
                data.sql(text, cli.base('en'))

    def test_csv_rejects_truncation(self):
        for text in ['name,name\na,b', 'name,owner\na', 'name,owner\n"a,b', 'name,owner\na,']:
            with self.subTest(text=text), self.assertRaisesRegex(mm.ImportError, 'CSV-NAO-SUPORTADO'):
                data.catalog(text)
        self.assertEqual(len(data.catalog((ROOT / 'exemplos/catalogo-cards/eventos.csv').read_text())), 11)

    def test_yaml_rejects_missing_values_unsafe_syntax_and_wrong_types(self):
        texts = ['titulo: !execute command', 'opcoes: text\n  - x', 'criterios: text\n  - nome: x',
                 '{"titulo":"a","titulo":"b"}',
                 '{"titulo":"a","opcoes":["a","b"],"criterios":[{"nome":"x","valores":["a"]}]}',
                 (ROOT / 'exemplos/tabela-comparacao/criterios.yaml').read_text()]
        for text in texts:
            with self.subTest(text=text), self.assertRaisesRegex(mm.ImportError, 'YAML-NAO-SUPORTADO'):
                data.yaml_comparison(text)

    def test_incompatible_type_and_unknown_extension(self):
        with self.assertRaisesRegex(mm.ImportError, 'TIPO-INCOMPATIVEL'):
            cli.parse(ROOT / 'exemplos/importar/en/catalog.csv', 'en', 'bpmn')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.txt'; path.write_text('flowchart LR')
            with self.assertRaisesRegex(mm.ImportError, 'FORMATO-NAO-SUPORTADO'): cli.parse(path, 'en')

    def test_html_escapes_input(self):
        output = cli.native_html('catalogo', [['name', 'owner'], ['<script>', 'a&b']], 'en', None)
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertIn('/*ESTILO*/', output)

    def test_gate_routes_and_failures_propagate(self):
        file = ROOT / 'exemplos/importar/en/sequence.mmd'
        with tempfile.TemporaryDirectory() as temp, patch.object(cli, 'run') as run:
            report = cli.generate(file, Path(temp), 'en')
            self.assertEqual(run.call_count, 2)
            self.assertEqual(Path(run.call_args_list[0][0][0][1]).name, 'gerar_sequencia.py')
            self.assertEqual(Path(run.call_args_list[1][0][0][1]).name, 'conceitual.py')
            self.assertEqual(report['gate'], 'passed')
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 7)):
            with self.assertRaises(SystemExit) as error: cli.run(['gate'])
            self.assertEqual(error.exception.code, 7)

    def test_source_input_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'process.bpmn'
            original = (ROOT / 'exemplos/importar/en/process.bpmn').read_bytes()
            path.write_bytes(original)
            with self.assertRaisesRegex(mm.ImportError, 'SAIDA-CONFLITA'):
                cli.generate(path, Path(temp), 'en', source_only=True)
            self.assertEqual(path.read_bytes(), original)

    def test_failed_conversion_invalidates_previous_report(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            file = out / 'bad.mmd'; file.write_text('gantt')
            report = out / 'bad.importacao.json'; report.write_text('{"gate":"passed"}')
            with self.assertRaises(mm.ImportError): cli.generate(file, out, 'en')
            self.assertEqual(json.loads(report.read_text())['gate'], 'pending')

    def test_invalid_utf8_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'bad.csv'; file.write_bytes(b'name,owner\na,\xff')
            with self.assertRaisesRegex(mm.ImportError, 'ENTRADA-INVALIDA'): cli.parse(file, 'en')

    def test_er_optional_key_and_unsupported_comments(self):
        text = 'erDiagram\nPARENT {\n uuid id PK\n}\nCHILD {\n uuid id PK\n uuid parent_id FK\n}\nPARENT |o..o{ CHILD : owns'
        _, model = mm.parse(text, cli.base('en'))
        self.assertFalse(model['tabelas']['public.CHILD']['colunas'][1][4])
        with self.assertRaisesRegex(mm.ImportError, 'MERMAID-NAO-SUPORTADO: linha 3:'):
            mm.parse('erDiagram\nPARENT {\n uuid id PK "comment"\n}', cli.base('en'))

    def test_yaml_inline_list_cannot_continue_as_block(self):
        with self.assertRaisesRegex(mm.ImportError, 'YAML-NAO-SUPORTADO: linha 3:'):
            data.yaml_comparison('titulo: Test\nopcoes: ["A", "B"]\n  - C\ncriterios:\n  - nome: Cost\n    valores: ["x", "y", "z"]')

    def test_der_without_relationships_passes_static_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            file = out / 'single.sql'; file.write_text('CREATE TABLE users (id uuid PRIMARY KEY);')
            cli.generate(file, out / 'result', 'en', source_only=True)
            source = out / 'result/_src/single/der-public.html'
            self.assertNotIn('<svg class="edges"', source.read_text())
            result = subprocess.run([sys.executable, str(ROOT / 'skills/ai-diagrams/scripts/poster_lint.py'), '--static', str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bpmn_layout_has_unique_cells(self):
        _, model = cli.parse(ROOT / 'exemplos/importar/en/flowchart.mmd', 'en')
        cli.position_bpmn(model)
        cells = [(n['lane'], n['col'], n['row']) for n in model['nodes']]
        self.assertEqual(len(cells), len(set(cells)))


if __name__ == '__main__': unittest.main()
