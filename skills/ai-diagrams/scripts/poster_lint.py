#!/usr/bin/env python3
"""Lint geométrico de posters.
Uso: poster_lint.py [--fix] [--static] arquivo.html [...]
Checks:
1. Ponta e início de seta encostam numa caixa ou borda de frame (tol 6px);
   entre 6 e 60px na direção do segmento, --fix faz o snap.
2. Roteamento ortogonal: nenhum segmento de seta atravessa o interior de
   caixa que não é seu endpoint (ATRAVESSA); segmentos paralelos de setas
   diferentes não podem ser colineares (COLINEAR); rotear por corredores.
3. Passos numerados obrigatórios: o canvas precisa de badges 1..N e a seção
   .passos precisa de itens correspondentes (SEM-BADGES / SEM-PASSOS /
   PASSOS-DIVERGEM).
4. Badge nasce com a seta: o centro de cada badge fica sobre a linha da seta
   (tol 6px), podendo deslizar ao longo dela; badge ao lado ou solto reprova
   (BADGE-SOLTO).
5. Sobreposicao medida no Chrome (mesmas condicoes do screenshot): badge,
   rotulos de no (.nl/.ns), icones, .elabel, .flabel e chips nao podem se
   sobrepor (SOBREPOE); seta nao passa por cima de texto, inclusive o de
   dentro dos .bchip (SETA-SOBRE-TEXTO); seta nao corre sobre a borda de frame
   (SETA-NA-BORDA); .elabel fica a ate 30px de alguma seta (ROTULO-SOLTO);
   ponta de seta nao fica no miolo de uma caixa (PONTA-DENTRO).
   Pula-se com --static (ou sem Chrome disponivel, com aviso).
7. Transbordo medido no Chrome: nada passa da borda direita da pagina, que e
   onde a captura corta (TRANSBORDA).
8. Registro tecnico: titulo, subtitulo, kicker e faixas sem vocabulario de
   marketing (TEXTO-MARKETING; lista em texto_tecnico.py).
9. C4: cada elemento .bchip.c4 tem tipo (.bn) e nome (.bt), e a página tem a
   legenda .c4leg (C4-SEM-TIPO, C4-SEM-LEGENDA).
10. Cor só do tema: hexadecimal ou rgb() literal no fonte reprova
   (COR-FORA-DO-TEMA; regra em cor_tema.py).
6. Documento sem desenho de setas (sem <svg class="edges">, como a matriz de
   dependencia) nao narra fluxo: os checks 3 e 4 nao se aplicam a ele. Os
   demais continuam valendo.
Saida: exit code 1 se houver qualquer problema. O build.py chama este lint
antes do PNG e reprova o poster com problema."""
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
                    issues.append(('ATRAVESSA', x1, (lo + hi) / 2, None))
                elif hi - lo > 10 and ultimo[i] == k and _near_box_pt(x2, y2, box):
                    issues.append(('DENTRO-DA-CAIXA %gpx: a seta corre por dentro da caixa que liga; encoste a ponta na borda' % (hi - lo), x1, (lo + hi) / 2, None))
            elif y1 == y2 and b + 2 < y1 < d - 2:
                lo, hi = max(min(x1, x2), a + 2), min(max(x1, x2), c - 2)
                if hi - lo > 4 and not (_near_box_pt(x1, y1, box) or _near_box_pt(x2, y2, box)):
                    issues.append(('ATRAVESSA', (lo + hi) / 2, y1, None))
                elif hi - lo > 10 and ultimo[i] == k and _near_box_pt(x2, y2, box):
                    issues.append(('DENTRO-DA-CAIXA %gpx: a seta corre por dentro da caixa que liga; encoste a ponta na borda' % (hi - lo), (lo + hi) / 2, y1, None))
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
                        issues.append(('COLINEAR-' + kind, s1[oi], ov(s1[r1], s1[r2], s2[r1], s2[r2]), None))
    return issues

