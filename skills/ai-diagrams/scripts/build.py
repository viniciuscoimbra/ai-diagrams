#!/usr/bin/env python3
"""Poster build: inlines CSS and aws:// icons, renders the PNG with headless Chrome.

Usage: python3 build.py <source.html> [height-px] [--out DIR] [--theme NAME|path.json] [--lang pt-BR|en|es]

Without a height, it uses the real page height measured in Chrome. A height smaller
than the page fails (CROPPED), because it would cut the footer.

Reads the source, injects the design system at the /*STYLE*/ marker, embeds the
aws://category/file.png icons as base64 and takes the screenshot (1760px wide,
scale 1.5; another width if the source declares <meta name="width">). Writes the
self-contained HTML and the PNG to the output folder.

Default output: if the source is in a folder named _src, writes to the parent folder
(source in _src/, deliverable next to it); otherwise, writes next to the source.

CSS: uses _style.css or style.css in the source folder if present; otherwise the
style.css bundled with this skill (assets/).

Theme: --theme, <meta name="theme"> in the source, AI_DIAGRAMS_THEME or ai-diagrams, in
that order (scripts/theme.py). The CSS :root of tokens becomes the theme's and the Google
Fonts link becomes the one for the theme families; the source geometry does not change.

Icons: the `diagrams` pip package (mingrammer), which installs the official AWS PNGs
in <site-packages>/resources/aws. Detected automatically; override with the
POSTER_ICONBASE environment variable.

Chrome: detected in the usual macOS and Linux paths; override with the
POSTER_CHROME environment variable.
"""
import sys, os, re, base64, subprocess, shutil


def find_iconbase():
    env = os.environ.get('POSTER_ICONBASE')
    if env and os.path.isdir(env):
        return env
    try:
        import diagrams
        cand = os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)),
                            'resources', 'aws')
        if os.path.isdir(cand):
            return cand
    except ImportError:
        pass
    sys.exit('AWS icons not found. Install them with pip3 install diagrams, '
             'or point POSTER_ICONBASE to a resources/aws folder.')


def find_chrome():
    env = os.environ.get('POSTER_CHROME')
    if env and os.path.exists(env):
        return env
    candidates = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        p = shutil.which(name)
        if p:
            return p
    sys.exit('Chrome not found. Install Google Chrome or point POSTER_CHROME to it.')


def find_css(src_dir):
    for name in ('_style.css', 'style.css', '_style.css', 'style.css'):
        p = os.path.join(src_dir, name)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'style.css')


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import theme as tema, lang as idioma, compat
    flag_tema, sys.argv[1:] = tema.tirar_flag(sys.argv[1:])
    flag_idioma, sys.argv[1:] = idioma.tirar_flag(sys.argv[1:])
    out_dir, sys.argv[1:] = compat.take_flag(sys.argv[1:], '--out', '--saida',
                                             '--out without a value; pass the output folder')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    fonte = os.path.abspath(args[0])
    H = int(args[1]) if len(args) > 1 else None
    src_dir = os.path.dirname(fonte)
    if out_dir is None:
        out_dir = os.path.dirname(src_dir) if os.path.basename(src_dir) == '_src' else src_dir

    src = open(fonte).read()
    tm = tema.tema(flag_tema, src, src_dir)
    tr = idioma.idioma(flag_idioma, fonte_html=src)
    iconbase = find_iconbase()
    chrome = find_chrome()
    if not tema.tem_marcador(src):
        sys.exit('NO-STYLE: the source has no /*STYLE*/ marker inside <style>; without it the PNG comes out without the design system. Copy the <head> from the template of the diagram type.')
    src = idioma.aplicar(tema.aplicar(src, open(find_css(src_dir)).read(), tm), tr)

    _cache = {}
    faltando = []

    def repl(m):
        p = os.path.join(iconbase, m.group(1))
        if not os.path.exists(p):
            faltando.append(m.group(1))
            return m.group(0)
        if p not in _cache:
            _cache[p] = 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
        return _cache[p]

    final = re.sub(r'aws://([a-z0-9/._-]+)', repl, src)
    if faltando:
        sys.exit('Icon(s) not found in %s: %s. List the available ones with ls %s/<category>/' %
                 (iconbase, ', '.join(sorted(set(faltando))), iconbase))

    # Gate determinístico: o lint roda no fonte ANTES de qualquer saída.
    # Setas, badges, passos e sobreposição medida no Chrome; problema reprova o build.
    import importlib.util as _ilu
    _lint_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poster_lint.py')
    _spec = _ilu.spec_from_file_location('poster_lint', _lint_path)
    _pl = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_pl)
    _issues = _pl.lint_completo(fonte, tm=tm)
    if _issues:
        print('LINT FAILED %s:' % fonte)
        for kind, x, y, _s in _issues:
            print('  %s at (%g,%g)' % (kind, x, y))
        sys.exit('Fix the source and run again. (checks: see the docstring of poster_lint.py)')

    # Altura da captura: a medida no Chrome quando não vem no comando; altura menor que
    # o conteúdo corta o rodapé, e isso reprova.
    precisa = _pl.ULTIMA_MEDICAO.get('altura')
    if H is None:
        H = precisa or 1500
    elif precisa and H < precisa:
        sys.exit('CROPPED: the page is %dpx tall and the capture asked for %dpx. Run without the height '
                 '(it is measured automatically) or with %d.' % (precisa, H, precisa))

    # Largura da captura: 1760px, ou a que o fonte declara em <meta name="largura">
    # quando o desenho precisa de mais espaço para ficar legível (o DER declara).
    m = re.search(r'<meta name="(?:width|largura)" content="(\d+)"', src)
    W = int(m.group(1)) if m else 1760

    name = os.path.basename(fonte)
    os.makedirs(out_dir, exist_ok=True)
    html_out = os.path.join(out_dir, name)
    open(html_out, 'w').write(final)
    png = os.path.join(out_dir, name.replace('.html', '.png'))
    r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                        f'--screenshot={png}', f'--window-size={W},{H}',
                        '--force-device-scale-factor=1.5', 'file://' + html_out],
                       capture_output=True, timeout=120)
    if not os.path.exists(png):
        sys.exit('Chrome did not write the PNG. ' + r.stderr.decode()[-800:])
    print(f'OK {html_out}')
    print(f'OK {png}')


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        sys.exit('Chrome did not respond in time. Check the network (fonts come from Google Fonts), '
                 'close other stuck headless Chrome processes and check POSTER_CHROME.')
