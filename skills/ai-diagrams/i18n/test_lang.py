#!/usr/bin/env python3
"""Language checks of the engine and the generators, without Chrome: python3 i18n/test_lang.py."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
import lang as idioma
import poster_lint
import build_states


class IdiomaTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {k: v for k, v in os.environ.items() if not k.startswith('AI_DIAGRAMS_')}, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_flags(self):
        self.assertEqual(idioma.tirar_flag(['a.json', '--idioma', 'es', 'b.html']), ('es', ['a.json', 'b.html']))
        self.assertEqual(idioma.tirar_flag(['--idioma=en', 'a.json']), ('en', ['a.json']))
        for args in (['--idioma'], ['--idioma', '--tema', 'papel']):
            with self.assertRaisesRegex(SystemExit, 'LANG-NOT-FOUND'):
                idioma.tirar_flag(args)

    def test_precedencia(self):
        self.assertEqual(idioma.idioma()['_codigo'], 'pt-BR')
        os.environ['AI_DIAGRAMS_IDIOMA'] = 'es'
        self.assertEqual(idioma.idioma()['_codigo'], 'es')
        self.assertEqual(idioma.idioma(fonte_json={'idioma': 'en'})['_codigo'], 'en')
        fonte = "<meta content='en' name='idioma' />"
        self.assertEqual(idioma.idioma(fonte_html=fonte)['_codigo'], 'en')
        self.assertEqual(idioma.idioma('pt-BR', fonte_json={'idioma': 'en'})['_codigo'], 'pt-BR')
        self.assertEqual(idioma.idioma('pt-BR', fonte_html=fonte)['_codigo'], 'pt-BR')

    def test_inexistente(self):
        for valor in ('fr', '', '../en', 'EN'):
            with self.assertRaisesRegex(SystemExit, 'LANG-NOT-FOUND'):
                idioma.idioma(valor)

    def test_incompleto_em_qualquer_catalogo(self):
        for nome in idioma.IDIOMAS:
            with tempfile.TemporaryDirectory() as pasta:
                for arquivo in idioma.PASTA.glob('*.json'):
                    shutil.copy(arquivo, pasta)
                caminho = Path(pasta) / (nome + '.json')
                catalogo = json.loads(caminho.read_text())
                del catalogo['sequencia.passos']
                caminho.write_text(json.dumps(catalogo))
                with patch.object(idioma, 'PASTA', Path(pasta)):
                    with self.assertRaisesRegex(SystemExit, 'LANG-INCOMPLETE: missing sequencia.passos'):
                        idioma.idioma(nome)

    def test_chave_solicitada_ausente(self):
        with self.assertRaisesRegex(SystemExit, 'LANG-INCOMPLETE: missing nova.chave'):
            idioma.idioma()['nova.chave']

    def test_meta_e_lang(self):
        fonte = '<html lang="pt-BR"><head></head><body>Texto autoral</body></html>'
        self.assertEqual(idioma.aplicar(fonte, idioma.idioma()), fonte)
        self.assertEqual(idioma.para_gerador(idioma.idioma()), '')
        for codigo in idioma.IDIOMAS:
            tr = idioma.idioma(codigo)
            saida = idioma.aplicar(fonte, tr)
            self.assertIn('lang="%s"' % codigo, saida)
            self.assertIn('<meta name="lang" content="%s">' % codigo, saida)
            self.assertIn('Texto autoral', saida)
        saida = idioma.aplicar("<html><head><meta content='en' name='idioma'></head></html>", idioma.idioma('es'))
        self.assertEqual(saida.count('name="lang"') + saida.count('name="idioma"'), 1)
        self.assertIn('<html lang="es">', saida)
        self.assertEqual(idioma.idioma(fonte_html=saida)['_codigo'], 'es')

    def test_passos_e_c4_independentes_do_texto(self):
        for titulo in ('Passos', 'Steps', 'Pasos'):
            fonte = '<div class="sec">%s</div><div class="badge">1</div><div class="passos"><div class="pb">1</div></div>' % titulo
            self.assertEqual(poster_lint.check_passos(fonte), [])
        for titulo in ('Legenda C4', 'C4 legend', 'Leyenda C4'):
            self.assertEqual(poster_lint.check_c4('<div class="c4leg">%s</div>' % titulo), [])

    def test_geradores(self):
        casos = [('swimlanes', '06-swimlanes', '06-account-opening', None),
                 ('sequence', '09-sequence', '09-pix-outbound', 'sequencia.kicker'),
                 ('states', '10-state-machine', '10-pix-states', 'estados.kicker')]
        with tempfile.TemporaryDirectory() as pasta:
            for gerador, modelo, nome, chave in casos:
                spec = json.loads((SKILL / 'templates' / modelo / '_src' / (nome + '.json')).read_text())
                spec['lang'] = 'es'
                if chave:
                    spec.pop('kicker', None)
                fonte = Path(pasta) / (nome + '.json')
                fonte.write_text(json.dumps(spec, ensure_ascii=False))
                for codigo in ('en', 'es'):
                    destino = Path(pasta) / (nome + '-' + codigo + '.html')
                    subprocess.run([sys.executable, str(SKILL / 'scripts' / ('build_' + gerador + '.py')),
                                    str(fonte), str(destino), '--lang', codigo], check=True, capture_output=True)
                    saida = destino.read_text()
                    self.assertIn('<html lang="%s">' % codigo, saida)
                    self.assertIn('<meta name="lang" content="%s">' % codigo, saida)
                    if chave:
                        self.assertIn(idioma.idioma(codigo)[chave], saida)
                    self.assertNotIn('>Notação<', saida)
                    self.assertNotIn('>Passos<', saida)

    def test_bpmn_sem_chrome(self):
        modelo = SKILL / 'templates/08-bpmn/_src/08-payment-dispute.json'
        with tempfile.TemporaryDirectory() as pasta:
            xml = []
            for codigo in idioma.IDIOMAS:
                destino = Path(pasta) / codigo
                resultado = subprocess.run([sys.executable, str(SKILL / 'bpmn/build_bpmn.py'), str(modelo),
                                            '--out', str(destino), '--lang', codigo, '--no-chrome'],
                                           check=True, capture_output=True, text=True)
                self.assertIn('import and PNG pending', resultado.stdout)
                html = (destino / (modelo.stem + '.html')).read_text()
                self.assertIn(idioma.idioma(codigo)['bpmn.kicker'], html)
                self.assertIn('<html lang="%s">' % codigo, html)
                self.assertFalse(list(destino.glob('*.png')))
                xml.append((destino / (modelo.stem + '.bpmn')).read_bytes())
            self.assertEqual(xml[0], xml[1])
            self.assertEqual(xml[0], xml[2])

    def test_largura_estados(self):
        spec = {'estados': [{'id': 'espera', 'nome': 'Pendiente de activación', 'largura': 280}],
                'inicial': 'espera', 'transicoes': [{'de': 'espera', 'para': 'espera', 'evento': 'retry'}]}
        graph = build_states.layout(spec, 'RIGHT')
        estado = next(c for c in graph['children'] if c['id'] == 'espera')
        self.assertEqual(estado['width'], 280)
        self.assertEqual(spec['estados'][0]['_w'], 280)
        for largura in (0, 34, '280', True, 280.5):
            spec['estados'][0]['largura'] = largura
            with self.assertRaisesRegex(SystemExit, 'WIDTH-INVALID'):
                build_states.layout(spec, 'RIGHT')


if __name__ == '__main__':
    unittest.main()
