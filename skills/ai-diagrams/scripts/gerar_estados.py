#!/usr/bin/env python3
"""Gera o fonte HTML de uma máquina de estados a partir de um JSON.

Uso: python3 gerar_estados.py <spec.json> [saida.html]

Antes do desenho, confere o grafo e para com mensagem se faltar estado inicial,
se uma transição citar estado não declarado ou não tiver evento, se um estado
não for alcançável a partir do inicial, se um estado não final não tiver saída,
ou se um estado final tiver saída. Depois o elkjs (estados/elk-layout.cjs)
decide posição e roteamento ortogonal; o desenho é todo desta skill. Sem saída
explícita, grava <spec>.html ao lado do JSON. O build e o lint são do
conceitual.py.
"""
import json, os, sys, html, math, re, subprocess

EST_W = 204                  # largura do estado
EST_H, EST_H_SUB = 66, 90    # altura sem e com subtítulo, nome numa linha
CHAR_NOME = 9.4              # 17px IBM Plex Sans 600
CHAR = 8.0                   # 15px IBM Plex Sans, rótulo da transição
LINHA = 20
ROT_MAX = 220                # largura máxima do rótulo antes de quebrar
INI = 22                     # diâmetro do ponto inicial
LACO = 34                    # quanto o laço sai da caixa
LARGURA_MAX = 1320
AQUI = os.path.dirname(os.path.abspath(__file__))
ELK = os.path.join(AQUI, '..', 'estados', 'elk-layout.cjs')


def esc(t):
    return html.escape(str(t), quote=False)


def code_html(t):
    """`trecho` vira <code>: nome de evento, campo ou mensagem."""
    partes = re.split(r'`([^`]+)`', t)
    return ''.join(esc(p) if i % 2 == 0 else '<code>%s</code>' % esc(p) for i, p in enumerate(partes))


def larg(t, char=CHAR):
    return len(t.replace('`', '')) * char


def erro(codigo, msg):
    sys.exit('ESTADOS REPROVOU %s: %s' % (codigo, msg))


def conferir(S):
    ids = [e['id'] for e in S['estados']]
    final = {e['id'] for e in S['estados'] if e.get('final')}
    if not S.get('inicial'):
        erro('SEM-INICIAL', 'declare "inicial" com o id do primeiro estado')
    if S['inicial'] not in ids:
        erro('SEM-INICIAL', 'o inicial "%s" não está em estados' % S['inicial'])
    saidas = {i: [] for i in ids}
    for t in S['transicoes']:
        for k in ('de', 'para'):
            if t.get(k) not in ids:
                erro('DESCONHECIDO', 'transição cita "%s", que não está em estados' % t.get(k))
        if not str(t.get('evento', '')).strip():
            erro('SEM-EVENTO', 'transição %s -> %s sem evento' % (t['de'], t['para']))
        if t['de'] in final:
            erro('SAI-DO-FINAL', 'o estado final "%s" tem saída para "%s"' % (t['de'], t['para']))
        saidas[t['de']].append(t['para'])
    vistos, fila = {S['inicial']}, [S['inicial']]
    while fila:
        for p in saidas[fila.pop()]:
            if p not in vistos:
                vistos.add(p)
                fila.append(p)
    for i in ids:
        if i not in vistos:
            erro('INALCANCAVEL', 'nenhum caminho do inicial chega a "%s"' % i)
        if i not in final and not [p for p in saidas[i] if p != i]:
            erro('SEM-SAIDA', '"%s" não é final e não sai para outro estado' % i)


def quebra(p):
    """Quebra um trecho em linhas de até ROT_MAX; trecho entre crases não se parte."""
    linhas, atual = [], ''
    for tok in re.findall(r'`[^`]*`\S*|\S+', p):
        teste = (atual + ' ' + tok).strip()
        if atual and larg(teste) > ROT_MAX:
            linhas.append(atual)
            atual = tok
        else:
            atual = teste
    return linhas + [atual]


def rotulo(t):
    """Linhas do rótulo, já quebradas: evento, [guarda], / ação. A largura é a da linha mais longa."""
    partes = [('ev', t['evento'])]
    if t.get('guarda'):
        partes.append(('gd', '[%s]' % t['guarda']))
    if t.get('acao'):
        partes.append(('ac', '/ %s' % t['acao']))
    linhas = [(cls, l) for cls, p in partes for l in quebra(p)]
    w = max(40, max(larg(l) for _, l in linhas))
    return linhas, int(w) + 8, len(linhas) * LINHA


