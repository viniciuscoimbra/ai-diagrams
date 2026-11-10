#!/usr/bin/env python3
"""Build and lint of conceptual diagrams: swimlanes, cards, panels and cross-team flows.

Usage: python3 conceptual.py <source.html> [--height N|auto] [--width N] [--scale N]
(width: 1400px, or the one in the source's <meta name="width">)
                             [--display N] [--min-text N] [--min-label N] [--out DIR] [--lint-only]
                             [--theme NAME|path.json] [--lang pt-BR|en|es]

Difference from poster_lint.py: here there is no AWS topology, no required
numbered steps and no badge pinned to the arrow. The rules are different.

CSS: _style-conceptual.css or _style.css in the source folder; otherwise this
skill's assets/style-conceptual.css. Theme: --theme, the source's <meta name="theme">,
AI_DIAGRAMS_THEME or ai-diagrams, in that order (scripts/theme.py); it replaces the :root
of tokens and the font link, and the lint measures with the theme fonts. --height auto
measures the real height of .page in Chrome and uses it for the capture (default).

Checks (all measured in Chrome, same conditions as the screenshot):
  OVERFLOW       content larger than its box (text cut or squeezed).
  OVERLAP        two content boxes intersect.
  OFF-PAGE       element goes past the body width or out on the left.
  OFF-CANVAS     element inside .canvas goes past the canvas frame.
  TEXT-TOO-SMALL text that, shown at Confluence width, falls below the minimum.
                 Content has a high minimum (--min-text, default 10.5px displayed);
                 labels, identifiers and editorial frame have a low one (--min-label, 7.0).
  LABEL-OVER-BOX loose label on the canvas covering a content box it is not a child of.
                 A container (frame, lane) does not count: a label inside it is fine.
  ARROW-DETACHED arrow end that touches no box (tol 6px).
  ARROW-OVER-TEXT  arrow segment crossing the inside of a text box.
  COLLINEAR      two different arrows running on the same line (tol 4px, stretch > 8px).
  TEXT-OVER-LIFELINE  text over a lifeline or activation bar (sequence).
  MARKETING-COPY title, subtitle, kicker or band with sales vocabulary (technical_text.py).
  COLOR-OUTSIDE-THEME  literal hex or rgb() in the source; color only via var(--token) (theme_color.py).
  FONT-OUTSIDE-THEME   font-family with a literal family; font only via var(--font-text|mono).

Fails before measuring:
  NO-STYLE       the source has no /*STYLE*/ marker inside <style>.
  MEASURE-FAILED Chrome did not return the measurement.

Exit code 1 on any problem. The build only writes the PNG with lint at zero.
"""
import sys, os, re, json, subprocess, tempfile, shutil

MEASURE_JS = """
<script>
window.addEventListener('load', function () {
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () {
    var out = {boxes: [], body: document.body.getBoundingClientRect().width,
               pagew: 0, svg: null, canvas: null};
    var cvs = document.querySelector('.canvas');
    if (cvs) { var cr = cvs.getBoundingClientRect();
               out.canvas = [cr.left, cr.top, cr.right, cr.bottom]; }
    var pg = document.querySelector('.page');
    if (pg) out.pagew = pg.getBoundingClientRect().width;
    var seen = [];
    document.querySelectorAll('[class]').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      var cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') return;
      var folha = true;
      for (var i = 0; i < el.children.length; i++) {
        var c = el.children[i];
        if (c.tagName !== 'BR' && c.tagName !== 'B' && c.tagName !== 'SPAN' &&
            c.tagName !== 'IMG' && c.tagName !== 'CODE') { folha = false; break; }
      }
      var anc = [], q = el.parentElement;
      while (q && q !== document.body) { anc.push(q.className.toString()); q = q.parentElement; }
      seen.push({
        cls: el.className.toString(),
        anc: anc.join(' '),
        tag: el.tagName,
        folha: folha,
        x: r.left, y: r.top, x2: r.right, y2: r.bottom,
        sw: el.scrollWidth, cw: el.clientWidth,
        sh: el.scrollHeight, ch: el.clientHeight,
        fs: parseFloat(cs.fontSize),
        txt: (el.textContent || '').trim().slice(0, 46)
      });
    });
    out.boxes = seen;
    out.sw = document.documentElement.scrollWidth;
    var sv = document.querySelector('svg.edges');
    if (sv) { var sr = sv.getBoundingClientRect(); out.svg = [sr.left, sr.top]; }
    document.body.setAttribute('data-lint', encodeURIComponent(JSON.stringify(out)));
  });
});
</script>"""


