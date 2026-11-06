"""Check de cor no fonte: a cor vem do tema, nunca de literal no diagrama.

Hexadecimal (#374151), rgb()/rgba() e hsl()/hsla() com número reprovam com
COR-FORA-DO-TEMA. O fonte usa var(--token); os tokens estão no :root de
assets/estilo.css e assets/estilo-conceitual.css, com valores em temas/ai-diagrams.json.
Atributo SVG fill e stroke não aceita var(): use style="stroke:var(--apoio)".
Ficam de fora data: URIs, entidades HTML (&#160;) e referências a id (url(#a), href="#a").
Fonte segue a mesma regra: font-family com nome de família literal reprova com
FONTE-FORA-DO-TEMA; use var(--fonte-texto) ou var(--fonte-mono), que o tema define.
Usado por poster_lint.py e conceitual.py, sempre sobre o fonte, antes de o CSS base entrar.
"""
import re

MENSAGEM = 'use var(--token) do tema (tokens no :root do CSS base)'
MENSAGEM_FONTE = 'use var(--fonte-texto) ou var(--fonte-mono); a família vem do tema'
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