def check_passos(t):
    issues = []
    badges = re.findall(r'<div class="badge"[^>]*>\s*(\d+)', t)
    pitems = re.findall(r'class="pb">\s*(\d+)', t)
    if not badges: issues.append(('SEM-BADGES', 0, 0, None))
    if not pitems: issues.append(('SEM-PASSOS', 0, 0, None))
    if badges and pitems and set(badges) != set(pitems):
        issues.append(('PASSOS-DIVERGEM', len(set(badges)), len(set(pitems)), None))
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
            issues.append(('BADGE-SOLTO ' + n, cx, cy, None))
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
    import texto_tecnico as tt
    return [('TEXTO-MARKETING "%s" em "%s"' % (termo, trecho), 0, 0, None)
            for termo, trecho in tt.marketing(tt.textos_de_abertura(t))]


def check_cores(t):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cor_tema
    return [('COR-FORA-DO-TEMA %s na linha %d: %s' % (lit, linha, cor_tema.MENSAGEM), 0, 0, None)
            for lit, linha in cor_tema.cores_fora(t)]


def check_c4(t):
    """C4: todo elemento diz o tipo (.bn) e o nome (.bt), e a página traz a legenda (.c4leg)."""
    els = re.findall(r'<div class="bchip c4[^"]*"[^>]*>(.*?)\n  </div>', t, re.S)
    if not els:
        return []
    issues = [('C4-SEM-TIPO: elemento "%s" precisa de .bn (tipo e tecnologia) e .bt (nome)'
               % re.sub(r'<[^>]+>|\s+', ' ', e).strip()[:40], 0, 0, None)
              for e in els if 'class="bn"' not in e or 'class="bt"' not in e]
    if 'class="c4leg"' not in t:
        issues.append(('C4-SEM-LEGENDA: inclua a seção "Legenda C4" com .c4leg', 0, 0, None))
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
            issues.append(('FIXADO', x, y, s))
        else:
            issues.append(('SOLTA', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('AJUSTAVEL', x, y, s))
    for m in re.finditer(r'<path d="([^"]+)"[^>]*marker-end[^>]*/>', t):
        r = start_of_path(m.group(1))
        if not r: continue
        x, y, dx, dy = r
        if near_solid(x, y, solid) or near_frame_border(x, y, frames): continue
        s = march(x, y, dx, dy, solid, frames) or recuar(x, y, dx, dy, vertices(m.group(1))[1], solid, frames)
        if s and fix:
            out = out.replace(m.group(1), fix_path_start(m.group(1), *s), 1)
            issues.append(('FIXADO-INICIO', x, y, s))
        else:
            issues.append(('SOLTA-INICIO', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('AJUSTAVEL-INICIO', x, y, s))
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
            issues.append(('FIXADO', x, y, s))
        else:
            issues.append(('SOLTA', x, y, ('sugestao',) + tuple(caixa_mais_proxima(x, y, solid, frames)[1:])) if not s else ('AJUSTAVEL', x, y, s))
        sx, sy = x1, y1
        if not (near_solid(sx, sy, solid) or near_frame_border(sx, sy, frames)):
            s2 = march(sx, sy, -dx, -dy, solid, frames)
            if s2 and fix:
                o2 = m.group(0) if m.group(0) in out else None
                if o2:
                    n2 = o2.replace('x1="%s"' % m.group(1), 'x1="%g"' % s2[0], 1).replace('y1="%s"' % m.group(2), 'y1="%g"' % s2[1], 1)
                    out = out.replace(o2, n2, 1)
                    issues.append(('FIXADO-INICIO', sx, sy, s2))
            elif not (s2 and fix):
                issues.append(('SOLTA-INICIO' if not s2 else 'AJUSTAVEL-INICIO', sx, sy, s2))
    issues += check_routing(t, solid)
    if '<svg class="edges"' in t:
        issues += check_passos(t)
        if fix:
            out, fixos = fix_badges(out)
            issues += [('FIXADO-BADGE ' + n, x, y, (nx, ny)) for n, x, y, nx, ny in fixos]
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
    document.querySelectorAll('.chip,.bchip,.oss,.svc').forEach(function (b) { push('chip', -1, b); });
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
    """Mesma busca do build.py: _estilo.css ou estilo.css do projeto, senao o da skill."""
    for name in ('_estilo.css', 'estilo.css'):
        p = os.path.join(src_dir, name)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'estilo.css')


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


def measure(fn, chrome):
    """Renderiza no Chrome e devolve as caixas reais (coordenadas do canvas)."""
    t = open(fn).read()
    if '/*ESTILO*/' in t:
        t = t.replace('/*ESTILO*/', open(find_css(os.path.dirname(os.path.abspath(fn)))).read())
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
            sys.exit('O Chrome não respondeu em 120s ao medir %s. Confira a rede (as fontes vêm do '
                     'Google Fonts), feche outros Chrome headless presos e confira POSTER_CHROME (%s). '
                     'Para rodar só os checks sem Chrome, use --static.' % (fn, chrome))
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
          ('nl', 'chip'), ('ns', 'chip')}


