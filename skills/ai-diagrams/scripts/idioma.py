#!/usr/bin/env python3
"""Rótulos do motor: --idioma > meta/campo idioma > AI_DIAGRAMS_IDIOMA > pt-BR."""
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / 'i18n'
PADRAO = 'pt-BR'
IDIOMAS = ('pt-BR', 'en', 'es')


class Rotulos(dict):
    def __missing__(self, chave):
        sys.exit('IDIOMA-INCOMPLETO: falta %s' % chave)


def tirar_flag(argv):
    out, valor, i = [], None, 0
    while i < len(argv):
        a = argv[i]
        if a == '--idioma':
            if i + 1 >= len(argv) or argv[i + 1].startswith('--'):
                sys.exit('IDIOMA-INEXISTENTE: --idioma sem valor; use pt-BR, en ou es')
            valor, i = argv[i + 1], i + 2
            continue
        if a.startswith('--idioma='):
            valor = a.split('=', 1)[1]
        else:
            out.append(a)
        i += 1
    return valor, out


class MetaIdioma(HTMLParser):
    valor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') == 'idioma':
            self.valor = attrs.get('content', '')


def carregar(codigo):
    if codigo not in IDIOMAS:
        sys.exit('IDIOMA-INEXISTENTE: %s; use pt-BR, en ou es' % codigo)
    catalogos = {}
    for nome in IDIOMAS:
        caminho = PASTA / (nome + '.json')
        if not caminho.is_file():
            sys.exit('IDIOMA-INEXISTENTE: %s' % caminho)
        try:
            catalogos[nome] = json.loads(caminho.read_text())
        except (OSError, ValueError) as e:
            sys.exit('IDIOMA-INCOMPLETO: %s não abre como json (%s)' % (caminho, e))
        if not isinstance(catalogos[nome], dict):
            sys.exit('IDIOMA-INCOMPLETO: %s precisa de um objeto de rótulos' % caminho)
    chaves = set().union(*(set(c) for c in catalogos.values()))
    for nome, catalogo in catalogos.items():
        for chave in sorted(chaves):
            if not isinstance(catalogo.get(chave), str) or not catalogo[chave]:
                sys.exit('IDIOMA-INCOMPLETO: falta %s (%s.json)' % (chave, nome))
    return Rotulos(catalogos[codigo])


def idioma(flag=None, fonte_html=None, fonte_json=None):
    meta = MetaIdioma()
    meta.feed(fonte_html or '')
    fonte = fonte_json.get('idioma') if fonte_json is not None else meta.valor
    if flag is not None:
        codigo, origem = flag, 'flag'
    elif fonte is not None:
        codigo, origem = fonte, 'fonte'
    elif os.environ.get('AI_DIAGRAMS_IDIOMA'):
        codigo, origem = os.environ['AI_DIAGRAMS_IDIOMA'], 'env'
    else:
        codigo, origem = PADRAO, 'padrao'
    rotulos = carregar(codigo)
    rotulos['_codigo'], rotulos['_origem'] = codigo, origem
    return rotulos


def para_gerador(rotulos):
    return '<meta name="idioma" content="%s">\n' % rotulos['_codigo'] if rotulos['_origem'] != 'padrao' else ''


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
    fonte, alterados = re.subn(r'<meta\b(?=[^>]*\bname\s*=\s*([\"\x27])idioma\1)[^>]*>',
                              lambda m: meta, fonte, flags=re.I)
    if not alterados:
        fonte = fonte.replace('</head>', meta + '\n</head>', 1)
    return fonte
