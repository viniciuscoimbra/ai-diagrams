#!/usr/bin/env python3
"""Checks the theme against the pipeline: the theme JSON is the source of truth for color and font.

Usage: python3 check_theme.py [theme.json]   (default: themes/ai-diagrams.json in this skill)

The token :root of assets/style.css and assets/style-conceptual.css is only the fallback of the
default theme: the gate replaces that block with the chosen theme's (scripts/theme.py). This
checks that the fallback is exactly what theme.py writes for the JSON, and that nothing outside
it hardcodes a color or a font.

Checks (exit 1 on any failure):
  TOKEN-MISMATCH       token in the base CSS :root with a value different from the JSON, missing
                       or extra.
  COLOR-OUTSIDE-THEME  literal color in the base CSS outside the token :root, in the generators
                       (er/*.mjs, scripts/build_*.py) or in bpmn/build_bpmn.py.
  FONT-OUTSIDE-THEME   font-family with a literal family name in the same files; fonts only
                       through var(--font-text) and var(--font-mono).
  THEME-INCOMPLETE     a JSON in themes/ without a required key (or THEME-INVALID).
  THEME-INVALID        a JSON in themes/ that is not schema_version 2 (the engine writes only v2).
"""
import json, os, re, sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SK, 'scripts'))
import theme_color
import theme as tema


def tokens_bloco(css):
    b = tema.bloco_tokens(css)
    if b is None:
        return None, css
    corpo = re.sub(r'/\*.*?\*/', '', css[b[0]:b[1]], flags=re.S)
    achado = {k: v.strip() for k, v in re.findall(r'--([\w-]+):([^;]+);', corpo)}
    return achado, css[:b[0]] + css[b[1]:]


def normal(v):
    return v.replace(' ', '').upper()


def main():
    falhas = []
    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SK, 'themes', 'ai-diagrams.json')
    try:
        esperado = dict(tema.tokens(tema.carregar(caminho)))
    except SystemExit as e:
        print('  ' + str(e))
        sys.exit(1)

    for arq in ('style.css', 'style-conceptual.css'):
        css = open(os.path.join(SK, 'assets', arq)).read()
        achado, resto = tokens_bloco(css)
        if achado is None:
            falhas.append('TOKEN-MISMATCH %s: no token :root (--ink)' % arq)
            achado = {}
        for k, v in esperado.items():
            if k not in achado:
                falhas.append('TOKEN-MISMATCH %s: missing --%s' % (arq, k))
            elif normal(achado[k]) != normal(v):
                falhas.append('TOKEN-MISMATCH %s: --%s is %s, the theme says %s' % (arq, k, achado[k], v))
        for k in sorted(set(achado) - set(esperado)):
            falhas.append('TOKEN-MISMATCH %s: --%s does not come from the theme (the gate replaces the block and it disappears)' % (arq, k))
        falhas += ['COLOR-OUTSIDE-THEME %s: %s on line %d' % (arq, c, l) for c, l in theme_color.cores_fora(resto)]
        falhas += ['FONT-OUTSIDE-THEME %s: %s on line %d' % (arq, c, l) for c, l in theme_color.fontes_fora(resto)]

    geradores = [os.path.join(SK, 'er', f) for f in sorted(os.listdir(os.path.join(SK, 'er'))) if f.endswith('.mjs')]
    geradores += [os.path.join(SK, 'scripts', f) for f in sorted(os.listdir(os.path.join(SK, 'scripts')))
                  if f.startswith('build_') and f.endswith('.py')]
    geradores.append(os.path.join(SK, 'bpmn', 'build_bpmn.py'))
    for g in geradores:
        txt = open(g).read()
        falhas += ['COLOR-OUTSIDE-THEME %s: %s on line %d' % (os.path.basename(g), c, l) for c, l in theme_color.cores_fora(txt)]
        falhas += ['FONT-OUTSIDE-THEME %s: %s on line %d' % (os.path.basename(g), c, l) for c, l in theme_color.fontes_fora(txt)]

    pasta = os.path.join(SK, 'themes')
    for f in sorted(os.listdir(pasta)):
        if f.endswith('.json'):
            p = os.path.join(pasta, f)
            try:
                tema.carregar(p)
            except SystemExit as e:
                falhas.append(str(e))
                continue
            versao = json.load(open(p)).get('schema_version')
            if versao != 2:
                falhas.append('THEME-INVALID: themes/%s has schema_version %s; the engine writes only 2' % (f, versao))

    for f in falhas:
        print('  ' + f)
    print('theme: %d tokens checked, %d failures' % (len(esperado), len(falhas)))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
