"""Static brandkit checks. Browser interaction and visual approval remain separate."""
import base64
import hashlib
import json
import math
import re
import struct
from html.parser import HTMLParser
from io import BytesIO
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image

BRAND = Path(__file__).resolve().parents[1]
PLYNGO = BRAND.parent.parent / 'plyngo'
REFY = PLYNGO / 'node_modules/@refy/ui'
PROPOSALS = ['encontro', 'mosaico', 'orbita']
SIZES = (16, 32, 64)


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements, self.text = [], []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag in ('script', 'style'):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored -= 1

    def handle_data(self, value):
        if not self.ignored:
            self.text.append(value)


def rgb(color):
    assert re.fullmatch(r'#[0-9A-F]{6}', color), ('Invalid color', color)
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def multiply(colors):
    divisor = 255 ** (len(colors) - 1)
    return '#' + ''.join(f'{math.floor(math.prod(channel) / divisor + .5):02X}' for channel in zip(*(rgb(color) for color in colors)))


def contrast(background, foreground):
    def luminance(color):
        channels = [channel / 255 for channel in rgb(color)]
        return sum((channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4) * weight for channel, weight in zip(channels, (.2126, .7152, .0722)))
    low, high = sorted((luminance(background), luminance(foreground)))
    return (high + .05) / (low + .05)


