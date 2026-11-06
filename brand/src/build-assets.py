#!/usr/bin/env python3
"""Build outlined SVG assets and portable multiply intersections; render PNGs with librsvg."""
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET
from html import escape
from itertools import combinations
import json
import math
import subprocess
from fontTools.ttLib import TTFont, woff2
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'brand/assets'
FONTS = ROOT.parent / 'local-ui/src/assets/fonts'
INK, SUPPORT, PAPER, ZONE = '#171717', '#525252', '#FFFFFF', '#F5F5F5'
COLORS = [('Ciano', '#24C8F5'), ('Coral', '#FF5B59'), ('Amarelo', '#FFE600'), ('Violeta', '#9868F5')]
CYAN, CORAL, YELLOW, VIOLET = [color for _, color in COLORS]
# Node already supplies Brotli when the local fontTools environment does not.
if not woff2.haveBrotli:
    woff2.haveBrotli = True
    woff2.brotli = SimpleNamespace(decompress=lambda value: subprocess.run(
        ['node', '-e', "process.stdout.write(require('node:zlib').brotliDecompressSync(require('node:fs').readFileSync(0)))"],
        input=value, stdout=subprocess.PIPE, check=True).stdout)
SANS = TTFont(FONTS / 'inter-latin.woff2')
MONO = TTFont(FONTS / 'jetbrains-mono-latin.woff2')


def rgb(color):
    return [int(color[i:i+2], 16) for i in (1, 3, 5)]


def multiply(*colors):
    # Multiply encoded sRGB channels, rounding half up once for the final intersection.
    channels = zip(*(rgb(color) for color in colors))
    return '#' + ''.join(f'{math.floor(math.prod(channel) / 255 ** (len(colors)-1) + .5):02X}' for channel in channels)


