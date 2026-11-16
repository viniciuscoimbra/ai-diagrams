#!/usr/bin/env python3
"""Checks the translated example sources and that their contracts match the originals, without Chrome."""
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
ORIGINAIS = ROOT / 'examples'
sys.path.insert(0, str(ROOT / 'skills/ai-diagrams/scripts'))
import spec
KIND = {'swimlanes': 'swimlanes', 'sequence': 'sequence', 'state-machine': 'states', 'bpmn': 'bpmn',
        'er-schema': 'er_model', 'dependency-matrix': 'er_model'}
EXIBICAO = {
    'titulo_pagina', 'cabecalho', 'kicker', 'h1', 'sub', 'nome', 'texto', 'chip',
    'titulo', 'itens', 'f1', 'f2', 'rodape', 'rotulo', 'schemas', 'title',
    'subtitle', 'name', 'evento', 'guarda', 'acao', 'desc', 'passo', 'fases',
    'idioma', 'largura', 'lang', 'header', 'footer', 'page_title',
}


def contrato(value):
    if isinstance(value, dict):
        return {k: contrato(v) for k, v in value.items() if k not in EXIBICAO}
    if isinstance(value, list):
        return [contrato(v) for v in value]
    return value


class Visivel(HTMLParser):
    def __init__(self):
        super().__init__()
        self.oculto = 0
        self.textos = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.oculto += 1

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.oculto -= 1

    def handle_data(self, text):
        if not self.oculto:
            self.textos.append(text)


fontes = list(ORIGINAIS.glob('*/output/_src/*'))
assert len(fontes) == 17
for idioma in ('en', 'es'):
    for original in fontes:
        destino = BASE / idioma / original.relative_to(ORIGINAIS)
        assert destino.is_file(), destino
        conteudo = destino.read_text()
        assert '\u2014' not in conteudo, destino
        if destino.suffix == '.json':
            kind = KIND[original.relative_to(ORIGINAIS).parts[0]]
            atual = spec.ler(kind, json.loads(conteudo))
            assert atual.get('idioma') == idioma, destino
            assert contrato(atual) == contrato(spec.ler(kind, json.loads(original.read_text()))), destino
        if destino.suffix == '.mjs':
            def layout(path):
                code = 'import {pathToFileURL} from "node:url"; console.log(JSON.stringify((await import(pathToFileURL(process.argv[1]))).default));'
                return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', code, str(path)], text=True))
            assert contrato(spec.ler('er_layout', layout(destino))) == contrato(spec.ler('er_layout', layout(original))), destino
    htmls = list((BASE / idioma).glob('*/output/_src/*.html'))
    htmls += list((BASE / idioma / 'bpmn/output').glob('*.html'))
    assert len(htmls) == 11
    for html in htmls:
        conteudo = html.read_text()
        assert f'lang="{idioma}"' in conteudo, html
        assert f'name="lang" content="{idioma}"' in conteudo or f'name="idioma" content="{idioma}"' in conteudo, html
        parser = Visivel()
        parser.feed(conteudo)
        texto = ' '.join(parser.textos)
        assert not re.search(r'Exemplos de diagrama|\bPassos\b|\bNotificações\b|\bConciliação\b|C4 · nível|Faturas e recebimentos|Cada célula conta', texto), html

original = (ORIGINAIS / 'build-all.sh').read_text()
atual = (BASE / 'build-all.sh').read_text()
comandos = lambda s: [linha.strip() for linha in s.splitlines() if linha.strip().startswith(('python3 ', 'node '))]
assert comandos(atual) == [linha.replace('"$E/', '"$E/$lang/') for linha in comandos(original)]
subprocess.run(['bash', '-n', str(BASE / 'build-all.sh')], check=True)
print('examples-i18n: 34 sources, 22 HTML, identifiers and gates preserved; 0 failures')
