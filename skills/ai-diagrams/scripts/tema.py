#!/usr/bin/env python3
"""Tema dos diagramas: o único módulo que lê o json do tema e gera o CSS dele.

Escolha do tema, a mesma em todo comando da skill (build.py, conceitual.py, poster_lint.py,
gerar_raias.py, gerar_sequencia.py, gerar_estados.py, bpmn/gerar_bpmn.py, der/der-montar.mjs,
der/der-visao-geral.mjs), nesta ordem:
  1. flag --tema <nome ou caminho.json>;
  2. <meta name="tema" content="..."> no fonte HTML (os geradores gravam quando o tema não é o padrão);
  3. variável de ambiente AI_DIAGRAMS_TEMA;
  4. padrão: ai-diagrams.
Nome resolve para temas/<nome>.json desta skill. Caminho (termina em .json ou tem barra) aceita
um json em qualquer pasta; na meta, o caminho é relativo à pasta do fonte.

O tema gera o :root com todos os tokens de cor e de fonte e o link do Google Fonts das famílias.
O :root do CSS base (assets/estilo.css, assets/estilo-conceitual.css) é só o fallback do tema
padrão; o gate troca esse bloco pelo do tema escolhido. conferir_tema.py confere o fallback.

Reprova (exit 1, antes de abrir o Chrome):
  TEMA-INEXISTENTE  nome sem temas/<nome>.json, ou caminho que não existe.
  TEMA-INVALIDO     json que não abre, ou cor fora do formato #RRGGBB.
  TEMA-INCOMPLETO   chave obrigatória ausente: "TEMA-INCOMPLETO: falta cores.acento".

Uso direto:
  python3 tema.py [--tema X] --css          imprime o :root do tema
  python3 tema.py [--tema X] --link         imprime o link do Google Fonts
  python3 tema.py [--tema X] --gerador HTML imprime json {link, meta} para um gerador que grava HTML
"""
import json, os, re, sys
from urllib.parse import quote_plus

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(SK, 'temas')
PADRAO = 'ai-diagrams'
ENV = 'AI_DIAGRAMS_TEMA'

OBRIGATORIAS = {
    'cores': ['tinta', 'apoio', 'cinza', 'zona', 'papel', 'acento', 'risco', 'risco_fundo'],
    'cores_derivadas': ['acento_forte', 'cinza_claro', 'c4_pessoa_tipo', 'c4_pessoa_desc', 'c4_externo', 'c4_limite'],
    'paleta_der': ['der_borda', 'der_legenda', 'der_linha_par', 'der_chave', 'der_dominio', 'der_fora', 'der_copia',
                   'der_forte', 'der_dependente', 'der_associativa', 'der_controle', 'der_fato', 'der_versionada',
                   'der_projecao', 'der_trilha', 'der_dominio_fundo', 'der_configuracao', 'der_referencia',
                   'der_visao', 'der_calor'],
    'fontes': ['texto', 'mono'],
}
# a mesma cor em canais, para rgba(): color-mix arredonda diferente e muda pixel
CANAIS = ['apoio', 'papel', 'risco']
PESOS = 'wght@400;500;600;700'
_HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
_LINK = re.compile(r'<link\b[^>]*href="https://fonts\.googleapis\.com/css2\?[^"]*"[^>]*>')
_META = re.compile(r'<meta name="tema" content="([^"]*)">')


def falha(msg):
    sys.exit(msg)


def tirar_flag(argv):
    """Tira --tema X (ou --tema=X) do argv. Devolve (valor ou None, argv sem a flag)."""
    out, valor, i = [], None, 0
    while i < len(argv):
        a = argv[i]
        if a == '--tema':
            if i + 1 >= len(argv):
                falha('TEMA-INEXISTENTE: --tema sem valor; passe um nome (temas/<nome>.json) ou um caminho .json')
            valor, i = argv[i + 1], i + 2
            continue
        if a.startswith('--tema='):
            valor = a.split('=', 1)[1]
        else:
            out.append(a)
        i += 1
    return valor, out


def _e_caminho(v):
    return v.endswith('.json') or os.sep in v or '/' in v


def caminho(valor, base=None):
    """Nome ou caminho para o arquivo json. base: pasta para caminho relativo (padrão: cwd)."""
    if _e_caminho(valor):
        p = os.path.abspath(os.path.join(base, valor) if base and not os.path.isabs(valor) else valor)
        if not os.path.isfile(p):
            falha('TEMA-INEXISTENTE: %s não existe' % p)
        return p
    p = os.path.join(PASTA, valor + '.json')
    if not os.path.isfile(p):
        disp = ', '.join(sorted(f[:-5] for f in os.listdir(PASTA) if f.endswith('.json')))
        falha('TEMA-INEXISTENTE: não há temas/%s.json; temas da skill: %s; ou passe um caminho .json' % (valor, disp))
    return p


def escolher(flag=None, fonte_html=None, fonte_dir=None):
    """Aplica a precedência. Devolve (caminho do json, origem, valor como foi dado)."""
    if flag:
        return caminho(flag), 'flag', flag
    if fonte_html:
        m = _META.search(fonte_html)
        if m:
            return caminho(m.group(1), fonte_dir), 'meta', m.group(1)
    env = os.environ.get(ENV)
    if env:
        return caminho(env), 'env', env
    return caminho(PADRAO), 'padrao', PADRAO