def contrast(a, b):
    def luminance(color):
        channels = [channel / 255 for channel in rgb(color)]
        channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        return sum(v * weight for v, weight in zip(channels, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + .05) / (dark + .05)


def swatch(color):
    foreground = max((INK, PAPER), key=lambda ink: contrast(color, ink))
    ratio = contrast(color, foreground)
    assert ratio >= 4.5, (color, foreground, ratio)
    return {'hex': color, 'foreground': foreground, 'contrast': round(ratio, 2)}


def number(value):
    return f'{value:.4f}'.rstrip('0').rstrip('.')


def text(value, x, y, size, color=INK, weight=400, mono=False, spacing=0, max_width=None):
    font = MONO if mono else SANS
    glyphs = font.getGlyphSet(location={'wght': weight} if 'fvar' in font else None)
    cmap, scale, paths, advance = font.getBestCmap(), size / font['head'].unitsPerEm, [], 0
    for char in value:
        assert ord(char) in cmap, f'Unsupported character: {char!r}'
        glyph = glyphs[cmap[ord(char)]]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        if pen.getCommands():
            paths.append(f'<path transform="translate({number(x + advance)} {number(y)}) scale({number(scale)} {number(-scale)})" d="{pen.getCommands()}"/>')
        advance += glyph.width * scale + spacing
    width = advance - spacing if value else 0
    if max_width is not None:
        assert width <= max_width, f'Text exceeds width: {value!r} ({width:.1f}>{max_width})'
    return f'<g fill="{color}" aria-label="{escape(value, quote=True)}">' + ''.join(paths) + '</g>'


def rect(x, y, width, height, fill, stroke=None, sw=1):
    assert width > 0 and height > 0
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>'


# The equilateral A is inscribed in the bowl, with its apex on x=32.
SHAPES = [
    ('M4 4H32V60H4Z', CYAN),
    ('M60 32A28 28 0 1 1 4 32A28 28 0 1 1 60 32Z', CORAL),
    (f'M32 4L{number(32 + 14 * math.sqrt(3))} 46L{number(32 - 14 * math.sqrt(3))} 46Z', YELLOW),
]


def symbol(mono=None, prefix='mark'):
    shapes = SHAPES
    if mono:
        return ''.join(f'<path d="{path}" fill="none" stroke="{mono}" stroke-width="3" stroke-linejoin="round"/>' for path, _ in shapes)
    defs = f'<clipPath id="{prefix}-1"><path d="{shapes[1][0]}"/></clipPath>'
    body = ''.join(f'<path d="{path}" fill="{color}"/>' for path, color in shapes[:2])
    # Only stem and bowl multiply; the opaque yellow A paints over both.
    body += f'<g clip-path="url(#{prefix}-1)"><path d="{shapes[0][0]}" fill="{multiply(CYAN, CORAL)}"/></g>'
    body += f'<path d="{shapes[2][0]}" fill="{YELLOW}"/>'
    return '<defs>' + defs + '</defs>' + body


def lockup(ink=INK, mono=False, prefix='mark'):
    return '<g transform="translate(0 4) scale(.875)">' + symbol(mono=ink if mono else None, prefix=prefix) + '</g>' + text('ai-diagrams', 70, 45, 40, ink, 600, spacing=-1.2, max_width=234)


def write(filename, width, height, title, body, description='', viewbox=None):
    viewbox = viewbox or f'0 0 {width} {height}'
    desc = f'<desc>{escape(description)}</desc>' if description else ''
    result = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{viewbox}" role="img"><title>{escape(title)}</title>{desc}{body}</svg>\n'
    parsed = ET.fromstring(result)
    assert parsed.attrib['viewBox'] == viewbox
    assert '<text' not in result and '<image' not in result and 'http' not in result.replace('http://www.w3.org/2000/svg', '')
    assert not any(token in result for token in ['mix-blend-mode', '<filter', 'opacity='])
    ids = [element.attrib['id'] for element in parsed.iter() if 'id' in element.attrib]
    assert len(ids) == len(set(ids)), f'Duplicate IDs in {filename}'
    (OUT / filename).write_text(result)


def badge(value, x, y, size=28, fill=INK, foreground=PAPER):
    return rect(x-size/2, y-size/2, size, size, fill) + text(str(value), x-size*.19, y+size*.23, size*.62, foreground, 600)


def arrow(points, value, badge_x, badge_y, color=SUPPORT):
    assert points[-1][1] == points[-2][1] and points[-1][0] > points[-2][0]
    assert any((x1 == x2 == badge_x and min(y1,y2) <= badge_y <= max(y1,y2)) or (y1 == y2 == badge_y and min(x1,x2) <= badge_x <= max(x1,x2)) for (x1,y1),(x2,y2) in zip(points,points[1:])), 'Badge must belong to connector'
    d = f'M{points[0][0]} {points[0][1]}'
    for (x1,y1),(x2,y2) in zip(points, points[1:]):
        assert x1 == x2 or y1 == y2, 'Orthogonal connectors only'
        d += f'H{x2}' if y1 == y2 else f'V{y2}'
    x,y=points[-1]
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/><path d="M{x-9} {y-5}L{x} {y}L{x-9} {y+5}Z" fill="{color}"/>' + badge(value,badge_x,badge_y)


OUT.mkdir(parents=True, exist_ok=True)
assert multiply('#FFFFFF', CYAN) == CYAN
assert multiply('#000000', CORAL) == '#000000'
assert multiply(CYAN, CORAL) == '#244756'
assert multiply(CYAN, YELLOW) == multiply(YELLOW, CYAN) == '#24B400'
assert abs(contrast('#000000', PAPER) - 21) < .0001
palette = {
    'colors': [{'name': name, **swatch(color)} for name, color in COLORS],
    'pairs': [{'names': [a[0], b[0]], **swatch(multiply(a[1], b[1]))} for a, b in combinations(COLORS, 2)],
}
assert len(palette['pairs']) == 6
(ROOT / 'brand/paleta.json').write_text(json.dumps(palette, ensure_ascii=False, indent=2) + '\n')
proposal = json.loads((ROOT / 'skills/ai-diagrams/temas/ai-diagrams.json').read_text())
proposal.update(nome='ai-diagrams vivo', fontes={'texto': 'Inter', 'mono': 'JetBrains Mono'})
proposal['cores'].update(tinta=INK, apoio=SUPPORT, cinza='#737373', zona=ZONE, papel=PAPER, acento=CYAN)
proposal['cores_derivadas']['acento_forte'] = '#086A84'
proposal['paleta_der'].update(der_forte=CORAL, der_dependente=CYAN, der_associativa=VIOLET, der_controle=YELLOW)
proposal['moldura'].update(cabecalho='{assunto}', mostrar_cliente=False)
(ROOT / 'brand/tema-vivo.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n')

write('proposta-encontro.svg', 64, 64, 'ai-diagrams · Encontro', symbol(), 'D com A: haste ciano, bojo circular coral e triângulo equilátero inscrito no círculo, apontando para o topo no diâmetro vertical. Amarelo vivo puro na camada superior; multiply somente entre haste e círculo.')
variants = [('solid', INK, False), ('solid-reverse', PAPER, False), ('mono-dark', INK, True), ('mono-light', PAPER, True)]
for name, ink, mono in variants:
    write(f'logo-{name}.svg', 304, 64, f'ai-diagrams · {name}', lockup(ink, mono), 'Símbolo Encontro: D com A, haste vertical, círculo e triângulo equilátero inscrito, com ponta no topo e eixo no diâmetro vertical. Nome em Inter Semibold convertido em curvas.')
    write(f'symbol-{name}.svg', 64, 64, f'ai-diagrams · símbolo {name}', symbol(mono=ink if mono else None), 'Encontro: D com A, haste vertical, bojo circular e triângulo equilátero inscrito, com ponta no topo e eixo no diâmetro vertical. Contornos em uma tinta nas versões monocromáticas; amarelo puro por cima e multiply só entre haste e círculo nas coloridas.')
write('favicon.svg', 64, 64, 'ai-diagrams · Encontro', symbol())
for size in (16, 32, 64):
    write(f'favicon-{size}.svg', size, size, f'ai-diagrams · favicon {size}', symbol(), viewbox='0 0 64 64')

social = rect(0, 0, 1280, 640, PAPER)
social += '<g transform="translate(64 48)">' + lockup(prefix='social-logo') + '</g>'
social += text('Documentos', 64, 256, 64, INK, 600, spacing=-2.2, max_width=630)
social += text('ganham vida.', 64, 330, 64, INK, 600, spacing=-2.2, max_width=630)
social += text('Diagramas bonitos para ideias', 67, 388, 24, SUPPORT, max_width=590)
social += text('que merecem ser vistas.', 67, 422, 24, SUPPORT, max_width=590)
social += text('ESCREVA. GERE. COMPARTILHE.', 67, 553, 14, SUPPORT, mono=True, spacing=.9, max_width=580)
social += rect(738, 58, 478, 524, ZONE)
social += text('UM DOCUMENTO, MUITAS FORMAS.', 766, 96, 12, SUPPORT, mono=True, spacing=.35, max_width=426)
social += '<g transform="translate(778 122) scale(6.25)">' + symbol(prefix='social-poster') + '</g>'
social += text('ai-diagrams', 766, 552, 14, SUPPORT, mono=True, max_width=250)
social += text('ENCONTRO', 1043, 552, 12, SUPPORT, mono=True, max_width=145)
write('social-preview.svg', 1280, 640, 'ai-diagrams · Documentos ganham vida.', social, 'Documentos ganham vida. Diagramas bonitos para ideias que merecem ser vistas. Pôster Encontro em ciano, coral e amarelo, sobre interface branca.')

poster = rect(0, 0, 1280, 856, PAPER)
poster += '<g transform="translate(56 26) scale(.58)">' + lockup(prefix='diagram-logo') + '</g>'
poster += text('ESTUDO DE COR / 01', 1030, 55, 13, SUPPORT, mono=True, max_width=194)
poster += rect(56, 79, 1168, 1, '#D4D4D4')
poster += text('UM DOCUMENTO, MUITAS FORMAS.', 56, 129, 15, SUPPORT, mono=True, spacing=.5, max_width=1168)
poster += text('Uma ideia fica clara quando ganha forma.', 56, 190, 43, INK, 600, spacing=-1, max_width=1168)
poster += text('Da descrição ao diagrama, com o fonte sempre por perto.', 56, 235, 23, SUPPORT, max_width=1168)
poster += rect(56, 283, 1168, 317, ZONE)
poster += text('DA IDEIA À IMAGEM', 82, 323, 13, SUPPORT, mono=True, spacing=.5, max_width=1000)
boxes = [(82, 385, 216, 112, 'Descrição', 'sua ideia em texto', CYAN), (391, 385, 216, 112, 'Fonte', 'arquivo editável', CORAL), (700, 385, 216, 112, 'Gate', 'confere geometria', YELLOW), (1009, 385, 189, 112, 'Diagrama', 'imagem final', VIOLET)]
for x, y, w, h, label, sub, color in boxes:
    fg = swatch(color)['foreground']
    poster += rect(x, y, w, h, color)
    poster += text(label, x+18, y+43, 25, fg, 600, max_width=w-36)
    poster += text(sub, x+18, y+78, 13, fg, mono=True, max_width=w-36)
for points, n, x in [([(298, 441), (391, 441)], 1, 344.5), ([(607, 441), (700, 441)], 2, 653.5), ([(916, 441), (1009, 441)], 3, 962.5)]:
    poster += arrow(points, n, x, 441)
poster += text('O gate confere caixas, textos e conectores antes da renderização.', 82, 558, 18, SUPPORT, max_width=1116)
poster += text('LEGENDA', 56, 648, 13, SUPPORT, mono=True, spacing=.5, max_width=1168)
for x, (label, color) in zip((56, 352, 648, 944), [('Ideia', CYAN), ('Construção', CORAL), ('Verificação', YELLOW), ('Resultado', VIOLET)]):
    poster += rect(x, 675, 18, 18, color)
    poster += text(label, x+29, 690, 18, INK, max_width=244)
poster += text('Estudo de identidade com a paleta viva. O tema atual do produto permanece igual.', 56, 744, 18, SUPPORT, max_width=1168)
poster += rect(56, 778, 1168, 1, '#D4D4D4')
poster += text('ai-diagrams · Fluxo de geração · 2026-11', 56, 817, 13, SUPPORT, mono=True, max_width=650)
poster += text('Proposta visual / sem execução do gate', 902, 817, 13, SUPPORT, max_width=322)
write('exemplo-diagrama.svg', 1280, 856, 'Uma ideia fica clara quando ganha forma.', poster, 'Estudo de diagrama com descrição, fonte, gate e diagrama. Quatro cores com legenda explícita, texto com contraste AA e conectores numerados. Proposta visual, sem execução do gate.')

expected = {f'{kind}-{name}.svg' for kind in ['logo', 'symbol'] for name, *_ in variants} | {f'favicon-{size}.svg' for size in (16, 32, 64)} | {'proposta-encontro.svg', 'favicon.svg', 'social-preview.svg', 'exemplo-diagrama.svg'}
assert expected == {p.name for p in OUT.glob('*.svg')}
for name, width, height in [('social-preview', 1280, 640)] + [(f'favicon-{size}', size, size) for size in (16, 32, 64)]:
    subprocess.run(['rsvg-convert', '-w', str(width), '-h', str(height), '-o', str(OUT / f'{name}.png'), str(OUT / f'{name}.svg')], check=True)
    header = (OUT / f'{name}.png').read_bytes()[:24]
    assert header[:8] == b'\x89PNG\r\n\x1a\n'
    assert int.from_bytes(header[16:20], 'big') == width and int.from_bytes(header[20:24], 'big') == height
print(f'{len(expected)} SVGs and 4 PNGs generated. Outlined Inter/JetBrains Mono, XML, multiply, contrast, text widths and dimensions checked.')
