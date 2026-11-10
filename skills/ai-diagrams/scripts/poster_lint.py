#!/usr/bin/env python3
"""Geometric lint for posters.
Usage: poster_lint.py [--fix] [--static] file.html [...]
Checks:
1. Arrow head and arrow start touch a box or a frame border (tol 6px);
   between 6 and 60px along the segment, --fix snaps them (DETACHED,
   ADJUSTABLE, FIXED; -START for the arrow start).
2. Orthogonal routing: no arrow segment crosses the interior of a box that
   is not its endpoint (CROSSES); parallel segments of different arrows
   cannot be collinear (COLLINEAR-V / COLLINEAR-H); route through corridors.
   An arrow running inside the box it connects fails with INSIDE-BOX.
3. Numbered steps are required: the canvas needs badges 1..N and the .passos
   section needs matching items (NO-BADGES / NO-STEPS / STEPS-MISMATCH).
4. A badge is born with its arrow: the center of each badge sits on the
   arrow line (tol 6px) and may slide along it; a badge beside the line or
   loose fails (BADGE-DETACHED). --fix moves it onto the arrow (FIXED-BADGE).
5. Overlap measured in Chrome (same conditions as the screenshot): badges,
   node labels (.nl/.ns), icons, .elabel, .flabel and chips cannot overlap
   (OVERLAP); an arrow does not run over text, including the text inside
   .bchip (ARROW-OVER-TEXT); an arrow does not run along a frame border
   (ARROW-ON-EDGE); a frame border does not cut node text (TEXT-OVER-EDGE);
   an .elabel sits within 30px of some arrow (LABEL-DETACHED); an arrow tip
   does not sit in the middle of a box (ARROWHEAD-INSIDE).
   Skipped with --static (or when Chrome is not available, with NO-CHROME).
   A render that returns no measurement fails with MEASURE-FAILED.
6. A document without drawn arrows (no <svg class="edges">, like the
   dependency matrix) does not narrate a flow: checks 3 and 4 do not apply
   to it. The others still do.
7. Overflow measured in Chrome: nothing goes past the right edge of the
   page, where the capture cuts (OVERFLOW).
8. Technical register: title, subtitle, kicker and bands without marketing
   vocabulary (MARKETING-COPY; list in technical_text.py).
9. C4: every .bchip.c4 element has a type (.bn) and a name (.bt), and the
   page has the .c4leg legend (C4-NO-TYPE, C4-NO-LEGEND). A page whose arrows
   carry .rel labels (the C4 generator, scripts/build_c4.py) needs no badges:
   every arrow has exactly one .rel with what it does (.rd) and its [technology]
   (.rt) (C4-REL-MISSING, C4-REL-INCOMPLETE); in Chrome, the label sits on or
   beside its own arrow (C4-REL-DETACHED) and no other arrow crosses it
   (ARROW-OVER-TEXT); it does not touch a box, a border label or another label
   (OVERLAP).
10. Color and font only from the theme: a literal hex or rgb() in the source
   fails (COLOR-OUTSIDE-THEME); so does a font-family with a literal family
   name (FONT-OUTSIDE-THEME; rules in theme_color.py).
Theme: --theme <name or path.json>, <meta name="theme"> in the source,
AI_DIAGRAMS_THEME or ai-diagrams, in that order (scripts/theme.py). The Chrome
measurement uses the theme fonts.
Language: --lang pt-BR|en|es, <meta name="lang">, AI_DIAGRAMS_LANG or pt-BR.
The structural checks use classes and do not depend on the label text.
Output: exit code 1 on any problem. build.py runs this lint before the PNG
and fails the poster when there is a problem."""
import re, sys, os

def boxes(t):
    solid, frames = [], []
    for m in re.finditer(r'<div class="(node|chip[^"]*|oss|svc|bchip[^"]*)"[^>]*style="([^"]*)"', t):
        cls, st = m.group(1), m.group(2)
        def px(k, d=None):
            mm = re.search(k + r':(-?[\d.]+)px', st)
            return float(mm.group(1)) if mm else d
        l, tp = px('left'), px('top')
        if l is None or tp is None: continue
        w = px('width', 110 if cls == 'node' else 150)
        h = px('height', 95 if cls == 'node' else 70)
        cls = cls.split()[0]
        if cls == 'node':
            solid.append((l + (w - 44) / 2, tp, l + (w - 44) / 2 + 44, tp + 44))
        else:
            solid.append((l, tp, l + w, tp + h))
    for m in re.finditer(r'<div class="frame [^"]*"[^>]*style="([^"]*)"', t):
        st = m.group(1)
        v = {k: float(re.search(k + r':(-?[\d.]+)px', st).group(1)) for k in ('left', 'top', 'width', 'height')}
        frames.append((v['left'], v['top'], v['left'] + v['width'], v['top'] + v['height']))
    return solid, frames