def carregar(p):
    try:
        t = json.load(open(p))
    except (OSError, ValueError) as e:
        falha('TEMA-INVALIDO: %s não abre como json (%s)' % (p, e))
    for grupo, chaves in OBRIGATORIAS.items():
        g = t.get(grupo)
        if not isinstance(g, dict):
            falha('TEMA-INCOMPLETO: falta %s (%s)' % (grupo, p))
        for k in chaves:
            v = g.get(k)
            if v is None or v == '':
                falha('TEMA-INCOMPLETO: falta %s.%s (%s)' % (grupo, k, p))
            if grupo != 'fontes' and not _HEX.match(str(v)):
                falha('TEMA-INVALIDO: %s.%s é "%s"; use #RRGGBB (%s)' % (grupo, k, v, p))
    t['_caminho'] = p
    return t


def tema(flag=None, fonte_html=None, fonte_dir=None):
    """Atalho para os comandos: escolhe e carrega."""
    p, origem, valor = escolher(flag, fonte_html, fonte_dir)
    t = carregar(p)
    t['_origem'], t['_valor'] = origem, valor
    return t


def _rgb(h):
    return ','.join(str(int(h[i:i + 2], 16)) for i in (1, 3, 5))


def pilha_texto(t):
    return "'%s',Arial,sans-serif" % t['fontes']['texto']


def pilha_mono(t):
    return "'%s',monospace" % t['fontes']['mono']


def tokens(t):
    """Lista ordenada (nome do token sem --, valor) que o :root declara."""
    out = []
    for grupo in ('cores', 'cores_derivadas', 'paleta_der'):
        for k in OBRIGATORIAS[grupo]:
            if k == 'der_calor':
                continue
            out.append((k.replace('_', '-'), t[grupo][k].upper()))
    for k in CANAIS:
        out.append((k + '-rgb', _rgb(t['cores'][k])))
    out.append(('der-calor-rgb', _rgb(t['paleta_der']['der_calor'])))
    out.append(('fonte-texto', pilha_texto(t)))
    out.append(('fonte-mono', pilha_mono(t)))
    return out


def css_root(t):
    linhas = ['--%s:%s;' % kv for kv in tokens(t)]
    return ':root{\n  /* tema %s: gerado por scripts/tema.py a partir de %s */\n  %s\n}' % (
        t.get('nome', ''), os.path.basename(t['_caminho']), '\n  '.join(linhas))


def link_fontes(t):
    fam = '&'.join('family=%s:%s' % (quote_plus(t['fontes'][k]), PESOS) for k in ('texto', 'mono'))
    return '<link href="https://fonts.googleapis.com/css2?%s&display=swap" rel="stylesheet">' % fam


def bloco_tokens(css):
    """(início, fim) do :root de tokens no CSS base (o primeiro :root que declara --tinta), ou None."""
    for m in re.finditer(r':root\s*\{', css):
        fim = css.find('}', m.end())
        if fim > 0 and '--tinta' in css[m.end():fim]:
            return m.start(), fim + 1
    return None


def css_com_tema(css_base, t):
    """O CSS base com o :root de tokens trocado pelo do tema (ou o do tema na frente, se o CSS não tem)."""
    b = bloco_tokens(css_base)
    if b is None:
        return css_root(t) + '\n' + css_base
    return css_base[:b[0]] + css_root(t) + css_base[b[1]:]


def com_link(html, t):
    """Troca o link do Google Fonts do fonte pelo das famílias do tema."""
    novo = link_fontes(t)
    if _LINK.search(html):
        return _LINK.sub(lambda m: novo, html, count=1)
    pre = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n')
    return html.replace('</head>', pre + novo + '\n</head>', 1) if '</head>' in html else html


def aplicar(html, css_base, t):
    """Fonte com /*ESTILO*/ -> HTML com o CSS base, o :root do tema e o link das fontes."""
    return com_link(html.replace('/*ESTILO*/', css_com_tema(css_base, t)), t)


def para_gerador(t, saida_html):
    """Link das fontes e meta do tema para um gerador gravar no fonte HTML.
    A meta só entra quando o tema foi escolhido (flag ou env); no padrão o fonte fica como sempre foi."""
    meta = ''
    if t['_origem'] in ('flag', 'env'):
        v = t['_valor']
        if _e_caminho(v):  # relativo ao fonte quando fica perto dele (projeto portável); senão, absoluto
            rel = os.path.relpath(t['_caminho'], os.path.dirname(os.path.abspath(saida_html)))
            v = rel if rel.split(os.sep).count('..') <= 3 else t['_caminho']
        meta = '<meta name="tema" content="%s">' % v
    return {'link': link_fontes(t), 'meta': meta}


def main():
    flag, argv = tirar_flag(sys.argv[1:])
    t = tema(flag)
    if '--css' in argv:
        print(css_root(t))
    elif '--link' in argv:
        print(link_fontes(t))
    elif '--gerador' in argv:
        print(json.dumps(para_gerador(t, argv[argv.index('--gerador') + 1]), ensure_ascii=False))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