def check_medido(data, t):
    issues = []
    bw, sw = data.get('largura', [0, 0])
    if sw > bw + 1 or data.get('fora'):
        alvo = '; '.join('%s "%s" até %dpx' % (c[:20], tx, r) for c, r, tx in data.get('fora', [])[:3])
        issues.append(('TRANSBORDA conteúdo passa da largura da página (%dpx, documento com %dpx): %s'
                       % (bw, sw, alvo or 'ver o PNG'), 0, 0, None))
    bx = data['boxes']
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            k1, n1, *r1, tx1 = bx[i]
            k2, n2, *r2, tx2 = bx[j]
            if k1 in ('nl', 'ns', 'icon') and k2 in ('nl', 'ns', 'icon') and n1 == n2:
                continue  # partes do mesmo no
            if (k1, k2) in _PARES or (k2, k1) in _PARES:
                if _inter(r1, r2):
                    issues.append(('SOBREPOE %s×%s "%s"' % (k1, k2, (tx1 or tx2)[:24]),
                                   max(r1[0], r2[0]), max(r1[1], r2[1]), None))
    # borda de frame (AWS Cloud, conta, zona) cruzando texto de nó ou rótulo
    for k, n, a, b, c, d, tx in [x for x in bx if x[0] in ('nl', 'ns', 'elabel')]:
        for _, _, fa, fb, fc, fd, _ in [x for x in bx if x[0] == 'frame']:
            corta_v = any(a + 2 < xb < c - 2 for xb in (fa, fc)) and min(d, fd) - max(b, fb) > 2
            corta_h = any(b + 2 < yb < d - 2 for yb in (fb, fd)) and min(c, fc) - max(a, fa) > 2
            if corta_v or corta_h:
                issues.append(('TEXTO-SOBRE-BORDA %s "%s": a borda de um frame corta o texto; mova o nó para dentro ou para fora do frame' % (k, tx[:24]), a, b, None))
                break
    ox, oy = data.get('svg', [0, 0])
    textos = [b for b in bx if b[0] in ('nl', 'ns', 'elabel', 'flabel', 'btx')]
    for (_, x1, y1, x2, y2) in segments(t):
        x1, y1, x2, y2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
        for k, n, a, b, c, d, tx in textos:
            box = (a, b, c, d)
            if _near_box_pt(x1, y1, box) or _near_box_pt(x2, y2, box):
                continue
            if x1 == x2 and a + 2 < x1 < c - 2:
                lo, hi = max(min(y1, y2), b + 2), min(max(y1, y2), d - 2)
                if hi - lo > 3:
                    issues.append(('SETA-SOBRE-TEXTO %s "%s": a vertical em x=%g cruza o texto (x %g a %g); passe a seta por x<%g ou x>%g, ou saia pela lateral do ícone'
                                   % (k, tx[:24], x1 - ox, a - ox, c - ox, a - ox - 8, c - ox + 8), x1, (lo + hi) / 2, None))
            elif y1 == y2 and b + 2 < y1 < d - 2:
                lo, hi = max(min(x1, x2), a + 2), min(max(x1, x2), c - 2)
                if hi - lo > 3:
                    issues.append(('SETA-SOBRE-TEXTO %s "%s": a horizontal em y=%g cruza o texto (y %g a %g); passe a seta por y<%g ou y>%g'
                                   % (k, tx[:24], y1 - oy, b - oy, d - oy, b - oy - 8, d - oy + 8), (lo + hi) / 2, y1, None))
    # seta correndo em cima da borda de um frame: some no tracejado e parece parte do frame
    frames = [x for x in bx if x[0] == 'frame']
    segs = [(x1 + ox, y1 + oy, x2 + ox, y2 + oy) for (_, x1, y1, x2, y2) in segments(t)]
    for x1, y1, x2, y2 in segs:
        for _, _, fa, fb, fc, fd, ftx in frames:
            if x1 == x2 and any(abs(x1 - xb) <= 3 for xb in (fa, fc)):
                if min(max(y1, y2), fd) - max(min(y1, y2), fb) > 20:
                    issues.append(('SETA-NA-BORDA a vertical em x=%g corre sobre a borda do frame "%s"; afaste pelo menos 16px'
                                   % (x1 - ox, ftx[:24]), x1, (y1 + y2) / 2, None))
            elif y1 == y2 and any(abs(y1 - yb) <= 3 for yb in (fb, fd)):
                if min(max(x1, x2), fc) - max(min(x1, x2), fa) > 20:
                    issues.append(('SETA-NA-BORDA a horizontal em y=%g corre sobre a borda do frame "%s"; afaste pelo menos 16px'
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
                    issues.append(('PONTA-DENTRO a seta tem ponta em (%g,%g), no miolo da caixa "%s"; leve a ponta até a borda'
                                   % (px - ox, py - oy, ctx[:24]), px, py, None))
                    break
    # rótulo de aresta longe de qualquer seta: o leitor não sabe a que seta ele pertence
    if segs:
        for k, n, a, b, c, d, tx in [x for x in bx if x[0] == 'elabel']:
            dist = min(math.hypot(max(a - max(x1, x2), 0, min(x1, x2) - c), max(b - max(y1, y2), 0, min(y1, y2) - d))
                       for x1, y1, x2, y2 in segs)
            if dist > 30:
                issues.append(('ROTULO-SOLTO elabel "%s" está a %dpx da seta mais próxima; encoste a até 30px da sua seta'
                               % (tx[:24], dist), a, b, None))
    return issues


ULTIMA_MEDICAO = {}


def lint_completo(fn, fix=False, static=False):
    issues = lint(fn, fix)
    if not static:
        chrome = find_chrome()
        if chrome is None:
            issues.append(('SEM-CHROME (sobreposicao nao verificada; use --static para silenciar)', 0, 0, None))
        else:
            data = measure(fn, chrome)
            if data is None:
                issues.append(('MEDICAO-FALHOU', 0, 0, None))
            else:
                ULTIMA_MEDICAO.clear()
                ULTIMA_MEDICAO.update(data)
                issues += check_medido(data, open(fn).read())
    return issues


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fix = '--fix' in sys.argv
    static = '--static' in sys.argv
    total = 0
    for fn in args:
        iss = lint_completo(fn, fix, static)
        if iss:
            total += len(iss)
            print(fn)
            for kind, x, y, s in iss:
                if kind.startswith('TRANSBORDA'):
                    print('  %s. Reduza o conteúdo, fixe larguras ou declare <meta name="largura">' % kind)
                elif kind.startswith(('C4-', 'COR-FORA-DO-TEMA')):
                    print('  %s' % kind)
                elif kind.startswith('TEXTO-MARKETING'):
                    print('  %s: reescreva em registro técnico' % kind)
                elif kind.startswith(('SEM-', 'PASSOS', 'MEDICAO')):
                    print('  %s' % kind if kind.startswith(('SEM-CHROME', 'MEDICAO')) else '  %s (badges=%g, passos=%g)' % (kind, x, y))
                elif kind.startswith(('ATRAVESSA', 'COLINEAR', 'BADGE-SOLTO', 'SOBREPOE', 'SETA-SOBRE-TEXTO', 'DENTRO-DA-CAIXA', 'TEXTO-SOBRE-BORDA', 'SETA-NA-BORDA', 'ROTULO-SOLTO', 'PONTA-DENTRO')):
                    print('  %s em (%g,%g)' % (kind, x, y))
                else:
                    if kind.startswith('FIXADO-BADGE'):
                        print('  %s: centro de (%g,%g) para (%g,%g), sobre a seta' % (kind, x, y, s[0], s[1]))
                    elif s and s[0] == 'sugestao':
                        print('  %s ponta em (%g,%g): a caixa mais próxima tem borda em (%g,%g); leve a ponta até lá'
                              % (kind, x, y, s[1], s[2]))
                    else:
                        print('  %s ponta em (%g,%g)%s' % (kind, x, y, ' -> snap (%g,%g)' % s if s else ''))
    print('total:', total)
    sys.exit(1 if total else 0)
