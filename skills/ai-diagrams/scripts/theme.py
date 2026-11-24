#!/usr/bin/env python3
"""Diagram theme: the only module that reads the theme JSON and writes its CSS.

Theme choice, the same in every command of the skill (build.py, conceptual.py, poster_lint.py,
build_swimlanes.py, build_sequence.py, build_states.py, bpmn/build_bpmn.py, er/er-build.mjs,
er/er-overview.mjs), in this order:
  1. flag --theme <name or path.json>;
  2. <meta name="theme" content="..."> in the HTML source (generators write it when the theme is not the default);
  3. environment variable AI_DIAGRAMS_THEME;
  4. default: ai-diagrams.
A name resolves to themes/<name>.json in this skill. A path (ends in .json or has a slash) accepts
a JSON in any folder; in the meta, the path is relative to the source folder.

The theme produces the :root with every color and font token and the Google Fonts link of its
families. The :root of the base CSS (assets/style.css, assets/style-conceptual.css) is only the
fallback of the default theme; the gate replaces that block with the chosen theme's. check_theme.py
checks the fallback.

Theme files use schema_version 2 (English keys). Version 1 files (Portuguese keys) are still read.

Fails (exit 1, before Chrome opens):
  THEME-NOT-FOUND   name without themes/<name>.json, or a path that does not exist.
  THEME-INVALID     JSON that does not parse, or a color outside #RRGGBB.
  THEME-INCOMPLETE  missing required key: "THEME-INCOMPLETE: missing colors.accent".

Direct use:
  python3 theme.py [--theme X] --css             prints the theme :root
  python3 theme.py [--theme X] --link            prints the Google Fonts link
  python3 theme.py [--theme X] --generator HTML  prints {link, meta} as JSON for a generator that writes HTML
  python3 theme.py [--theme X] --json            prints the theme as schema_version 2
"""
import json, os, re, sys
from urllib.parse import quote_plus

import compat

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(SK, 'themes')
PADRAO = 'ai-diagrams'
ENV, ENV_OLD = 'AI_DIAGRAMS_THEME', 'AI_DIAGRAMS_TEMA'
NOMES_ANTIGOS = {'papel': 'paper'}

OBRIGATORIAS = {
    'colors': ['ink', 'support', 'muted', 'zone', 'paper', 'accent', 'risk', 'risk_bg'],
    'derived': ['accent_strong', 'muted_light', 'c4_person_type', 'c4_person_desc', 'c4_external', 'c4_boundary'],
    'er_palette': ['er_border', 'er_legend', 'er_row_even', 'er_key', 'er_domain', 'er_external', 'er_copy',
                   'er_strong', 'er_dependent', 'er_associative', 'er_control', 'er_fact', 'er_versioned',
                   'er_projection', 'er_trail', 'er_domain_bg', 'er_config', 'er_reference',
                   'er_view', 'er_heat'],
    'fonts': ['text', 'mono'],
}
# Optional keys, added after 0.2.0: a theme without them keeps the 0.2.0 look.
# Each one falls back to another key of the theme.
OPCIONAIS = {
    'derived': [('c4_focus', 'colors', 'paper'), ('c4_focus_border', 'colors', 'ink'),
                ('c4_internal', 'colors', 'zone'), ('c4_internal_border', 'colors', 'muted')],
}
# schema_version 1 -> 2: group and key names
V1_GRUPOS = {'cores': 'colors', 'cores_derivadas': 'derived', 'paleta_der': 'er_palette', 'fontes': 'fonts'}
V1_CHAVES = {
    'tinta': 'ink', 'apoio': 'support', 'cinza': 'muted', 'zona': 'zone', 'papel': 'paper', 'acento': 'accent',
    'risco': 'risk', 'risco_fundo': 'risk_bg', 'acento_forte': 'accent_strong', 'cinza_claro': 'muted_light',
    'c4_pessoa_tipo': 'c4_person_type', 'c4_pessoa_desc': 'c4_person_desc', 'c4_externo': 'c4_external',
    'c4_limite': 'c4_boundary', 'der_borda': 'er_border', 'der_legenda': 'er_legend', 'der_linha_par': 'er_row_even',
    'der_chave': 'er_key', 'der_dominio': 'er_domain', 'der_fora': 'er_external', 'der_copia': 'er_copy',
    'der_forte': 'er_strong', 'der_dependente': 'er_dependent', 'der_associativa': 'er_associative',
    'der_controle': 'er_control', 'der_fato': 'er_fact', 'der_versionada': 'er_versioned',
    'der_projecao': 'er_projection', 'der_trilha': 'er_trail', 'der_dominio_fundo': 'er_domain_bg',
    'der_configuracao': 'er_config', 'der_referencia': 'er_reference', 'der_visao': 'er_view', 'der_calor': 'er_heat',
    'texto': 'text', 'mono': 'mono',
}
V1_MOLDURA = {'cabecalho': 'header', 'rodape': 'footer', 'rodape_direita': 'footer_right',
              'classificacao': 'classification', 'mostrar_cliente': 'show_client'}