def find_chrome():
    env = os.environ.get('POSTER_CHROME')
    if env and os.path.exists(env):
        return env
    for c in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              '/Applications/Chromium.app/Contents/MacOS/Chromium'):
        if os.path.exists(c):
            return c
    for n in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        p = shutil.which(n)
        if p:
            return p
    sys.exit('Chrome not found. Set POSTER_CHROME.')


def inline_css(fonte, tm):
    import theme as tema
    src = open(fonte).read()
    if not tema.tem_marcador(src):
        sys.exit('NO-STYLE: the source has no /*STYLE*/ marker inside <style>; without it the PNG has no design system. Copy the <head> of the template for this type.')
    d = os.path.dirname(os.path.abspath(fonte))
    for nome in ('_style-conceptual.css', '_style.css', '_style-conceptual.css', '_style.css'):
        p = os.path.join(d, nome)
        if os.path.exists(p):
            return tema.aplicar(src, open(p).read(), tm)
    skill = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'assets', 'style-conceptual.css')
    return tema.aplicar(src, open(skill).read(), tm)


def inline_icones(src):
    """Troca aws://categoria/arquivo.png pelo PNG em base64, como no build.py."""
    if 'aws://' not in src:
        return src
    import base64
    from build import find_iconbase
    base = find_iconbase()
    faltando = []

    def repl(m):
        p = os.path.join(base, m.group(1))
        if not os.path.exists(p):
            faltando.append(m.group(1))
            return m.group(0)
        return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()

    out = re.sub(r'aws://([a-z0-9/._-]+)', repl, src)
    if faltando:
        sys.exit('Missing icon(s) in %s: %s' % (base, ', '.join(sorted(set(faltando)))))
    return out


ALTURA_JS = """<script>window.addEventListener('load',function(){(document.fonts?document.fonts.ready:Promise.resolve()).then(function(){var p=document.querySelector('.page')||document.body;document.body.setAttribute('data-h',Math.ceil(p.getBoundingClientRect().bottom))})})</script>"""


def medir_altura(html, chrome, largura):
    """Altura real do conteúdo, para a captura não cortar nem sobrar."""
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(html.replace('</body>', ALTURA_JS + '</body>'))
        tmp = f.name
    try:
        r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            f'--window-size={largura},4000', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + tmp], capture_output=True, timeout=180)
        m = re.search(r'data-h="(\d+)"', r.stdout.decode('utf-8', 'replace'))
        return int(m.group(1)) if m else None
    finally:
        os.unlink(tmp)


def medir(html, chrome, largura, altura):
    t = html.replace('</body>', MEASURE_JS + '</body>')
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(t)
        tmp = f.name
    try:
        r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            f'--window-size={largura},{altura}',
                            '--virtual-time-budget=5000', '--dump-dom', 'file://' + tmp],
                           capture_output=True, timeout=180)
        m = re.search(r'data-lint="([^"]+)"', r.stdout.decode('utf-8', 'replace'))
        if not m:
            return None
        from urllib.parse import unquote
        return json.loads(unquote(m.group(1).replace('&amp;', '&')))
    finally:
        os.unlink(tmp)


# classes cujo conteúdo é caixa de conteúdo e não pode sobrepor outra caixa irmã
CAIXAS = ('card', 'chip', 'colhead', 'faixa', 'node', 'painel', 'campo', 'bloco', 'destino',
          'passo', 'no', 'centro', 'alt', 'esc', 'check', 'losango')
# onde uma ponta de seta pode encostar: as caixas mais os contêineres e a decisão.
# Contêiner (frame, lane) não entra em CAIXAS porque envolve os painéis por construção
# e reprovaria como sobreposição.
ALVOS = CAIXAS + ('frame', 'lane', 'lateral', 'vida', 'ativ')
# rótulos que flutuam sobre o canvas; nunca podem cobrir uma caixa alheia.
TEXTO_SOLTO = ('elabel', 'nota', 'mlabel')
# classes ignoradas no check de transbordo (contêineres com filhos posicionados)
SEM_TRANSBORDO = ('canvas', 'grid', 'wrap', 'page', 'col')
# texto que é rótulo, identificador ou moldura editorial: piso de legibilidade menor.
# A especificação visual trata slug como "dado operacional secundário".
SECUNDARIO = ('hdr', 'kicker', 'foot', 'slug', 'rot', 'sid', 'ptag', 'flabel', 'elabel',
              'chip', 'fase', 'pn', 'ls', 'sec', 'an', 'fk', 'ct', 'et', 'jct', 'jkey',
              'nsub', 'cb', 'lt', 'nn', 'rlabel')
