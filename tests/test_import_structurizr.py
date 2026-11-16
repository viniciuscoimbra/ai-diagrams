"""Structurizr DSL import and the C4 model: same views from the DSL and from the JSON, rejections, view derivation."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/ai-diagrams/scripts'))
import build_c4 as c4
import import_structurizr as dsl
import lang
import spec

BASE = {'lang': 'pt-BR', 'title': 'Diagrama importado', 'footer': 'Importação'}
TR = lang.idioma('pt-BR')


def views(model):
    m = spec.ler('c4', model)
    M = c4.Modelo(m)
    out = {}
    for v in m['views']:
        d = c4.derivar(M, dict(v), TR)
        out[v['key']] = (sorted(d['caixas']), [(r['from'], r['to'], r['description'], r['technology']) for r in d['arestas']], d['moldura'])
    return out


class StructurizrTests(unittest.TestCase):
    def test_billing_dsl_draws_the_same_views_as_the_json(self):
        json_model = json.loads((ROOT / 'examples/c4/output/_src/billing-c4.json').read_text())
        dsl_model = dsl.modelo_c4((ROOT / 'examples/c4/billing.dsl').read_text(), BASE)
        self.assertEqual(views(json_model), views(dsl_model))
        shapes = {e['id']: e.get('shape') for e in dsl_model['elements'] if e.get('shape')}
        self.assertEqual(shapes, {'portal': 'web', 'backoffice': 'web', 'banco': 'database'})
        external = {e['id'] for e in dsl_model['elements'] if e.get('external')}
        self.assertEqual(external, {'cip', 'liquidante', 'webhook'})

    def test_autolayout_direction_becomes_orientation(self):
        text = '''workspace {
    model {
        u = person "User" "uses it"
        s = softwareSystem "Shop" "sells"
        u -> s "Buys" "browser"
    }
    views {
        systemContext s "lr" {
            include *
            autoLayout lr
        }
        systemContext s "tb" {
            include *
            autoLayout tb 300 300
        }
        systemContext s "bare" {
            include *
            autoLayout
        }
    }
}'''
        vs = {v['key']: v for v in dsl.modelo_c4(text, BASE)['views']}
        self.assertEqual(vs['lr'].get('orientation'), 'horizontal')
        self.assertEqual(vs['tb'].get('orientation'), 'vertical')
        self.assertNotIn('orientation', vs['bare'])

    def test_orientation_is_checked(self):
        self.assertEqual(c4.orientacao({}, {'key': 'a'}), 'auto')
        self.assertEqual(c4.orientacao({'orientation': 'vertical'}, {'key': 'a'}), 'vertical')
        self.assertEqual(c4.orientacao({'orientation': 'vertical'}, {'key': 'a', 'orientation': 'horizontal'}), 'horizontal')
        with self.assertRaisesRegex(SystemExit, 'C4-VIEW'):
            c4.orientacao({}, {'key': 'a', 'orientation': 'LR'})

    def test_hierarchical_identifiers_this_and_filtered_views(self):
        text = '''workspace {
    !identifiers hierarchical
    model {
        u = person "User" "uses it"
        s = softwareSystem "Shop" "sells" {
            api = container "API" "orders" "Go" "Core"
            web = container "Web" "pages" "React" {
                -> s.api "Calls" "HTTPS"
            }
        }
        u -> s.web "Buys" "browser"
    }
    views {
        container s "all" { include * }
        filtered "all" exclude "Core" "no-core"
    }
}'''
        model = dsl.modelo_c4(text, BASE)
        self.assertIn({'from': 'web', 'to': 'api', 'description': 'Calls', 'technology': 'HTTPS'}, model['relationships'])
        v = views(model)
        self.assertEqual(v['all'][0], ['api', 'u', 'web'])
        self.assertEqual(v['no-core'][0], ['u', 'web'])

    def test_unsupported_syntax_names_the_line(self):
        for text, code in [('workspace {\n  !include other.dsl\n}', 'DSL-UNSUPPORTED: !include'),
                           ('workspace {\n model {\n  a = person "A" "a"\n  a -> b "x" "y"\n }\n}', 'DSL-UNKNOWN'),
                           ('workspace {\n model {\n  a = person "A" "a"\n }\n views {\n  custom "k" { }\n }\n}', 'DSL-UNSUPPORTED: custom view'),
                           ('workspace {\n model {\n  a = person "A" "a"\n }\n views {\n  systemLandscape { include ->a-> }\n }\n}', 'DSL-UNSUPPORTED: include')]:
            with self.subTest(code=code):
                with self.assertRaises(dsl.DSLError) as e:
                    dsl.modelo_c4(text, BASE)
                self.assertIn(code, str(e.exception))
                self.assertIn('at line', str(e.exception))

    def test_model_rules(self):
        base = {'lang': 'pt-BR', 'header': ['a', 'b'], 'footer': ['a', 'b'], 'views': [{'type': 'landscape', 'key': 'l'}]}
        cases = [([{'id': 's', 'type': 'system', 'name': 'S', 'description': 'd'},
                   {'id': 'c', 'type': 'container', 'parent': 's', 'name': 'C', 'description': 'd'}], [], 'C4-NO-TECHNOLOGY'),
                 ([{'id': 'c', 'type': 'container', 'name': 'C', 'description': 'd', 'technology': 't'}], [], 'C4-PARENT'),
                 ([{'id': 'p', 'type': 'person', 'name': 'P', 'description': 'd'}], [{'from': 'p', 'to': 'x', 'description': 'd', 'technology': 't'}], 'C4-UNKNOWN'),
                 ([{'id': 'p', 'type': 'person', 'name': 'P', 'description': 'd'}, {'id': 'p', 'type': 'person', 'name': 'Q', 'description': 'd'}], [], 'C4-DUPLICATE')]
        for elements, rels, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(SystemExit) as e:
                    c4.Modelo(spec.ler('c4', dict(base, elements=elements, relationships=rels)))
                self.assertIn(code, str(e.exception))

    def test_implied_relationship_and_explicit_one_wins(self):
        v = views(json.loads((ROOT / 'examples/c4/output/_src/billing-c4.json').read_text()))
        context = {(a, b): d for a, b, d, _ in v['context'][1]}
        self.assertEqual(context[('cliente', 'cobranca')], 'Emite e acompanha boletos')
        self.assertEqual(context[('cobranca', 'cip')], 'Registra o boleto antes da linha digitável')
        containers = {(a, b) for a, b, _, _ in v['containers'][1]}
        self.assertIn(('cliente', 'api'), containers)
        self.assertNotIn(('cliente', 'cobranca'), containers)
        self.assertEqual(v['api'][2], 'api')


if __name__ == '__main__':
    unittest.main()