def rotulo_html(linhas, t):
    return '<br>'.join('<span class="%s">%s</span>' % (cls, code_html(l)) for cls, l in linhas)


def layout(S, direcao):
    filhos = [{'id': '__ini', 'width': INI, 'height': INI}]
    for e in S['estados']:
        e['_h'] = EST_H_SUB if e.get('sub') else EST_H
        if larg(e['nome'], CHAR_NOME) > EST_W - 34:
            sys.exit('nome de estado longo demais para uma linha: "%s"' % e['nome'])
        filhos.append({'id': e['id'], 'width': EST_W, 'height': e['_h']})
    arestas = [{'id': 't_ini', 'sources': ['__ini'], 'targets': [S['inicial']]}]
    for k, t in enumerate(S['transicoes']):
        partes, w, h = rotulo(t)
        t['_partes'], t['_w'], t['_h'] = partes, w, h
        arestas.append({'id': 't%d' % k, 'sources': [t['de']], 'targets': [t['para']],
                        'labels': [{'id': 'l%d' % k, 'width': w, 'height': h, 'text': 'x'}]})
    g = {'id': 'raiz', 'children': filhos, 'edges': arestas, 'layoutOptions': {
        'elk.algorithm': 'layered',
        'elk.direction': direcao,
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
        'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
        'elk.spacing.nodeNode': '56',
        'elk.layered.spacing.nodeNodeBetweenLayers': '72',
        'elk.spacing.edgeEdge': '22',
        'elk.spacing.edgeNode': '24',
        'elk.layered.spacing.edgeEdgeBetweenLayers': '22',
        'elk.layered.spacing.edgeNodeBetweenLayers': '24',
        'elk.spacing.edgeLabel': '6',
        'elk.edgeLabels.placement': 'CENTER',
        'elk.padding': '[top=20,left=20,bottom=20,right=20]',
    }}
    r = subprocess.run(['node', ELK], input=json.dumps(g), capture_output=True, text=True)
    if r.returncode:
        sys.exit('elkjs falhou: ' + r.stderr.strip())
    return json.loads(r.stdout)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    S = json.load(open(spec_path))
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(spec_path)[0] + '.html'
    conferir(S)

    g = layout(S, S.get('direcao', 'RIGHT'))
    if g['width'] > LARGURA_MAX and 'direcao' not in S:
        g2 = layout(S, 'DOWN')
        if g2['width'] < g['width']:
            g = g2
    canvas_w, canvas_h = int(math.ceil(g['width'])), int(math.ceil(g['height']))
    pos = {c['id']: c for c in g['children']}
    ests = {e['id']: e for e in S['estados']}
    R = lambda v: int(round(v))

    out = []
    c = pos['__ini']
    out.append(f'      <div class="painel ini" style="left:{R(c["x"])}px;top:{R(c["y"])}px;width:{INI}px;height:{INI}px"></div>')
    for e in S['estados']:
        c = pos[e['id']]
        cls = 'painel estado' + (' final' if e.get('final') else '') + (' ' + e['estilo'] if e.get('estilo') else '')
        tag = 'final' if e.get('final') else 'estado'
        sub = f'<div class="ps">{code_html(e["sub"])}</div>' if e.get('sub') else ''
        out.append(f'      <div class="{cls}" style="left:{R(c["x"])}px;top:{R(c["y"])}px;width:{EST_W}px;height:{e["_h"]}px">'
                   f'<div class="ptag">{tag}</div><div class="pt">{esc(e["nome"])}</div>{sub}</div>')

    svg = []
    tr = {'t%d' % k: t for k, t in enumerate(S['transicoes'])}
    for a in g['edges']:
        t = tr.get(a['id'])
        if t and t['de'] == t['para']:
            # laço: o do ELK sai 10 px da caixa; redesenhado do mesmo lado, mais aberto
            c = pos[t['de']]
            s = a['sections'][0]
            esq = s['startPoint']['x'] < c['x'] + EST_W / 2
            borda = R(c['x']) if esq else R(c['x']) + EST_W
            fora = borda - LACO if esq else borda + LACO
            y1, y2 = R(c['y']) + 18, R(c['y']) + ests[t['de']]['_h'] - 18
            svg.append(f'        <path d="M{borda},{y1} L{fora},{y1} L{fora},{y2} L{borda},{y2}" '
                       'stroke-width="1.6" fill="none" marker-end="url(#s)" style="stroke:var(--apoio)"/>')
            lx = fora - 10 - t['_w'] if esq else fora + 10
            ly = (y1 + y2) // 2 - t['_h'] // 2
            cls = 'mlabel tlabel dir' if esq else 'mlabel tlabel'
            out.append(f'      <div class="{cls}" style="left:{lx}px;top:{ly}px;width:{t["_w"]}px">'
                       f'{rotulo_html(t["_partes"], t)}</div>')
            continue
        for s in a.get('sections', []):
            pts = [s['startPoint']] + s.get('bendPoints', []) + [s['endPoint']]
            d = 'M%d,%d ' % (R(pts[0]['x']), R(pts[0]['y'])) + ' '.join('L%d,%d' % (R(p['x']), R(p['y'])) for p in pts[1:])
            svg.append(f'        <path d="{d}" stroke-width="1.6" fill="none" marker-end="url(#s)" style="stroke:var(--apoio)"/>')
        if t:
            lb = a['labels'][0]
            out.append(f'      <div class="mlabel tlabel" style="left:{R(lb["x"])}px;top:{R(lb["y"])}px;width:{t["_w"]}px">'
                       f'{rotulo_html(t["_partes"], t)}</div>')

    svg_html = (f'      <svg class="edges" viewBox="0 0 {canvas_w} {canvas_h}">\n'
                '        <defs><marker id="s" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">\n'
                '          <path d="M0,0 L9,4.5 L0,9 z" style="fill:var(--apoio)"/></marker></defs>\n'
                + '\n'.join(svg) + '\n      </svg>')

    secoes = []
    com_desc = [e for e in S['estados'] if e.get('desc')]
    if com_desc:
        secoes.append('  <div class="sec">Estados</div>\n  <div class="passos-seq estados-leg">')
        for e in com_desc:
            secoes.append(f'    <div class="ps-item"><div class="pd"><b>{esc(e["nome"])}</b> {code_html(e["desc"])}</div></div>')
        secoes.append('  </div>')
    secoes.append('  <div class="sec">Notação</div>\n  <div class="notacao wrap">'
                  '<div class="nt"><div class="ini-mini"></div>estado inicial</div>'
                  '<div class="nt"><div class="est-mini"></div>estado</div>'
                  '<div class="nt"><div class="est-mini final"></div>estado final: não tem saída</div>'
                  '<div class="nt"><span class="nt-rot"><span class="ev">evento</span> <span class="gd">[guarda]</span> '
                  '<span class="ac">/ ação</span></span>a transição acontece no evento, se a guarda vale, e executa a ação</div></div>')

    faixa = ''
    if S.get('faixa'):
        f2 = f'\n    <div class="f2">{esc(S["faixa"]["f2"])}</div>' if S['faixa'].get('f2') else ''
        faixa = f'  <div class="faixa">\n    <div class="f1">{esc(S["faixa"]["f1"])}</div>{f2}\n  </div>'

    pagina = canvas_w + 80
    largura_meta = f'<meta name="largura" content="{pagina}">\n' if pagina > 1400 else ''
    largura_css = f'\nbody{{width:{pagina}px}}' if pagina > 1400 else ''
    he, hd = S['cabecalho']
    fe, fd = S['rodape']
    doc = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{esc(S['titulo_pagina'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
{largura_meta}<style>/*ESTILO*/{largura_css}</style></head><body>
<div class="page">

  <div class="hdr"><span>{esc(he)}</span><span>{esc(hd)}</span></div>

  <div class="kicker"><span class="sq">■</span> {esc(S.get('kicker', 'Máquina de estados'))}</div>
  <h1>{esc(S['h1'])}</h1>
  <div class="sub">{code_html(S['sub'])}</div>

  <div class="canvas" style="width:{canvas_w}px;height:{canvas_h}px">
{chr(10).join(out)}
{svg_html}
  </div>

{chr(10).join(secoes)}
{faixa}

  <div class="foot"><span>{esc(fe)}</span><span>{esc(fd)}</span></div>

</div>
</body></html>
'''
    open(saida, 'w').write(doc)
    print(saida)
    print('canvas %dx%d · %d estados · %d transições' % (canvas_w, canvas_h, len(S['estados']), len(S['transicoes'])))


if __name__ == '__main__':
    main()