# marcadores gráficos, não texto de leitura: fora do piso de legibilidade.
NAO_TEXTO = ('sq', 'badge', 'pnum')


def cls_set(c):
    return set(c.split())


def eh(el, nomes):
    return bool(cls_set(el['cls']) & set(nomes))


def segmentos(t):
    """Devolve uma lista por path: [(segmentos do path 1), (do path 2), ...].
    Agrupar por path importa: só o primeiro e o último ponto do caminho precisam
    encostar numa caixa. As dobras intermediárias correm pelo corredor.
    Paths dentro de <defs> são desenho de marcador, não seta: ficam de fora."""
    t = re.sub(r'<defs\b.*?</defs>', '', t, flags=re.S)
    caminhos = []
    for m in re.finditer(r'<path[^>]*\sd="([^"]+)"', t):
        d = m.group(1)
        out = []
        toks = re.findall(r'([MHVL])\s*(-?[\d.]+)(?:[ ,]+(-?[\d.]+))?', d)
        x = y = None
        for op, a, b in toks:
            a = float(a)
            b = float(b) if b else None
            if op == 'M':
                x, y = a, b
            elif op == 'L':
                out.append((x, y, a, b)); x, y = a, b
            elif op == 'H':
                out.append((x, y, a, y)); x = a
            elif op == 'V':
                out.append((x, y, x, a)); y = a
        if out:
            caminhos.append(out)
    return caminhos