# the same color as channels, for rgba(): color-mix rounds differently and changes pixels
CANAIS = ['support', 'paper', 'risk']
PESOS = 'wght@400;500;600;700'
_HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
_LINK = re.compile(r'<link\b[^>]*href="https://fonts\.googleapis\.com/css2\?[^"]*"[^>]*>')
_META = re.compile(r'<meta name="(?:theme|tema)" content="([^"]*)">')


def falha(msg):
    sys.exit(msg)


def tirar_flag(argv):
    """Remove --theme X (or --theme=X, or the deprecated --tema) from argv. Returns (value or None, rest)."""
    return compat.take_flag(argv, '--theme', '--tema',
                            'THEME-NOT-FOUND: --theme without a value; pass a name (themes/<name>.json) or a .json path')


def _e_caminho(v):
    return v.endswith('.json') or os.sep in v or '/' in v


def caminho(valor, base=None):
    """Name or path to the JSON file. base: folder for a relative path (default: cwd)."""
    if _e_caminho(valor):
        p = os.path.abspath(os.path.join(base, valor) if base and not os.path.isabs(valor) else valor)
        if not os.path.isfile(p):
            falha('THEME-NOT-FOUND: %s does not exist' % p)
        return p
    if valor in NOMES_ANTIGOS:
        compat.warn('theme "%s"' % valor, 'theme "%s"' % NOMES_ANTIGOS[valor])
        valor = NOMES_ANTIGOS[valor]
    p = os.path.join(PASTA, valor + '.json')
    if not os.path.isfile(p):
        disp = ', '.join(sorted(f[:-5] for f in os.listdir(PASTA) if f.endswith('.json')))
        falha('THEME-NOT-FOUND: no themes/%s.json; skill themes: %s; or pass a .json path' % (valor, disp))
    return p


def escolher(flag=None, fonte_html=None, fonte_dir=None):
    """Applies the precedence. Returns (JSON path, origin, value as given)."""
    if flag:
        return caminho(flag), 'flag', flag
    if fonte_html:
        m = _META.search(fonte_html)
        if m:
            return caminho(m.group(1), fonte_dir), 'meta', m.group(1)
    env = compat.env(ENV, ENV_OLD)
    if env:
        return caminho(env), 'env', env
    return caminho(PADRAO), 'padrao', PADRAO


def v2(t):
    """A schema_version 1 theme (Portuguese keys) as schema_version 2; a v2 theme comes back as is."""
    if 'cores' not in t and t.get('schema_version') != 1 and t.get('versao_schema') != 1:
        return t
    novo = {'schema_version': 2, 'name': t.get('nome', ''), 'company': t.get('empresa', ''), 'logo': t.get('logo')}
    for antigo, grupo in V1_GRUPOS.items():
        if isinstance(t.get(antigo), dict):
            novo[grupo] = {V1_CHAVES.get(k, k): v for k, v in t[antigo].items()}
    if isinstance(t.get('moldura'), dict):
        novo['frame'] = {V1_MOLDURA.get(k, k): v for k, v in t['moldura'].items()}
    return novo


def carregar(p):
    try:
        t = json.load(open(p))
    except (OSError, ValueError) as e:
        falha('THEME-INVALID: %s does not parse as JSON (%s)' % (p, e))
    if not isinstance(t, dict):
        falha('THEME-INVALID: %s must be a JSON object' % p)
    t = v2(t)
    for grupo, chaves in OBRIGATORIAS.items():
        g = t.get(grupo)
        if not isinstance(g, dict):
            falha('THEME-INCOMPLETE: missing %s (%s)' % (grupo, p))
        for k in chaves:
            v = g.get(k)
            if v is None or v == '':
                falha('THEME-INCOMPLETE: missing %s.%s (%s)' % (grupo, k, p))
            if grupo != 'fonts' and not _HEX.match(str(v)):
                falha('THEME-INVALID: %s.%s is "%s"; use #RRGGBB (%s)' % (grupo, k, v, p))
    for grupo, itens in OPCIONAIS.items():
        for k, g_fb, k_fb in itens:
            v = t[grupo].get(k)
            if v is None or v == '':
                t[grupo][k] = t[g_fb][k_fb]
            elif not _HEX.match(str(v)):
                falha('THEME-INVALID: %s.%s is "%s"; use #RRGGBB (%s)' % (grupo, k, v, p))
    t['_caminho'] = p
    return t


def tema(flag=None, fonte_html=None, fonte_dir=None):
    """Shortcut for the commands: chooses and loads."""
    p, origem, valor = escolher(flag, fonte_html, fonte_dir)
    t = carregar(p)
    t['_origem'], t['_valor'] = origem, valor
    return t


def _rgb(h):
    return ','.join(str(int(h[i:i + 2], 16)) for i in (1, 3, 5))


def pilha_texto(t):
    return "'%s',Arial,sans-serif" % t['fonts']['text']


def pilha_mono(t):
    return "'%s',monospace" % t['fonts']['mono']