def near_solid(x, y, solid, tol=6):
    for (a, b, c, d) in solid:
        if a - tol <= x <= c + tol and b - tol <= y <= d + tol: return True
    return False

def near_frame_border(x, y, frames, tol=6):
    for (a, b, c, d) in frames:
        if (abs(x - a) <= tol or abs(x - c) <= tol) and b - tol <= y <= d + tol: return True
        if (abs(y - b) <= tol or abs(y - d) <= tol) and a - tol <= x <= c + tol: return True
    return False

def march(x, y, dx, dy, solid, frames, maxd=60):
    for t in range(1, maxd + 1):
        nx, ny = x + dx * t, y + dy * t
        for (a, b, c, d) in solid:
            if a <= nx <= c and b <= ny <= d:
                return nx + dx * 4, ny + dy * 4
        if near_frame_border(nx, ny, frames, 2):
            return nx, ny
    return None

def endpoint_of_path(d):
    toks = re.findall(r'([MHVL])\s*(-?[\d.]+)(?:[ ,](-?[\d.]+))?', d)
    x = y = px = py = None
    for c, a, b in toks:
        px, py = x, y
        if c == 'M' or c == 'L': x, y = float(a), float(b)
        elif c == 'H': x = float(a)
        elif c == 'V': y = float(a)
    if px is None: return None
    dx = 0 if x == px else (1 if x > px else -1)
    dy = 0 if y == py else (1 if y > py else -1)
    return x, y, dx, dy, toks

def fix_path_d(d, nx, ny):
    toks = list(re.finditer(r'([MHVL])\s*(-?[\d.]+)(?:[ ,](-?[\d.]+))?', d))
    last = toks[-1]
    c = last.group(1)
    if c == 'H': rep = 'H%g' % nx
    elif c == 'V': rep = 'V%g' % ny
    else: rep = '%s%g,%g' % (c, nx, ny)
    return d[:last.start()] + rep + d[last.end():]

def start_of_path(d):
    toks = re.findall(r'([MHVL])\s*(-?[\d.]+)(?:[ ,](-?[\d.]+))?', d)
    if not toks or toks[0][0] != 'M' or len(toks) < 2: return None
    x, y = float(toks[0][1]), float(toks[0][2])
    c, a, b = toks[1]
    nx, ny = x, y
    if c == 'M' or c == 'L': nx, ny = float(a), float(b)
    elif c == 'H': nx = float(a)
    elif c == 'V': ny = float(a)
    dx = 0 if nx == x else (1 if nx > x else -1)
    dy = 0 if ny == y else (1 if ny > y else -1)
    return x, y, -dx, -dy

def fix_path_start(d, nx, ny):
    m = re.match(r'M\s*(-?[\d.]+)[ ,](-?[\d.]+)', d)
    return 'M%g,%g' % (nx, ny) + d[m.end():]


def _near_box_pt(x, y, box, tol=10):
    a, b, c, d = box
    return a - tol <= x <= c + tol and b - tol <= y <= d + tol