def lint(data, fonte_txt, exibicao, piso, piso_rot):
    iss = []
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import technical_text as tt
    for termo, trecho in tt.marketing(tt.textos_de_abertura(fonte_txt)):
        iss.append(('MARKETING-COPY "%s" in "%s": %s' % (termo, trecho, tt.MENSAGEM),))
    import theme_color
    for lit, linha in theme_color.cores_fora(fonte_txt):
        iss.append(('COLOR-OUTSIDE-THEME %s on line %d: %s' % (lit, linha, theme_color.MENSAGEM),))
    for dec, linha in theme_color.fontes_fora(fonte_txt):
        iss.append(('FONT-OUTSIDE-THEME %s on line %d: %s' % (dec, linha, theme_color.MENSAGEM_FONTE),))
    bx = data['boxes']
    bodyw = data['body'] or 1
    escala = exibicao / bodyw

    if data.get('sw', 0) > bodyw + 1:
        iss.append(('OVERFLOW-PAGE document of %dpx on a %dpx page: the capture cuts the right side'
                    % (data['sw'], bodyw),))
    for el in bx:
        c = cls_set(el['cls'])
        if el['sw'] > el['cw'] + 1 and not (c & set(SEM_TRANSBORDO)):
            iss.append(('OVERFLOW-X %s "%s" (%d>%d)' % (el['cls'], el['txt'], el['sw'], el['cw']),))
        if el['sh'] > el['ch'] + 1 and not (c & set(SEM_TRANSBORDO)):
            iss.append(('OVERFLOW-Y %s "%s" (%d>%d)' % (el['cls'], el['txt'], el['sh'], el['ch']),))
        if el['x'] < -0.5 or el['x2'] > bodyw + 0.5:
            iss.append(('OFF-PAGE %s "%s" (%.0f..%.0f of %.0f)'
                        % (el['cls'], el['txt'], el['x'], el['x2'], bodyw),))
        if el['folha'] and el['txt'] and not (c & set(NAO_TEXTO)):
            lim = piso_rot if (c & set(SECUNDARIO)) else piso
            if el['fs'] * escala < lim:
                iss.append(('TEXT-TOO-SMALL %s "%s" (%.1fpx -> %.1fpx displayed, minimum %.1f)'
                            % (el['cls'], el['txt'], el['fs'], el['fs'] * escala, lim),))

    # rótulo solto no canvas não pode cobrir caixa da qual não é filho.
    soltos = [e for e in bx if eh(e, TEXTO_SOLTO)]
    for s in soltos:
        for a in bx:
            # contêiner (frame, lane) não conta: rótulo dentro dele é legítimo.
            if not eh(a, CAIXAS):
                continue
            if set(a['cls'].split()) & set(s['anc'].split()):
                continue  # o rótulo está dentro dessa caixa
            w = min(s['x2'], a['x2']) - max(s['x'], a['x'])
            h = min(s['y2'], a['y2']) - max(s['y'], a['y'])
            if w > 2 and h > 2:
                iss.append(('LABEL-OVER-BOX %s "%s" over %s "%s"'
                            % (s['cls'], s['txt'][:26], a['cls'], a['txt'][:26]),))

    cv = data.get('canvas')
    if cv:
        for el in bx:
            if 'canvas' not in el['anc'].split() and 'canvas' not in el['cls'].split():
                continue
            if 'canvas' in el['cls'].split():
                continue
            if (el['x'] < cv[0] - 0.5 or el['x2'] > cv[2] + 0.5
                    or el['y'] < cv[1] - 0.5 or el['y2'] > cv[3] + 0.5):
                iss.append(('OFF-CANVAS %s "%s" (%.0f..%.0f in %.0f..%.0f)'
                            % (el['cls'], el['txt'], el['x'], el['x2'], cv[0], cv[2]),))

    caixas = [e for e in bx if eh(e, CAIXAS)]
    for i in range(len(caixas)):
        for j in range(i + 1, len(caixas)):
            a, b = caixas[i], caixas[j]
            w = min(a['x2'], b['x2']) - max(a['x'], b['x'])
            h = min(a['y2'], b['y2']) - max(a['y'], b['y'])
            if w > 2 and h > 2:
                iss.append(('OVERLAP %s×%s "%s" / "%s"'
                            % (a['cls'], b['cls'], a['txt'][:22], b['txt'][:22]),))

    if data.get('svg'):
        ox, oy = data['svg']
        alvos = [(e['x'], e['y'], e['x2'], e['y2']) for e in bx if eh(e, ALVOS)]
        caminhos = segmentos(fonte_txt)
        segs = [s for c in caminhos for s in c]
        if caminhos and not alvos:
            iss.append(('NO-TARGETS: the drawing has arrows but no box in ALVOS=%s. '
                        'Give the boxes one of these classes or extend the tuple.'
                        % (ALVOS,),))
        # badge fica sobre a seta por desenho: marca o passo, não é texto de leitura
        textos = [e for e in bx if e['folha'] and e['txt'] and not eh(e, ALVOS) and not eh(e, NAO_TEXTO)]
        for c_ in caminhos:
            ini = (c_[0][0], c_[0][1])
            fim = (c_[-1][2], c_[-1][3])
            for (rx, ry) in (ini, fim):
                px, py = rx + ox, ry + oy
                if not any(a - 6 <= px <= c + 6 and b - 6 <= py <= d + 6 for (a, b, c, d) in alvos):
                    iss.append(('ARROW-DETACHED end at (%.0f,%.0f)' % (rx, ry),))
        # setas diferentes não podem correr na mesma linha: o leitor não separa uma da outra
        for i in range(len(caminhos)):
            for j in range(i + 1, len(caminhos)):
                for (a1, b1, a2, b2) in caminhos[i]:
                    for (c1, d1, c2, d2) in caminhos[j]:
                        if a1 == a2 and c1 == c2 and abs(a1 - c1) <= 4:
                            ov = min(max(b1, b2), max(d1, d2)) - max(min(b1, b2), min(d1, d2))
                            if ov > 8:
                                iss.append(('COLLINEAR-V at x=%.0f (%.0f px)' % (a1, ov),))
                        elif b1 == b2 and d1 == d2 and abs(b1 - d1) <= 4:
                            ov = min(max(a1, a2), max(c1, c2)) - max(min(a1, a2), min(c1, c2))
                            if ov > 8:
                                iss.append(('COLLINEAR-H at y=%.0f (%.0f px)' % (b1, ov),))
        for (x1, y1, x2, y2) in segs:
            for e in textos:
                a, b, c, d = e['x'], e['y'], e['x2'], e['y2']
                sx1, sy1, sx2, sy2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
                if sx1 == sx2 and a + 2 < sx1 < c - 2 and min(sy1, sy2) < d - 2 and max(sy1, sy2) > b + 2:
                    iss.append(('ARROW-OVER-TEXT "%s"' % e['txt'][:24],))
                elif sy1 == sy2 and b + 2 < sy1 < d - 2 and min(sx1, sx2) < c - 2 and max(sx1, sx2) > a + 2:
                    iss.append(('ARROW-OVER-TEXT "%s"' % e['txt'][:24],))
    # linha de vida e barra de ativação (sequência) não passam por baixo de texto
    for v in bx:
        if not eh(v, ('vida', 'ativ')):
            continue
        cx = (v['x'] + v['x2']) / 2
        for e in bx:
            if not (e['folha'] and e['txt']) or eh(e, NAO_TEXTO) or eh(e, ALVOS):
                continue
            if 'nota-seq' in e['anc'].split():   # a nota é caixa opaca por cima da linha
                continue
            h = min(v['y2'], e['y2']) - max(v['y'], e['y'])
            if h <= 2:
                continue
            if eh(v, ('ativ',)):
                cruza = min(v['x2'], e['x2']) - max(v['x'], e['x']) > 2
            else:
                cruza = e['x'] + 1 < cx < e['x2'] - 1
            if cruza:
                iss.append(('TEXT-OVER-LIFELINE %s "%s" over the %s at x=%.0f'
                            % (e['cls'], e['txt'][:26], 'activation bar' if eh(v, ('ativ',)) else 'lifeline', cx),))
    return iss, escala