def tokens(t):
    """Ordered list of (token name without --, value) that the :root declares."""
    out = []
    for grupo in ('colors', 'derived', 'er_palette'):
        for k in OBRIGATORIAS[grupo] + [o[0] for o in OPCIONAIS.get(grupo, [])]:
            if k == 'er_heat':
                continue
            out.append((k.replace('_', '-'), t[grupo][k].upper()))
    for k in CANAIS:
        out.append((k + '-rgb', _rgb(t['colors'][k])))
    out.append(('er-heat-rgb', _rgb(t['er_palette']['er_heat'])))
    out.append(('font-text', pilha_texto(t)))
    out.append(('font-mono', pilha_mono(t)))
    return out


# 0.1.x token names, still declared until 0.3.0 so older sources keep their colors
TOKENS_ANTIGOS = [('--%s' % a.replace('_', '-'), '--%s' % n.replace('_', '-'))
                  for a, n in V1_CHAVES.items() if a not in ('texto', 'mono', 'der_calor')] + \
                 [('--apoio-rgb', '--support-rgb'), ('--papel-rgb', '--paper-rgb'), ('--risco-rgb', '--risk-rgb'),
                  ('--der-calor-rgb', '--er-heat-rgb'), ('--fonte-texto', '--font-text'), ('--fonte-mono', '--font-mono')]


def css_root(t):
    linhas = ['--%s:%s;' % kv for kv in tokens(t)]
    return ':root{\n  /* theme %s: written by scripts/theme.py from %s */\n  %s\n}' % (
        t.get('name', ''), os.path.basename(t['_caminho']), '\n  '.join(linhas))


def css_aliases():
    return ':root{%s}' % ''.join('%s:var(%s);' % par for par in TOKENS_ANTIGOS)


def link_fontes(t):
    fam = '&'.join('family=%s:%s' % (quote_plus(t['fonts'][k]), PESOS) for k in ('text', 'mono'))
    return '<link href="https://fonts.googleapis.com/css2?%s&display=swap" rel="stylesheet">' % fam


def bloco_tokens(css):
    """(start, end) of the token :root in the base CSS (the first :root that declares --ink), or None."""
    for m in re.finditer(r':root\s*\{', css):
        fim = css.find('}', m.end())
        if fim > 0 and re.search(r'--(?:ink|tinta)\s*:', css[m.end():fim]):
            return m.start(), fim + 1
    return None


def css_com_tema(css_base, t, aliases=False):
    """The base CSS with its token :root replaced by the theme's (or the theme's in front, if the CSS has none).
    aliases: also declare the 0.1.x token names, for a source that still uses them."""
    root = css_root(t) + ('\n' + css_aliases() if aliases else '')
    b = bloco_tokens(css_base)
    if b is None:
        return root + '\n' + css_base
    return css_base[:b[0]] + root + css_base[b[1]:]


def usa_tokens_antigos(html):
    return any(re.search(re.escape(a) + r'(?![\w-])', html) for a, _ in TOKENS_ANTIGOS)


def com_link(html, t):
    """Replaces the source's Google Fonts link with the link of the theme families."""
    novo = link_fontes(t)
    if _LINK.search(html):
        return _LINK.sub(lambda m: novo, html, count=1)
    pre = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n')
    return html.replace('</head>', pre + novo + '\n</head>', 1) if '</head>' in html else html


MARCADOR, MARCADOR_ANTIGO = '/*STYLE*/', '/*ESTILO*/'


def tem_marcador(html):
    return MARCADOR in html or MARCADOR_ANTIGO in html


def aplicar(html, css_base, t):
    """Source with /*STYLE*/ -> HTML with the base CSS, the theme :root and the font link."""
    css = css_com_tema(css_base, t, usa_tokens_antigos(html))
    marcador = MARCADOR if MARCADOR in html else MARCADOR_ANTIGO
    return com_link(html.replace(marcador, css), t)


def para_gerador(t, saida_html):
    """Font link and theme meta for a generator to write in the HTML source.
    The meta only goes in when the theme was chosen (flag or env); with the default the source stays as it always was."""
    meta = ''
    if t['_origem'] in ('flag', 'env'):
        v = t['_valor']
        if _e_caminho(v):  # relative to the source when close to it (portable project); otherwise absolute
            rel = os.path.relpath(t['_caminho'], os.path.dirname(os.path.abspath(saida_html)))
            v = rel if rel.split(os.sep).count('..') <= 3 else t['_caminho']
        meta = '<meta name="theme" content="%s">' % v
    return {'link': link_fontes(t), 'meta': meta}


def publico(t):
    """The theme as a schema_version 2 file, without the private keys."""
    return {k: v for k, v in t.items() if not k.startswith('_')}


def main():
    flag, argv = tirar_flag(sys.argv[1:])
    t = tema(flag)
    gerador, argv = compat.take_flag(argv, '--generator', '--gerador')
    if '--css' in argv:
        print(css_root(t))
    elif '--link' in argv:
        print(link_fontes(t))
    elif gerador:
        print(json.dumps(para_gerador(t, gerador), ensure_ascii=False))
    elif '--json' in argv:
        print(json.dumps(publico(t), ensure_ascii=False, indent=2))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