def segments(t):
    segs = []
    for i, m in enumerate(re.finditer(r'<path d="([^"]+)"[^>]*marker-end[^>]*/>', t)):
        toks = re.findall(r'([MHVL])\s*(-?[\d.]+)(?:[ ,](-?[\d.]+))?', m.group(1))
        x = y = None
        for c, a, b in toks:
            if c == 'M':
                x, y = float(a), float(b); continue
            if c == 'L': nx, ny = float(a), float(b)
            elif c == 'H': nx, ny = float(a), y
            else: nx, ny = x, float(a)
            segs.append((i, x, y, nx, ny))
            x, y = nx, ny
    for i, m in enumerate(re.finditer(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"[^>]*marker-end[^>]*/>', t)):
        x1, y1, x2, y2 = map(float, m.groups())
        segs.append((1000 + i, x1, y1, x2, y2))
    return segs

def check_routing(t, solid):
    issues, segs = [], segments(t)
    ultimo = {s[0]: k for k, s in enumerate(segs)}  # índice do último segmento de cada seta
    for k, (i, x1, y1, x2, y2) in enumerate(segs):
        for box in solid:
            a, b, c, d = box
            if x1 == x2 and a + 2 < x1 < c - 2:
                lo, hi = max(min(y1, y2), b + 2), min(max(y1, y2), d - 2)
                if hi - lo > 4 and not (_near_box_pt(x1, y1, box) or _near_box_pt(x2, y2, box)):
                    issues.append(('CROSSES', x1, (lo + hi) / 2, None))
                elif hi - lo > 10 and ultimo[i] == k and _near_box_pt(x2, y2, box):
                    issues.append(('INSIDE-BOX %gpx: the arrow runs inside the box it connects (end the tip at the border)' % (hi - lo), x1, (lo + hi) / 2, None))
            elif y1 == y2 and b + 2 < y1 < d - 2:
                lo, hi = max(min(x1, x2), a + 2), min(max(x1, x2), c - 2)
                if hi - lo > 4 and not (_near_box_pt(x1, y1, box) or _near_box_pt(x2, y2, box)):
                    issues.append(('CROSSES', (lo + hi) / 2, y1, None))
                elif hi - lo > 10 and ultimo[i] == k and _near_box_pt(x2, y2, box):
                    issues.append(('INSIDE-BOX %gpx: the arrow runs inside the box it connects (end the tip at the border)' % (hi - lo), (lo + hi) / 2, y1, None))
    def ov(a1, a2, b1, b2):
        return min(max(a1, a2), max(b1, b2)) - max(min(a1, a2), min(b1, b2))
    seen = set()
    vs = [s for s in segs if s[1] == s[3]]
    hs = [s for s in segs if s[2] == s[4]]
    for lst, oi, r1, r2, kind in ((vs, 1, 2, 4, 'V'), (hs, 2, 1, 3, 'H')):
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                s1, s2 = lst[i], lst[j]
                if s1[0] == s2[0]: continue
                if abs(s1[oi] - s2[oi]) <= 8 and ov(s1[r1], s1[r2], s2[r1], s2[r2]) > 20:
                    key = (kind, round(s1[oi] / 4))
                    if key not in seen:
                        seen.add(key)
                        issues.append(('COLLINEAR-' + kind, s1[oi], ov(s1[r1], s1[r2], s2[r1], s2[r2]), None))
    return issues

def check_passos(t):
    issues = []
    badges = re.findall(r'<div class="badge"[^>]*>\s*(\d+)', t)
    pitems = re.findall(r'class="pb">\s*(\d+)', t)
    if not badges: issues.append(('NO-BADGES', 0, 0, None))
    if not pitems: issues.append(('NO-STEPS', 0, 0, None))
    if badges and pitems and set(badges) != set(pitems):
        issues.append(('STEPS-MISMATCH', len(set(badges)), len(set(pitems)), None))
    return issues


def check_badges(t):
    issues, segs = [], segments(t)
    for m in re.finditer(r'<div class="badge" style="left:(-?[\d.]+)px;top:(-?[\d.]+)px"[^>]*>\s*(\d+)', t):
        cx, cy, n = float(m.group(1)) + 10, float(m.group(2)) + 10, m.group(3)
        ok = False
        for (_, x1, y1, x2, y2) in segs:
            if x1 == x2 and abs(cx - x1) <= 6 and min(y1, y2) - 6 <= cy <= max(y1, y2) + 6: ok = True; break
            if y1 == y2 and abs(cy - y1) <= 6 and min(x1, x2) - 6 <= cx <= max(x1, x2) + 6: ok = True; break
        if not ok:
            issues.append(('BADGE-DETACHED ' + n, cx, cy, None))
    return issues

def fix_badges(t):
    """--fix: leva o centro de cada badge solto para o ponto mais próximo da seta mais
    próxima, a pelo menos 14px das pontas do segmento. Devolve (texto, correções)."""
    segs, fixos = segments(t), []
    def troca(m):
        cx, cy, n = float(m.group(1)) + 10, float(m.group(2)) + 10, m.group(3)
        melhor = None
        for (_, x1, y1, x2, y2) in segs:
            if x1 == x2 and abs(y2 - y1) >= 30:
                lo, hi = min(y1, y2) + 14, max(y1, y2) - 14
                px, py = x1, min(max(cy, lo), hi)
            elif y1 == y2 and abs(x2 - x1) >= 30:
                lo, hi = min(x1, x2) + 14, max(x1, x2) - 14
                px, py = min(max(cx, lo), hi), y1
            else:
                continue
            d = abs(px - cx) + abs(py - cy)
            if melhor is None or d < melhor[0]:
                melhor = (d, px, py)
        if melhor is None or melhor[0] <= 6:
            return m.group(0)
        fixos.append((n, cx, cy, melhor[1], melhor[2]))
        return m.group(0).replace('left:%spx;top:%spx' % (m.group(1), m.group(2)),
                                  'left:%gpx;top:%gpx' % (melhor[1] - 10, melhor[2] - 10))
    novo = re.sub(r'<div class="badge" style="left:(-?[\d.]+)px;top:(-?[\d.]+)px"[^>]*>\s*(\d+)', troca, t)
    return novo, fixos


def caixa_mais_proxima(x, y, solid, frames):
    """Ponto da borda de caixa (ou de frame) mais próximo de (x, y), para sugerir a correção."""
    melhor = None
    for (a, b, c, d) in solid + frames:
        px, py = min(max(x, a), c), min(max(y, b), d)
        if a < x < c and b < y < d:
            continue
        dist = abs(px - x) + abs(py - y)
        if melhor is None or dist < melhor[0]:
            melhor = (dist, px, py)
    return melhor


def vertices(d):
    """Pontos do caminho, em ordem."""
    pts, x, y = [], None, None
    for c, a, b in re.findall(r'([MHVL])\s*(-?[\d.]+)(?:[ ,](-?[\d.]+))?', d):
        if c in ('M', 'L'): x, y = float(a), float(b)
        elif c == 'H': x = float(a)
        else: y = float(a)
        pts.append((x, y))
    return pts


def recuar(x, y, dx, dy, vizinho, solid, frames):
    """Ponta que passou da caixa: volta pela própria linha até a borda, se a caixa está a até
    60px para trás e o ponto novo fica a mais de 20px do vértice vizinho."""
    s = march(x, y, -dx, -dy, solid, frames)
    if s and abs(s[0] - vizinho[0]) + abs(s[1] - vizinho[1]) > 20:
        return s
    return None


def check_texto(t):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import technical_text as tt
    return [('MARKETING-COPY "%s" in "%s"' % (termo, trecho), 0, 0, None)
            for termo, trecho in tt.marketing(tt.textos_de_abertura(t))]


def check_cores(t):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import theme_color
    return [('COLOR-OUTSIDE-THEME %s on line %d: %s' % (lit, linha, theme_color.MENSAGEM), 0, 0, None)
            for lit, linha in theme_color.cores_fora(t)] + \
           [('FONT-OUTSIDE-THEME %s on line %d: %s' % (dec, linha, theme_color.MENSAGEM_FONTE), 0, 0, None)
            for dec, linha in theme_color.fontes_fora(t)]


def check_rel(t):
    """C4 gerado: cada seta tem um rótulo .rel, com o que faz e a tecnologia."""
    setas = len(re.findall(r'<path d="[^"]+"[^>]*marker-end[^>]*/>', t))
    rels = re.findall(r'<div class="rel" data-edge="(\d+)"[^>]*>(.*?)</div>', t)
    issues = []
    if sorted(int(k) for k, _ in rels) != list(range(setas)):
        issues.append(('C4-REL-MISSING: %d arrows and %d .rel labels; every arrow needs one label, data-edge 0..%d'
                       % (setas, len(rels), setas - 1), 0, 0, None))
    for k, corpo in rels:
        if 'class="rd"' not in corpo or not re.search(r'class="rt">\[[^\]]+\]', corpo):
            issues.append(('C4-REL-INCOMPLETE: label of arrow %s needs what it does (.rd) and [technology] (.rt)' % k, 0, 0, None))
    return issues


def check_c4(t):
    """C4: todo elemento diz o tipo (.bn) e o nome (.bt), e a página traz a legenda (.c4leg)."""
    els = re.findall(r'<div class="bchip c4[^"]*"[^>]*>(.*?)\n\s*</div>', t, re.S)
    if not els:
        return []
    issues = [('C4-NO-TYPE: element "%s" needs .bn (type and technology) and .bt (name)'
               % re.sub(r'<[^>]+>|\s+', ' ', e).strip()[:40], 0, 0, None)
              for e in els if 'class="bn"' not in e or 'class="bt"' not in e]
    if 'class="c4leg"' not in t:
        issues.append(('C4-NO-LEGEND: add the C4 legend section with .c4leg', 0, 0, None))
    return issues


def lint(fn, fix=False):
    t = open(fn).read()
    solid, frames = boxes(t)
    out, issues = t, []
    for m in re.finditer(r'<path d="([^"]+)"[^>]*marker-end[^>]*/>', t):
        r = endpoint_of_path(m.group(1))
        if not r: continue
        x, y, dx, dy, _ = r
        if near_solid(x, y, solid) or near_frame_border(x, y, frames): continue
        s = march(x, y, dx, dy, solid, frames) or recuar(x, y, dx, dy, vertices(m.group(1))[-2], solid, frames)
        if s and fix:
            out = out.replace(m.group(1), fix_path_d(m.group(1), *s), 1)
            issues.append(('FIXED', x, y, s))
        else:
            issues.append(('DETACHED', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('ADJUSTABLE', x, y, s))
    for m in re.finditer(r'<path d="([^"]+)"[^>]*marker-end[^>]*/>', t):
        r = start_of_path(m.group(1))
        if not r: continue
        x, y, dx, dy = r
        if near_solid(x, y, solid) or near_frame_border(x, y, frames): continue
        s = march(x, y, dx, dy, solid, frames) or recuar(x, y, dx, dy, vertices(m.group(1))[1], solid, frames)
        if s and fix:
            out = out.replace(m.group(1), fix_path_start(m.group(1), *s), 1)
            issues.append(('FIXED-START', x, y, s))
        else:
            issues.append(('DETACHED-START', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('ADJUSTABLE-START', x, y, s))
    for m in re.finditer(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"[^>]*marker-end[^>]*/>', t):
        x1, y1, x, y = map(float, m.groups())
        dx = 0 if x == x1 else (1 if x > x1 else -1)
        dy = 0 if y == y1 else (1 if y > y1 else -1)
        if near_solid(x, y, solid) or near_frame_border(x, y, frames): continue
        s = march(x, y, dx, dy, solid, frames)
        if s and fix:
            o2 = m.group(0)
            n2 = o2.replace('x2="%s"' % m.group(3), 'x2="%g"' % s[0]).replace('y2="%s"' % m.group(4), 'y2="%g"' % s[1])
            out = out.replace(o2, n2, 1)
            issues.append(('FIXED', x, y, s))
        else:
            issues.append(('DETACHED', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('ADJUSTABLE', x, y, s))
        sx, sy = x1, y1
        if not (near_solid(sx, sy, solid) or near_frame_border(sx, sy, frames)):
            s2 = march(sx, sy, -dx, -dy, solid, frames)
            if s2 and fix:
                o2 = m.group(0) if m.group(0) in out else None
                if o2:
                    n2 = o2.replace('x1="%s"' % m.group(1), 'x1="%g"' % s2[0], 1).replace('y1="%s"' % m.group(2), 'y1="%g"' % s2[1], 1)
                    out = out.replace(o2, n2, 1)
                    issues.append(('FIXED-START', sx, sy, s2))
            elif not (s2 and fix):
                issues.append(('DETACHED-START' if not s2 else 'ADJUSTABLE-START', sx, sy, s2))
    issues += check_routing(t, solid)
    if '<svg class="edges"' in t and 'class="rel"' in t:
        issues += check_rel(t)
    elif '<svg class="edges"' in t:
        issues += check_passos(t)
        if fix:
            out, fixos = fix_badges(out)
            issues += [('FIXED-BADGE ' + n, x, y, (nx, ny)) for n, x, y, nx, ny in fixos]
        issues += check_badges(out)
    issues += check_texto(t)
    issues += check_c4(t)
    issues += check_cores(t)
    if fix and out != t: open(fn, 'w').write(out)
    return issues


# ---------------------------------------------------------------- medicao real
import os, json, subprocess, tempfile, shutil, math

MEASURE_JS = """
<script>
window.addEventListener('load', function () {
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () {
    var cv = document.querySelector('.canvas') || document.body;
    var o = cv.getBoundingClientRect();
    var out = {boxes: [], svg: [0, 0]};
    var svg = document.querySelector('svg.edges');
    if (svg) { var sr = svg.getBoundingClientRect(); out.svg = [sr.left - o.left, sr.top - o.top]; }
    function push(kind, idx, el) {
      var r = el.getBoundingClientRect();
      if (r.width < 1 && r.height < 1) return;
      out.boxes.push([kind, idx, r.left - o.left, r.top - o.top, r.right - o.left,
                      r.bottom - o.top, (el.textContent || '').trim().slice(0, 40)]);
    }
    document.querySelectorAll('.node').forEach(function (n, i) {
      var im = n.querySelector('img'); if (im) push('icon', i, im);
      var nl = n.querySelector('.nl'); if (nl) push('nl', i, nl);
      var ns = n.querySelector('.ns'); if (ns) push('ns', i, ns);
    });
    document.querySelectorAll('.badge').forEach(function (b) { push('badge', -1, b); });
    document.querySelectorAll('.elabel').forEach(function (b) { push('elabel', -1, b); });
    document.querySelectorAll('.frame > .flabel').forEach(function (b) { push('flabel', -1, b); });
    document.querySelectorAll('.frame').forEach(function (b) { push('frame', -1, b); });
    document.querySelectorAll('.chip,.bchip,.oss,.svc,.c4head').forEach(function (b) { push('chip', -1, b); });
    document.querySelectorAll('.rel').forEach(function (b) { push('rel', parseInt(b.getAttribute('data-edge'), 10), b); });
    document.querySelectorAll('.bchip .bn,.bchip .bt,.bchip .bs').forEach(function (b) { push('btx', -1, b); });
    // transbordo pela direita: a captura corta tudo que passa da largura da página
    var bw = document.body.getBoundingClientRect().width;
    out.largura = [bw, document.documentElement.scrollWidth];
    var pg = document.querySelector('.page') || document.body;
    out.altura = Math.ceil(pg.getBoundingClientRect().bottom);
    out.fora = [];
    document.querySelectorAll('body *').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > bw + 1 && out.fora.length < 6)
        out.fora.push([(el.className && el.className.baseVal === undefined ? el.className : el.tagName) + '',
                       Math.round(r.right), (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 30)]);
    });
    document.body.setAttribute('data-lint', JSON.stringify(out));
  });
});
</script>"""


def find_css(src_dir):
    """Mesma busca do build.py: _style.css ou style.css do projeto (ou os nomes antigos
    _style.css/style.css), senao o da skill."""
    for name in ('_style.css', 'style.css', '_style.css', 'style.css'):
        p = os.path.join(src_dir, name)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'style.css')


def find_chrome():
    env = os.environ.get('POSTER_CHROME')
    if env and os.path.exists(env):
        return env
    for c in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              '/Applications/Chromium.app/Contents/MacOS/Chromium'):
        if os.path.exists(c):
            return c
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        p = shutil.which(name)
        if p:
            return p
    return None


def measure(fn, chrome, tm=None):
    """Renderiza no Chrome, com o tema, e devolve as caixas reais (coordenadas do canvas)."""
    t = open(fn).read()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import theme as tema
    if tema.tem_marcador(t):
        d = os.path.dirname(os.path.abspath(fn))
        t = tema.aplicar(t, open(find_css(d)).read(), tm or tema.tema(None, t, d))
    t = t.replace('</body>', MEASURE_JS + '</body>')
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(t)
        tmp = f.name
    try:
        try:
            r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                                '--virtual-time-budget=4000', '--dump-dom', 'file://' + tmp],
                               capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            sys.exit('Chrome did not respond within 120s while measuring %s. Check the network (fonts come from '
                     'Google Fonts), close other stuck headless Chrome processes and check POSTER_CHROME (%s). '
                     'To run only the checks that do not need Chrome, use --static.' % (fn, chrome))
        m = re.search(r'data-lint="([^"]+)"', r.stdout.decode())
        if not m:
            return None
        return json.loads(m.group(1).replace('&quot;', '"').replace('&amp;', '&'))
    finally:
        os.unlink(tmp)


def _inter(b1, b2, pad=2):
    """Area de intersecao com folga: exige penetracao > pad nos dois eixos."""
    w = min(b1[2], b2[2]) - max(b1[0], b2[0])
    h = min(b1[3], b2[3]) - max(b1[1], b2[1])
    return w > pad and h > pad


# quem nao pode encostar em quem (ambas as direcoes)
_PARES = {('badge', 'icon'), ('badge', 'nl'), ('badge', 'ns'), ('badge', 'elabel'),
          ('badge', 'flabel'), ('badge', 'chip'), ('badge', 'badge'),
          ('elabel', 'icon'), ('elabel', 'nl'), ('elabel', 'ns'), ('elabel', 'elabel'),
          ('elabel', 'flabel'), ('elabel', 'chip'),
          ('nl', 'nl'), ('nl', 'ns'), ('ns', 'ns'), ('nl', 'icon'), ('ns', 'icon'),
          ('nl', 'chip'), ('ns', 'chip'),
          ('rel', 'rel'), ('rel', 'chip'), ('rel', 'flabel'), ('rel', 'badge'), ('rel', 'elabel'), ('rel', 'icon'),
          ('rel', 'nl'), ('rel', 'ns')}


def check_medido(data, t):
    issues = []
    bw, sw = data.get('largura', [0, 0])
    if sw > bw + 1 or data.get('fora'):
        alvo = '; '.join('%s "%s" up to %dpx' % (c[:20], tx, r) for c, r, tx in data.get('fora', [])[:3])
        issues.append(('OVERFLOW content goes past the page width (%dpx, document is %dpx): %s'
                       % (bw, sw, alvo or 'see the PNG'), 0, 0, None))
    bx = data['boxes']
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            k1, n1, *r1, tx1 = bx[i]
            k2, n2, *r2, tx2 = bx[j]
            if k1 in ('nl', 'ns', 'icon') and k2 in ('nl', 'ns', 'icon') and n1 == n2:
                continue  # partes do mesmo no
            if (k1, k2) in _PARES or (k2, k1) in _PARES:
                if _inter(r1, r2):
                    issues.append(('OVERLAP %s×%s "%s"' % (k1, k2, (tx1 or tx2)[:24]),
                                   max(r1[0], r2[0]), max(r1[1], r2[1]), None))
    # borda de frame (AWS Cloud, conta, zona) cruzando texto de nó ou rótulo
    for k, n, a, b, c, d, tx in [x for x in bx if x[0] in ('nl', 'ns', 'elabel')]:
        for _, _, fa, fb, fc, fd, _ in [x for x in bx if x[0] == 'frame']:
            corta_v = any(a + 2 < xb < c - 2 for xb in (fa, fc)) and min(d, fd) - max(b, fb) > 2
            corta_h = any(b + 2 < yb < d - 2 for yb in (fb, fd)) and min(c, fc) - max(a, fa) > 2
            if corta_v or corta_h:
                issues.append(('TEXT-OVER-EDGE %s "%s": a frame border cuts the text; move the node inside or outside the frame' % (k, tx[:24]), a, b, None))
                break
    ox, oy = data.get('svg', [0, 0])
    textos = [b for b in bx if b[0] in ('nl', 'ns', 'elabel', 'flabel', 'btx', 'rel')]
    for (seta, x1, y1, x2, y2) in segments(t):
        x1, y1, x2, y2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
        for k, n, a, b, c, d, tx in textos:
            box = (a, b, c, d)
            if k == 'rel' and n == seta:
                continue  # o rótulo da relação fica sobre a própria seta
            if _near_box_pt(x1, y1, box) or _near_box_pt(x2, y2, box):
                continue
            if x1 == x2 and a + 2 < x1 < c - 2:
                lo, hi = max(min(y1, y2), b + 2), min(max(y1, y2), d - 2)
                if hi - lo > 3:
                    issues.append(('ARROW-OVER-TEXT %s "%s": the vertical at x=%g crosses the text (x %g to %g); route the arrow through x<%g or x>%g, or leave from the side of the icon'
                                   % (k, tx[:24], x1 - ox, a - ox, c - ox, a - ox - 8, c - ox + 8), x1, (lo + hi) / 2, None))
            elif y1 == y2 and b + 2 < y1 < d - 2:
                lo, hi = max(min(x1, x2), a + 2), min(max(x1, x2), c - 2)
                if hi - lo > 3:
                    issues.append(('ARROW-OVER-TEXT %s "%s": the horizontal at y=%g crosses the text (y %g to %g); route the arrow through y<%g or y>%g'
                                   % (k, tx[:24], y1 - oy, b - oy, d - oy, b - oy - 8, d - oy + 8), (lo + hi) / 2, y1, None))
    # seta correndo em cima da borda de um frame: some no tracejado e parece parte do frame
    frames = [x for x in bx if x[0] == 'frame']
    segs = [(x1 + ox, y1 + oy, x2 + ox, y2 + oy) for (_, x1, y1, x2, y2) in segments(t)]
    for x1, y1, x2, y2 in segs:
        for _, _, fa, fb, fc, fd, ftx in frames:
            if x1 == x2 and any(abs(x1 - xb) <= 3 for xb in (fa, fc)):
                if min(max(y1, y2), fd) - max(min(y1, y2), fb) > 20:
                    issues.append(('ARROW-ON-EDGE the vertical at x=%g runs along the border of frame "%s"; keep it at least 16px away'
                                   % (x1 - ox, ftx[:24]), x1, (y1 + y2) / 2, None))
            elif y1 == y2 and any(abs(y1 - yb) <= 3 for yb in (fb, fd)):
                if min(max(x1, x2), fc) - max(min(x1, x2), fa) > 20:
                    issues.append(('ARROW-ON-EDGE the horizontal at y=%g runs along the border of frame "%s"; keep it at least 16px away'
                                   % (y1 - oy, ftx[:24]), (x1 + x2) / 2, y1, None))
    # ponta de seta no miolo de uma caixa: a seta nasce ou morre por cima do conteúdo
    por_seta = {}
    for (i, x1, y1, x2, y2) in segments(t):
        por_seta.setdefault(i, []).append((x1 + ox, y1 + oy, x2 + ox, y2 + oy))
    caixas = [x for x in bx if x[0] == 'chip']
    for i, ss in por_seta.items():
        for px, py in ((ss[0][0], ss[0][1]), (ss[-1][2], ss[-1][3])):
            for _, _, ca, cb, cc, cd, ctx in caixas:
                if ca + 6 < px < cc - 6 and cb + 6 < py < cd - 6:
                    issues.append(('ARROWHEAD-INSIDE the arrow has a tip at (%g,%g), in the middle of box "%s"; move the tip to the border'
                                   % (px - ox, py - oy, ctx[:24]), px, py, None))
                    break
    # rótulo da relação longe da própria seta: em cima dela ou ao lado, a no máximo 14px
    for k, n, a, b, c, d, tx in [x for x in bx if x[0] == 'rel']:
        proprios = [s for s, (i, *_r) in zip(segs, segments(t)) if i == n]
        if not proprios:
            continue
        dist = min(math.hypot(max(a - max(x1, x2), 0, min(x1, x2) - c), max(b - max(y1, y2), 0, min(y1, y2) - d))
                   for x1, y1, x2, y2 in proprios)
        if dist > 14:
            issues.append(('C4-REL-DETACHED label "%s" is %dpx from its arrow; keep it on the arrow or within 14px'
                           % (tx[:24], dist), a, b, None))
    # rótulo de aresta longe de qualquer seta: o leitor não sabe a que seta ele pertence
    if segs:
        for k, n, a, b, c, d, tx in [x for x in bx if x[0] == 'elabel']:
            dist = min(math.hypot(max(a - max(x1, x2), 0, min(x1, x2) - c), max(b - max(y1, y2), 0, min(y1, y2) - d))
                       for x1, y1, x2, y2 in segs)
            if dist > 30:
                issues.append(('LABEL-DETACHED elabel "%s" is %dpx from the nearest arrow; keep it within 30px of its arrow'
                               % (tx[:24], dist), a, b, None))
    return issues


ULTIMA_MEDICAO = {}


def lint_completo(fn, fix=False, static=False, tm=None):
    issues = lint(fn, fix)
    if not static:
        chrome = find_chrome()
        if chrome is None:
            issues.append(('NO-CHROME (overlap not checked; use --static to silence)', 0, 0, None))
        else:
            data = measure(fn, chrome, tm)
            if data is None:
                issues.append(('MEASURE-FAILED', 0, 0, None))
            else:
                ULTIMA_MEDICAO.clear()
                ULTIMA_MEDICAO.update(data)
                issues += check_medido(data, open(fn).read())
    return issues


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import theme as tema, lang as idioma
    flag_tema, resto = tema.tirar_flag(sys.argv[1:])
    flag_idioma, resto = idioma.tirar_flag(resto)
    args = [a for a in resto if not a.startswith('--')]
    fix = '--fix' in resto
    static = '--static' in resto
    total = 0
    for fn in args:
        tm = tema.tema(flag_tema, open(fn).read(), os.path.dirname(os.path.abspath(fn)))
        idioma.idioma(flag_idioma, fonte_html=open(fn).read())
        iss = lint_completo(fn, fix, static, tm)
        if iss:
            total += len(iss)
            print(fn)
            for kind, x, y, s in iss:
                if kind.startswith('OVERFLOW'):
                    print('  %s. Reduce the content, fix widths or declare <meta name="width">' % kind)
                elif kind.startswith(('C4-', 'COLOR-OUTSIDE-THEME', 'FONT-OUTSIDE-THEME')) and not kind.startswith('C4-REL-DETACHED'):
                    print('  %s' % kind)
                elif kind.startswith('MARKETING-COPY'):
                    print('  %s: rewrite in technical register' % kind)
                elif kind.startswith(('NO-BADGES', 'NO-STEPS', 'STEPS-MISMATCH', 'NO-CHROME', 'MEASURE-FAILED')):
                    print('  %s' % kind if kind.startswith(('NO-CHROME', 'MEASURE-FAILED')) else '  %s (badges=%g, steps=%g)' % (kind, x, y))
                elif kind.startswith(('CROSSES', 'COLLINEAR', 'BADGE-DETACHED', 'OVERLAP', 'ARROW-OVER-TEXT', 'INSIDE-BOX', 'TEXT-OVER-EDGE', 'ARROW-ON-EDGE', 'LABEL-DETACHED', 'ARROWHEAD-INSIDE', 'C4-REL-DETACHED')):
                    print('  %s at (%g,%g)' % (kind, x, y))
                else:
                    if kind.startswith('FIXED-BADGE'):
                        print('  %s: center moved from (%g,%g) to (%g,%g), on the arrow' % (kind, x, y, s[0], s[1]))
                    elif s and s[0] == 'sugestao':
                        print('  %s tip at (%g,%g): the nearest box has its border at (%g,%g); move the tip there'
                              % (kind, x, y, s[1], s[2]))
                    else:
                        print('  %s tip at (%g,%g)%s' % (kind, x, y, ' -> snap (%g,%g)' % s if s else ''))
    print('total:', total)
    sys.exit(1 if total else 0)
