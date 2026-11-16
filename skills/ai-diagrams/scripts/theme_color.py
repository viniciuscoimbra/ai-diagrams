"""Color check on the source: color comes from the theme, never from a literal in the diagram.

Hexadecimal (#374151), rgb()/rgba() and hsl()/hsla() with a number fail with
COLOR-OUTSIDE-THEME. The source uses var(--token); the tokens are in the :root of
assets/style.css and assets/style-conceptual.css, with values in themes/ai-diagrams.json.
The SVG fill and stroke attributes do not accept var(): use style="stroke:var(--support)".
data: URIs, HTML entities (&#160;) and id references (url(#a), href="#a") are ignored.
Fonts follow the same rule: font-family with a literal family name fails with
FONT-OUTSIDE-THEME; use var(--font-text) or var(--font-mono), which the theme defines.
Used by poster_lint.py and conceptual.py, always on the source, before the base CSS goes in.
"""
import re

MENSAGEM = 'use a var(--token) from the theme (tokens in the :root of the base CSS)'
MENSAGEM_FONTE = 'use var(--font-text) or var(--font-mono); the family comes from the theme'
_DATA = re.compile(r'data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+')
_COR = re.compile(r'(?<![&\w#])(?<!url\()(?<!href=")#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})(?![\w-])'
                  r'|\b(?:rgba?|hsla?)\(\s*[\d.]')


def cores_fora(fonte):
    """Lista de (literal, linha) para cada cor literal no fonte."""
    txt = _DATA.sub('', fonte)
    return [(m.group(0), txt.count('\n', 0, m.start()) + 1) for m in _COR.finditer(txt)]


_FONTE = re.compile(r'font-family\s*:\s*(?!\s*(?:var\(|inherit\b|initial\b|unset\b))([^;}"]+)')


def fontes_fora(fonte):
    """Lista de (declaração, linha) para cada font-family com família literal no fonte."""
    return [(m.group(0).strip(), fonte.count('\n', 0, m.start()) + 1) for m in _FONTE.finditer(fonte)]
