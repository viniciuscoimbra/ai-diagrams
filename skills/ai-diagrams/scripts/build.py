#!/usr/bin/env python3
"""Build de poster de arquitetura: inline de CSS e ícones aws://, PNG via Chrome headless.

Uso: python3 build.py <fonte.html> [altura-px] [--out DIR] [--tema NOME|caminho.json]

Sem altura, usa a altura real da página medida no Chrome. Altura menor que a
página reprova (CORTADO), porque cortaria o rodapé.

Lê o fonte, injeta o design system no marcador /*ESTILO*/, embute os ícones
aws://categoria/arquivo.png em base64 e tira o screenshot (1760px de largura,
escala 1.5; outra largura se o fonte declarar <meta name="largura">). Grava o HTML self-contained e o PNG no diretório de saída.

Saída default: se o fonte está numa pasta chamada _src, grava na pasta pai
(convenção fonte em _src/, entregável ao lado); senão, grava junto do fonte.

CSS: usa _estilo.css ou estilo.css na pasta do fonte se existir; senão, o
estilo.css empacotado nesta skill (assets/).

Tema: --tema, <meta name="tema"> do fonte, AI_DIAGRAMS_TEMA ou ai-diagrams, nessa
ordem (scripts/tema.py). O :root de tokens do CSS vira o do tema e o link do Google
Fonts vira o das famílias do tema; a geometria do fonte não muda.

Ícones: pacote pip `diagrams` (mingrammer), que instala os PNGs oficiais da
AWS em <site-packages>/resources/aws. Detectado automaticamente; override
com a variável de ambiente POSTER_ICONBASE.

Chrome: detectado nos caminhos usuais de macOS e Linux; override com a
variável de ambiente POSTER_CHROME.
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
    sys.exit('Ícones AWS não encontrados. Instale com pip3 install diagrams, '
             'ou aponte POSTER_ICONBASE para uma pasta resources/aws.')


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
    sys.exit('Chrome não encontrado. Instale o Google Chrome ou aponte POSTER_CHROME.')


def find_css(src_dir):
    for name in ('_estilo.css', 'estilo.css'):
        p = os.path.join(src_dir, name)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'estilo.css')


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tema
    flag_tema, sys.argv[1:] = tema.tirar_flag(sys.argv[1:])
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_dir = None
    if '--out' in sys.argv:
        out_dir = sys.argv[sys.argv.index('--out') + 1]
        args = [a for a in args if a != out_dir]
    if not args:
        sys.exit(__doc__)
    fonte = os.path.abspath(args[0])
    H = int(args[1]) if len(args) > 1 else None
    src_dir = os.path.dirname(fonte)
    if out_dir is None:
        out_dir = os.path.dirname(src_dir) if os.path.basename(src_dir) == '_src' else src_dir

    src = open(fonte).read()
    tm = tema.tema(flag_tema, src, src_dir)
    iconbase = find_iconbase()
    chrome = find_chrome()
    if '/*ESTILO*/' not in src:
        sys.exit('SEM-ESTILO: o fonte não tem o marcador /*ESTILO*/ dentro do <style>; sem ele o PNG sai sem o design system. Copie o <head> do modelo do tipo.')
    src = tema.aplicar(src, open(find_css(src_dir)).read(), tm)

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
        sys.exit('Ícone(s) inexistente(s) em %s: %s. Liste os disponíveis com ls %s/<categoria>/' %
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
        print('LINT REPROVOU %s:' % fonte)
        for kind, x, y, _s in _issues:
            print('  %s em (%g,%g)' % (kind, x, y))
        sys.exit('Corrija o fonte e rode de novo. (checks: ver docstring de poster_lint.py)')

    # Altura da captura: a medida no Chrome quando não vem no comando; altura menor que
    # o conteúdo corta o rodapé, e isso reprova.
    precisa = _pl.ULTIMA_MEDICAO.get('altura')
    if H is None:
        H = precisa or 1500
    elif precisa and H < precisa:
        sys.exit('CORTADO: a página tem %dpx de altura e a captura pediu %dpx. Rode sem a altura '
                 '(a medida é automática) ou com %d.' % (precisa, H, precisa))

    # Largura da captura: 1760px, ou a que o fonte declara em <meta name="largura">
    # quando o desenho precisa de mais espaço para ficar legível (o DER declara).
    m = re.search(r'<meta name="largura" content="(\d+)"', src)
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
        sys.exit('Chrome não gerou o PNG. ' + r.stderr.decode()[-800:])
    print(f'OK {html_out}')
    print(f'OK {png}')


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        sys.exit('O Chrome não respondeu a tempo. Confira a rede (as fontes vêm do Google Fonts), '
                 'feche outros Chrome headless presos e confira POSTER_CHROME.')