def resumo_escala(data, escala):
    """Menor tamanho efetivo por classe de texto: dado para a auditoria visual."""
    por = {}
    for el in data['boxes']:
        if el['folha'] and el['txt']:
            k = el['cls'].split()[-1] if el['cls'] else el['tag']
            por[k] = min(por.get(k, 999), el['fs'])
    return sorted(((k, v, v * escala) for k, v in por.items()), key=lambda r: r[2])


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import theme as tema, lang as idioma
    flag_tema, sys.argv[1:] = tema.tirar_flag(sys.argv[1:])
    flag_idioma, sys.argv[1:] = idioma.tirar_flag(sys.argv[1:])
    import compat
    argv = sys.argv[1:]
    so_lint = compat.has_flag(argv, '--lint-only', '--so-lint')
    def opt(novo, antigo, d):
        nonlocal argv
        v, argv = compat.take_flag(argv, novo, antigo, '%s needs a value' % novo)
        if v is None:
            return d
        try:
            return type(d)(v) if d is not None else v
        except ValueError:
            sys.exit('%s: invalid value "%s"' % (novo, v))
    piso_rot = opt('--min-label', '--piso-rot', 7.0)
    piso = opt('--min-text', '--piso', 10.5)
    largura = opt('--width', '--largura', 0)
    altura = opt('--height', '--altura', 'auto')
    escala_cap = opt('--scale', '--escala', 2.0)
    exibicao = opt('--display', '--exibicao', 1000)
    out_dir = opt('--out', None, None)
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    fonte = os.path.abspath(args[0])
    if not largura:
        # 1400px, ou a largura que o fonte declara quando o desenho precisa de mais
        m = re.search(r'<meta name="(?:width|largura)" content="(\d+)"', open(fonte).read())
        largura = int(m.group(1)) if m else 1400
    src_dir = os.path.dirname(fonte)
    if out_dir is None:
        out_dir = os.path.dirname(src_dir) if os.path.basename(src_dir) == '_src' else src_dir

    tm = tema.tema(flag_tema, open(fonte).read(), src_dir)
    tr = idioma.idioma(flag_idioma, fonte_html=open(fonte).read())
    chrome = find_chrome()
    html = idioma.aplicar(inline_icones(inline_css(fonte, tm)), tr)
    if altura == 'auto':
        altura = medir_altura(html, chrome, largura)
        if altura is None:
            sys.exit('MEASURE-FAILED: could not measure the height of .page.')
    else:
        altura = int(altura)
    data = medir(html, chrome, largura, altura)
    if data is None:
        sys.exit('MEASURE-FAILED: Chrome did not return data-lint.')
    iss, escala = lint(data, open(fonte).read(), exibicao, piso, piso_rot)

    print('display scale: %d CSS px -> %d px (%.2fx)' % (data['body'], exibicao, escala))
    print('smallest text per class (css -> displayed):')
    for k, v, e in resumo_escala(data, escala)[:12]:
        print('   %-16s %5.1f -> %4.1f' % (k, v, e))
    if iss:
        print('\nLINT FAILED %s (%d):' % (os.path.basename(fonte), len(iss)))
        for (t,) in iss:
            print('  ' + t)
        sys.exit(1)
    print('\nlint 0')
    if so_lint:
        return

    name = os.path.basename(fonte)
    html_out = os.path.join(out_dir, name)
    open(html_out, 'w').write(html)
    png = os.path.join(out_dir, name.replace('.html', '.png'))
    r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                        f'--screenshot={png}', f'--window-size={largura},{altura}',
                        f'--force-device-scale-factor={escala_cap}', 'file://' + html_out],
                       capture_output=True, timeout=180)
    if not os.path.exists(png):
        sys.exit('Chrome did not write the PNG. ' + r.stderr.decode()[-800:])
    print('OK %s' % html_out)
    print('OK %s' % png)


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        sys.exit('Chrome did not answer in time. Check the network (fonts come from Google Fonts), '
                 'close other stuck headless Chrome processes and check POSTER_CHROME.')