def png_size(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', 'Invalid PNG header'
    return struct.unpack('>II', data[16:24])


def check_d_silhouette(data, size):
    alpha = Image.open(BytesIO(data)).convert('RGBA').getchannel('A')
    margin, center, radius = size / 16, size / 2, 7 * size / 16
    assert alpha.getbbox() == (margin, margin, size - margin, size - margin), (size, 'D bounds changed')
    for y in range(size):
        for x in range(size):
            distance = min(x + .5 - margin, radius - math.hypot(max(0, x + .5 - center), y + .5 - center))
            # Ignore only the antialiased edge; the stem and rounded bowl must stay solid.
            if distance >= .75:
                assert alpha.getpixel((x, y)) >= 254, (size, x, y, 'Missing D silhouette')
            elif distance <= -.75:
                assert alpha.getpixel((x, y)) <= 1, (size, x, y, 'Shape protrudes outside D')


assert contrast('#000000', '#FFFFFF') == 21
assert contrast('#FFFFFF', '#FFFFFF') == 1
assert multiply(['#24C8F5', '#FF5B59']) == '#244756'
assert hashlib.sha256((BRAND.parent / 'skills/ai-diagrams/temas/ai-diagrams.json').read_bytes()).hexdigest() == 'b8799b6fc85e789e8ae6bad5a339cf7a32bc3bc3ccf7f76294ff5c955676d9af', 'Installed diagram theme changed'

palette = json.loads((BRAND / 'paleta.json').read_text())
colors = {entry['name']: entry['hex'] for entry in palette['colors']}
assert len(colors) == len(palette['colors']) == 4
expected_pairs = {frozenset(names) for names in combinations(colors, 2)}
assert len(palette['pairs']) == 6
assert {frozenset(entry['names']) for entry in palette['pairs']} == expected_pairs
for entry in palette['pairs']:
    assert len(entry['names']) == 2
    assert entry['hex'] == multiply([colors[name] for name in entry['names']]), ('Incorrect multiply', entry)
for entry in palette['colors'] + palette['pairs']:
    assert entry['foreground'] in ('#171717', '#FFFFFF')
    ratio = contrast(entry['hex'], entry['foreground'])
    assert ratio >= 4.5 and abs(ratio - entry['contrast']) < .006, ('Incorrect text contrast', entry, ratio)
allowed = {f'#{channel:02X}{channel:02X}{channel:02X}' for channel in range(256)} | set(colors.values())
for count in range(2, len(colors) + 1):
    allowed.update(multiply(group) for group in combinations(colors.values(), count))
json.loads((BRAND / 'tema-vivo.json').read_text())

variants = ('solid', 'solid-reverse', 'mono-dark', 'mono-light')
expected_svg = {f'{kind}-{variant}.svg' for kind in ('logo', 'symbol') for variant in variants}
expected_svg |= {f'proposta-{proposal}.svg' for proposal in PROPOSALS} | {f'favicon-{size}.svg' for size in SIZES}
expected_svg |= {'favicon.svg', 'social-preview.svg', 'exemplo-diagrama.svg'}
expected_png = {f'favicon-{size}.png' for size in SIZES} | {'social-preview.png'}
files = {path.name: path for path in (BRAND / 'assets').iterdir() if path.suffix in ('.svg', '.png')}
assert set(files) == expected_svg | expected_png, ('Unexpected or missing assets', set(files) ^ (expected_svg | expected_png))
assets = {name: path.read_bytes() for name, path in files.items()}
for name in sorted(expected_svg):
    raw = assets[name].decode()
    svg = ET.fromstring(raw)
    tags = {element.tag.rsplit('}', 1)[-1] for element in svg.iter()}
    assert not tags.intersection({'text', 'image', 'script', 'style', 'filter', 'foreignObject', 'font', 'font-face'}), (name, 'Non-portable SVG element')
    assert not re.search(r'mix-blend-mode|feBlend|font-family|@font-face|opacity\s*=', raw), (name, 'SVG depends on blending or fonts')
    svg_ids = [element.attrib['id'] for element in svg.iter() if 'id' in element.attrib]
    assert len(svg_ids) == len(set(svg_ids)), (name, 'Duplicate SVG IDs')
    for element in svg.iter():
        for attribute, value in element.attrib.items():
            assert attribute != 'style' and not attribute.startswith('font-'), (name, 'SVG depends on CSS or fonts')
            if attribute in ('fill', 'stroke', 'stop-color'):
                assert value == 'none' or value in allowed, (name, 'Unapproved paint', value)
            if attribute.rsplit('}', 1)[-1] == 'href':
                assert value.startswith('#') and value[1:] in svg_ids, (name, 'External or missing SVG reference', value)
            for reference in re.findall(r'url\(([^)]+)\)', value):
                assert reference.startswith('#') and reference[1:] in svg_ids, (name, 'Unresolved SVG reference', reference)
    assert not re.search(r'https?://(?!www.w3.org)', raw), (name, 'External SVG resource')
    labels = ' '.join(svg.itertext()) + ' '.join(element.attrib.get('aria-label', '') for element in svg.iter())
    assert not re.search(r'—', labels, re.I), (name, 'Forbidden asset copy')
    painted = set(re.findall(r'#[0-9A-Fa-f]{6}\b', raw.upper()))
    assert painted <= allowed, (name, 'Unapproved asset colors', painted - allowed)
    if '-mono-' in name:
        assert len(painted) == 1, (name, 'Monochrome asset needs one ink')
    dimensions = (float(svg.attrib['width']), float(svg.attrib['height']))
    viewbox = tuple(map(float, svg.attrib['viewBox'].split()))
    assert len(viewbox) == 4 and viewbox[:2] == (0, 0)
    expected_size = (304, 64) if name.startswith('logo-') else (1280, 640) if name == 'social-preview.svg' else (1280, 856) if name == 'exemplo-diagrama.svg' else (64, 64)
    if match := re.fullmatch(r'favicon-(16|32|64)\.svg', name):
        expected_size = (int(match[1]),) * 2
    assert dimensions == expected_size, (name, 'Incorrect SVG dimensions', dimensions)
    assert viewbox[2:] == ((64, 64) if name.startswith('favicon-') else expected_size), (name, 'Incorrect SVG viewBox')
for name in expected_png:
    expected_size = (1280, 640) if name == 'social-preview.png' else (int(name.split('-')[1].split('.')[0]),) * 2
    assert png_size(assets[name]) == expected_size, (name, 'Incorrect PNG dimensions')
    if name.startswith('favicon-'):
        check_d_silhouette(assets[name], expected_size[0])

html = (BRAND / 'brandkit.html').read_text()
doc = Document()
doc.feed(html)
ids = [attrs['id'] for _, attrs in doc.elements if 'id' in attrs]
assert len(ids) == len(set(ids)), 'Duplicate HTML IDs'
assert [attrs['id'] for tag, attrs in doc.elements if tag == 'section'] == ['assinatura', 'cor-tipografia', 'tom-de-voz', 'aplicacoes']
assert sum(tag == 'h1' for tag, _ in doc.elements) == 1
assert sum(attrs.get('role') == 'radio' for _, attrs in doc.elements) == 2
scope = next(attrs for _, attrs in doc.elements if attrs.get('id') == 'app-scope')
assert scope.get('class') == 'brandkit' and scope.get('data-theme') == 'light'
proposals = [attrs for _, attrs in doc.elements if 'proposal' in attrs.get('class', '').split()]
assert [attrs.get('data-proposal') for attrs in proposals] == PROPOSALS
assert [attrs.get('data-proposal') for attrs in proposals if attrs.get('data-recommended') == 'true'] == ['encontro']
assert sum('color-chip' in attrs.get('class', '').split() for _, attrs in doc.elements) == 4
assert sum('multiply-chip' in attrs.get('class', '').split() for _, attrs in doc.elements) == 6
for tag, attrs in doc.elements:
    if tag in ('script', 'img', 'link', 'source', 'video', 'audio', 'iframe'):
        source = attrs.get('src') or attrs.get('href')
        assert not source or source.startswith('data:'), (tag, 'External resource')
        if tag == 'img':
            assert attrs.get('alt') and source, 'Missing image or alternative text'
            header, encoded = source.split(',', 1)
            decoded = base64.b64decode(encoded, validate=True)
            assert decoded in assets.values(), 'Embedded image differs from its asset'
            if header == 'data:image/svg+xml;base64':
                ET.fromstring(decoded)
            else:
                assert header == 'data:image/png;base64', ('Unexpected image MIME', header)
                assert png_size(decoded) == (int(attrs['width']), int(attrs['height'])), 'Incorrect rendered favicon dimensions'
    if tag == 'a' and attrs.get('href', '').startswith('#'):
        assert attrs['href'][1:] in ids, 'Broken section link'
visible = ' '.join(doc.text)
assert not re.search(r'—', visible, re.I), 'Forbidden visible copy'
assert 'ai-diagrams' in visible and not re.search(r'\bAI-Diagrams\b', visible), 'Brand name casing changed'
for name, data in assets.items():
    mime = 'image/svg+xml' if name.endswith('.svg') else 'image/png'
    assert f'data:{mime};base64,{base64.b64encode(data).decode()}' in html, (name, 'Missing or stale embedded download')

app = (BRAND / 'src/app.jsx').read_text()
assert "import { Button, Card, SectionHeader, Segmented } from '@refy/ui';" in app
assert 'ThemeProvider' not in app
for name in re.findall(r"(?:download\(|data\.assets\[)'([^']+)'", app):
    assert name in assets, ('Missing download or image', name)
assert all(f'proposta-{proposal}.svg' in assets for proposal in PROPOSALS)
assert all(f'favicon-{size}.png' in assets for size in SIZES)
assert json.loads((REFY / 'package.json').read_text())['version'] == '0.4.0'

layout = (BRAND / 'src/layout.css').read_text()
refy_css = '\n'.join((REFY / path).read_text() for path in ('src/tokens/tokens.css', 'src/styles/global.css', 'dist/style.css'))
refy_css = re.sub(r'^@import[^\n]*\n', '', refy_css, flags=re.M)
base = (PLYNGO / 'prototipo/ui/tokens.css').read_text().replace(':root', '.brandkit')
bridge = (PLYNGO / 'design-system/plyngo-tokens.css').read_text()
bridge = re.sub(r'@font-face\s*\{[^}]+\}', '', bridge).replace('[data-plyngo-theme]', '.brandkit[data-theme]').replace('[data-plyngo-theme=dark]', '.brandkit[data-theme=dark]')
for name, css in [('Refy styles', refy_css), ('Plyngo base', base), ('Plyngo semantic bridge', bridge), ('Brandkit layout', layout)]:
    assert css in html, (name, 'Missing, changed or stale CSS layer')
declared = set(re.findall(r'(--[\w-]+)\s*:', refy_css + base + bridge)) | {'--brand-papel', '--brand-tinta'}
assert set(re.findall(r'var\((--[\w-]+)', layout)) <= declared, 'Unknown layout token'
assert not re.search(r'#[\da-fA-F]{3,8}\b|(?:rgb|hsl|oklch)\(', layout), 'Parallel interface palette'
assert '.brandkit{--brand-papel:#fff;--brand-tinta:#171717}' in html
assert '@media (max-width: 760px)' in layout
style = re.search(r'<style>(.*?)</style>', html, re.S)[1]
assert len(re.findall(r'@font-face\s*\{', style)) == 3
assert 'font-family:PlyngoInter' in style and 'font-family:PlyngoMono' in style
assert not re.search(r'@import\s', style), 'External CSS import'
for source in re.findall(r'url\(([^)]+)\)', style):
    assert source.strip('"\'').startswith(('data:', '#')), ('External CSS resource', source)

print(f'PASS (static): 4 sections, 3 proposals / Encontro recommended, D silhouette at 16/32/64 px, 4 colors / 6 correct multiply pairs, AA contrast, {len(expected_svg)} SVGs + {len(expected_png)} PNGs, embedded assets, Refy 0.4.0 + exact Plyngo CSS, valid tokens, accessible image names, unchanged installed diagram theme.')
print('PENDING: browser interaction, computed UI colors, layout at 1440/390, v2 captures and visual review. Run capture.mjs outside the sandbox.')
