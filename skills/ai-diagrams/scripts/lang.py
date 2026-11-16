#!/usr/bin/env python3
"""Engine labels: --lang > meta/field lang > AI_DIAGRAMS_LANG > pt-BR.
The 0.1.x names (--idioma, meta and field idioma, AI_DIAGRAMS_IDIOMA) still work until 0.3.0."""
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import compat

PASTA = Path(__file__).resolve().parents[1] / 'i18n'
PADRAO = 'pt-BR'
IDIOMAS = ('pt-BR', 'en', 'es')


class Rotulos(dict):
    def __missing__(self, chave):
        sys.exit('LANG-INCOMPLETE: missing %s' % chave)


def tirar_flag(argv):
    return compat.take_flag(argv, '--lang', '--idioma', 'LANG-NOT-FOUND: --lang without a value; use pt-BR, en or es')


class MetaIdioma(HTMLParser):
    valor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') in ('lang', 'idioma'):
            self.valor = attrs.get('content', '')


def carregar(codigo):
    if codigo not in IDIOMAS:
        sys.exit('LANG-NOT-FOUND: %s; use pt-BR, en or es' % codigo)
    catalogos = {}
    for nome in IDIOMAS:
        caminho = PASTA / (nome + '.json')
        if not caminho.is_file():
            sys.exit('LANG-NOT-FOUND: %s' % caminho)
        try:
            catalogos[nome] = json.loads(caminho.read_text())
        except (OSError, ValueError) as e:
            sys.exit('LANG-INCOMPLETE: %s does not parse as JSON (%s)' % (caminho, e))
        if not isinstance(catalogos[nome], dict):
            sys.exit('LANG-INCOMPLETE: %s must be an object of labels' % caminho)
    chaves = set().union(*(set(c) for c in catalogos.values()))
    for nome, catalogo in catalogos.items():
        for chave in sorted(chaves):
            if not isinstance(catalogo.get(chave), str) or not catalogo[chave]:
                sys.exit('LANG-INCOMPLETE: missing %s (%s.json)' % (chave, nome))
    return Rotulos(catalogos[codigo])


def idioma(flag=None, fonte_html=None, fonte_json=None):
    meta = MetaIdioma()
    meta.feed(fonte_html or '')
    fonte = (fonte_json.get('lang', fonte_json.get('idioma')) if fonte_json is not None else meta.valor)
    env = compat.env('AI_DIAGRAMS_LANG', 'AI_DIAGRAMS_IDIOMA') if flag is None and fonte is None else None
    if flag is not None:
        codigo, origem = flag, 'flag'
    elif fonte is not None:
        codigo, origem = fonte, 'fonte'
    elif env:
        codigo, origem = env, 'env'
    else:
        codigo, origem = PADRAO, 'padrao'
    rotulos = carregar(codigo)
    rotulos['_codigo'], rotulos['_origem'] = codigo, origem
    return rotulos


def para_gerador(rotulos):
    return '<meta name="lang" content="%s">\n' % rotulos['_codigo'] if rotulos['_origem'] != 'padrao' else ''


def aplicar(fonte, rotulos):
    if rotulos['_origem'] == 'padrao':
        return fonte
    codigo = rotulos['_codigo']
    def raiz(m):
        attrs, alterados = re.subn(r'(?<![\w-])lang\s*=\s*([\"\x27])[^\"\x27]*\1',
                                  'lang="%s"' % codigo, m[2], count=1, flags=re.I)
        return m[1] + ('' if alterados else ' lang="%s"' % codigo) + attrs
    fonte = re.sub(r'(<html\b)([^>]*>)', raiz, fonte, count=1, flags=re.I)
    meta = para_gerador(rotulos).rstrip()
    fonte, alterados = re.subn(r'<meta\b(?=[^>]*\bname\s*=\s*([\"\x27])(?:lang|idioma)\1)[^>]*>',
                              lambda m: meta, fonte, flags=re.I)
    if not alterados:
        fonte = fonte.replace('</head>', meta + '\n</head>', 1)
    return fonte
