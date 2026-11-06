#!/usr/bin/env python3
"""Gera o fonte HTML de um diagrama de sequência a partir de um JSON.

Uso: python3 gerar_sequencia.py <spec.json> [saida.html]

Coordenadas calculadas, nunca escritas à mão. Participante é coluna, mensagem é
linha. O rótulo de cada mensagem fica no vão vizinho da origem, do lado para onde
a seta anda, e o vão alarga até caber o rótulo: texto nunca cruza linha de vida.
Chamada síncrona abre barra de ativação no destino; a resposta do destino para a
origem fecha a barra. Fragmentos alt, loop e opt viram frame com divisória de
ramo. Sem saída explícita, grava <spec>.html ao lado do JSON. O build e o lint
são do conceitual.py.
"""
import json, os, sys, html, math, re

CAB_W, CAB_H = 168, 104      # cabeça do participante
VAO_MIN = CAB_W + 28         # distância mínima entre linhas de vida
VAO_MAX = 228                # acima disso, o rótulo quebra em linhas
ATIV = 6                     # meia largura da barra de ativação
BADGE = 20
CHAR = 8.0                   # largura média de caractere do rótulo (15px IBM Plex Sans)
LINHA = 20                   # altura de linha do rótulo
FCHAR = 8.2                  # largura de caractere da guarda (11px mono, caixa alta, .14em)
AUTO_W = 46                  # largura do laço da mensagem para si mesmo
AUTO_H = 26
TIPOS = {'ator': 'ator', 'servico': 'serviço', 'banco': 'banco', 'fila': 'fila',
         'externo': 'externo', 'sistema': 'sistema'}


def esc(t):
    return html.escape(str(t), quote=False)


def rotulo_html(t):
    """`trecho` vira <code>: nome de endpoint, evento ou campo."""
    partes = re.split(r'`([^`]+)`', t)
    return ''.join(esc(p) if i % 2 == 0 else '<code>%s</code>' % esc(p) for i, p in enumerate(partes))


def largura_texto(t):
    return len(t.replace('`', '')) * CHAR


def achatar(itens, nivel=0):
    """Lista linear de eventos: mensagens, notas e marcas de frame."""
    out = []
    for it in itens:
        if 'fragmento' in it:
            out.append({'abre': it['fragmento'], 'guarda': it['ramos'][0].get('guarda', ''), 'nivel': nivel})
            for k, ramo in enumerate(it['ramos']):
                if k:
                    out.append({'ramo': ramo.get('guarda', ''), 'nivel': nivel})
                out += achatar(ramo['mensagens'], nivel + 1)
            out.append({'fecha': True, 'nivel': nivel})
        else:
            out.append(it)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    S = json.load(open(spec_path))
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(spec_path)[0] + '.html'

    parts = S['participantes']
    idx = {p['id']: i for i, p in enumerate(parts)}
    n = len(parts)
    ev = achatar(S['mensagens'])
    for e in ev:
        for k in ('de', 'para'):
            if k in e and e[k] not in idx:
                sys.exit('participante "%s" não declarado em participantes' % e[k])

    # 1. vãos: cada rótulo pede espaço no vão vizinho da origem
    vao = [VAO_MIN] * max(n - 1, 0)
    margem_dir = 40
    passo = 0
    for e in ev:
        if 'de' not in e:
            continue
        a, b = idx[e['de']], idx[e['para']]
        if e.get('passo'):
            passo += 1
            e['n'] = passo
        extra = BADGE + 14 if e.get('n') else 12
        w = largura_texto(e['texto'])
        if a == b:
            pedido = AUTO_W + 14 + extra + w + 24
        else:
            pedido = ATIV + extra + w + ATIV + 24
        lim = VAO_MAX if a != b else VAO_MAX + AUTO_W
        if pedido > lim:
            w_max = lim - (pedido - w)
            e['linhas'] = math.ceil(w / w_max)
            e['w'] = w_max
            pedido = lim
        else:
            e['linhas'] = 1
            e['w'] = w + 6
        if a == b:
            if a < n - 1:
                vao[a] = max(vao[a], pedido)
            else:
                margem_dir = max(margem_dir, pedido)
        elif b > a:
            vao[a] = max(vao[a], pedido)
        else:
            vao[a - 1] = max(vao[a - 1], pedido)

    xs = [CAB_W // 2]
    for v in vao:
        xs.append(xs[-1] + int(v))
    canvas_w = int(xs[-1] + max(CAB_W // 2, margem_dir))

    # 2. linhas: y de cada evento
    y = CAB_H + 34
    abertos = []                 # pilha de frames: [evento de abertura, y0, ramos]
    frames = []
    for e in ev:
        if 'abre' in e:
            y += 14
            e['y'] = y
            abertos.append({'e': e, 'y0': y, 'ramos': [], 'cols': set()})
            y += 34
        elif 'ramo' in e:
            y += 6
            e['y'] = y
            abertos[-1]['ramos'].append((y, e['ramo']))
            y += 34
        elif 'fecha' in e:
            f = abertos.pop()
            f['y1'] = y + 4
            frames.append(f)
            if abertos:
                abertos[-1]['cols'] |= f['cols']
            y += 18
        elif 'nota' in e:
            linhas = math.ceil(largura_texto(e['nota']) / (CAB_W - 28))
            e['y'] = y
            e['h'] = 22 + linhas * 21
            y += e['h'] + 18
            for f in abertos:
                f['cols'].add(idx[e['sobre']])
        else:
            y += e['linhas'] * LINHA + 10
            e['y'] = y
            y += 16 + (AUTO_H if e['de'] == e['para'] else 0)
            for f in abertos:
                f['cols'] |= {idx[e['de']], idx[e['para']]}
                if e['de'] == e['para']:
                    f['auto'] = max(f.get('auto', 0), AUTO_W + 14 + (BADGE + 10 if e.get('n') else 0) + e['w'] + 10)
    canvas_h = y + 24

    # 2b. guarda do frame e nome de ramo cabem antes da próxima linha de vida
    for f in frames:
        c0 = min(f['cols'])
        tit = f['e']['abre'] + (' · ' + f['e']['guarda'] if f['e']['guarda'] else '')
        f['lab_w'] = max(len(s) for s in [tit] + [r for _, r in f['ramos']]) * FCHAR + 16
        pedido = ATIV + 10 + f['lab_w'] + 12 + ATIV
        if c0 < n - 1:
            vao[c0] = max(vao[c0], pedido)
        else:
            margem_dir = max(margem_dir, pedido)
    xs = [CAB_W // 2]
    for v in vao:
        xs.append(xs[-1] + int(v))
    canvas_w = int(xs[-1] + max(CAB_W // 2, margem_dir))

    # 3. ativações: síncrona abre no destino, resposta do destino fecha.
    # Cada ramo de um fragmento começa com as barras abertas na entrada dele.
    ativ = []
    pend = {}
    msgs = [e for e in ev if 'de' in e]
    entrada = []
    for e in ev:
        if 'abre' in e:
            entrada.append({k: len(v) for k, v in pend.items()})
            continue
        if 'ramo' in e:
            for pid, n_ab in entrada[-1].items():
                segs = pend.setdefault(pid, [])
                while len(segs) < n_ab:
                    segs.append([e['y'] - 6, None])
            continue
        if 'fecha' in e:
            entrada.pop()
            continue
        if 'de' not in e:
            continue
        if e.get('tipo', 'sincrona') == 'sincrona' and e['de'] != e['para']:
            pend.setdefault(e['para'], []).append([e['y'] - 4, None])
        if e.get('tipo') == 'resposta' and pend.get(e['de']):
            seg = pend[e['de']].pop()
            seg[1] = e['y'] + 4
            ativ.append((idx[e['de']], seg[0], seg[1]))
    for pid, segs in pend.items():
        ult = max(m['y'] for m in msgs if pid in (m['de'], m['para']))
        for s in segs:
            if ult + 4 > s[0] + 8:       # barra reaberta num ramo sem mensagem depois dela some
                ativ.append((idx[pid], s[0], ult + 4))

    def ativo(col, yy):
        return any(c == col and a <= yy <= b for (c, a, b) in ativ)

    out = []
    for i, p in enumerate(parts):
        x0 = xs[i] - CAB_W // 2
        tipo = p.get('tipo', 'servico')
        cls = 'painel cab' + (' externo' if tipo == 'externo' else '')
        ico = '<img src="%s" alt="">' % esc(p['icone']) if p.get('icone') else ''
        sub = '<div class="nsub">%s</div>' % esc(p['sub']) if p.get('sub') else ''
        out.append(f'      <div class="{cls}" style="left:{x0}px;top:0;width:{CAB_W}px;height:{CAB_H}px">\n'
                   f'        <div class="ptag">{esc(TIPOS.get(tipo, tipo))}</div>\n'
                   f'        <div class="cabrow">{ico}<div><div class="pt">{esc(p["nome"])}</div>{sub}</div></div>\n'
                   f'      </div>')
        out.append(f'      <div class="vida" style="left:{xs[i] - ATIV}px;top:{CAB_H}px;height:{canvas_h - CAB_H - 8}px"></div>')

    for f in frames:
        c0, c1 = min(f['cols']), max(f['cols'])
        nivel = f['e']['nivel']
        x0 = xs[c0] - 44 + 0 * nivel
        x1 = max(xs[c1] + 44 + f.get('auto', 0), int(xs[c0] + ATIV + 10 + f['lab_w'] + 10))
        # frame interno recua para dentro do externo
        for g in frames:
            if g is not f and g['y0'] < f['y0'] and g['y1'] > f['y1'] and min(g['cols']) == c0:
                x0 = max(x0, xs[c0] - 44 + 14 * (nivel - g['e']['nivel']))
            if g is not f and g['y0'] < f['y0'] and g['y1'] > f['y1'] and max(g['cols']) == c1:
                x1 = min(x1, xs[c1] + 44 + g.get('auto', 0) - 14 * (nivel - g['e']['nivel']))
        guarda = f['e']['guarda']
        tit = f['e']['abre'] + (' · ' + guarda if guarda else '')
        lx = xs[c0] + ATIV + 10 - x0
        ramos = ''.join(f'\n        <div class="ramo" style="top:{ry - f["y0"]}px"><span class="rlabel" style="left:{lx}px">{esc(rg)}</span></div>'
                        for ry, rg in f['ramos'])
        out.append(f'      <div class="frame" style="left:{x0}px;top:{f["y0"]}px;width:{x1 - x0}px;height:{f["y1"] - f["y0"]}px">\n'
                   f'        <div class="flabel seq" style="left:{lx}px">{esc(tit)}</div>{ramos}\n      </div>')

    for (c, a, b) in ativ:
        out.append(f'      <div class="ativ" style="left:{xs[c] - ATIV}px;top:{a}px;height:{b - a}px"></div>')

    svg = []
    for e in ev:
        if 'nota' in e:
            c = idx[e['sobre']]
            out.append(f'      <div class="painel nota-seq" style="left:{xs[c] - CAB_W // 2}px;top:{e["y"]}px;width:{CAB_W}px;height:{e["h"]}px">'
                       f'<div class="ps" style="margin-top:0">{esc(e["nota"])}</div></div>')
            continue
        if 'de' not in e:
            continue
        a, b, yy = idx[e['de']], idx[e['para']], e['y']
        tipo = e.get('tipo', 'sincrona')
        dash = ' stroke-dasharray="6 4"' if tipo == 'resposta' else ''
        mk = 's' if tipo == 'sincrona' else 'a'
        lh = e['linhas'] * LINHA
        if a == b:
            xa = xs[a] + (ATIV if ativo(a, yy) else 0)
            svg.append(f'        <path d="M{xa},{yy} H{xs[a] + AUTO_W} V{yy + AUTO_H} H{xa}" stroke="#374151" '
                       f'stroke-width="1.6" fill="none"{dash} marker-end="url(#{mk})"/>')
            lx = xs[a] + AUTO_W + 14
            if e.get('n'):
                out.append(f'      <div class="badge" style="left:{lx}px;top:{yy + AUTO_H // 2 - BADGE // 2}px">{e["n"]}</div>')
                lx += BADGE + 10
            out.append(f'      <div class="mlabel" style="left:{lx}px;top:{yy + AUTO_H // 2 - lh // 2}px;width:{int(e["w"])}px">{rotulo_html(e["texto"])}</div>')
            continue
        d = 1 if b > a else -1
        xa = xs[a] + d * (ATIV if ativo(a, yy) else 0)
        xb = xs[b] - d * (ATIV if ativo(b, yy) else 0)
        svg.append(f'        <path d="M{xa},{yy} H{xb}" stroke="#374151" stroke-width="1.6" fill="none"{dash} marker-end="url(#{mk})"/>')
        lx = xa + d * 10
        if e.get('n'):
            bx = lx if d > 0 else lx - BADGE
            out.append(f'      <div class="badge" style="left:{bx}px;top:{yy - BADGE // 2}px">{e["n"]}</div>')
            lx += d * (BADGE + 8)
        topo = yy - 8 - lh
        if e.get('n'):
            topo = yy - BADGE // 2 - 4 - lh
        if d > 0:
            out.append(f'      <div class="mlabel" style="left:{int(lx)}px;top:{topo}px;width:{int(e["w"])}px">{rotulo_html(e["texto"])}</div>')
        else:
            out.append(f'      <div class="mlabel dir" style="left:{int(lx - e["w"])}px;top:{topo}px;width:{int(e["w"])}px">{rotulo_html(e["texto"])}</div>')

    svg_html = (f'      <svg class="edges" viewBox="0 0 {canvas_w} {canvas_h}">\n'
                '        <defs><marker id="s" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">\n'
                '          <path d="M0,0 L9,4.5 L0,9 z" fill="#374151"/></marker>\n'
                '        <marker id="a" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto">\n'
                '          <path d="M1,1 L8.5,5 L1,9" fill="none" stroke="#374151" stroke-width="1.5"/></marker></defs>\n'
                + '\n'.join(svg) + '\n      </svg>')

    passos = [e for e in ev if e.get('n')]
    secoes = []
    if passos:
        secoes.append('  <div class="sec">Passos</div>\n  <div class="passos-seq">')
        for e in passos:
            secoes.append(f'    <div class="ps-item"><div class="badge">{e["n"]}</div><div class="pd">{rotulo_html(e["passo"])}</div></div>')
        secoes.append('  </div>')
    usados = {e.get('tipo', 'sincrona') for e in ev if 'de' in e}
    nt = [('sincrona', '', 'chamada síncrona'), ('assincrona', ' aberta', 'mensagem assíncrona'),
          ('resposta', ' trac aberta', 'resposta')]
    itens = ''.join(f'<div class="nt"><div class="lin{c}"></div>{t}</div>' for k, c, t in nt if k in usados)
    secoes.append(f'  <div class="sec">Notação</div>\n  <div class="notacao">{itens}'
                  '<div class="nt"><div class="ativ-mini"></div>barra de ativação: o participante está processando</div></div>')

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

  <div class="kicker"><span class="sq">■</span> {esc(S.get('kicker', 'Diagrama de sequência'))}</div>
  <h1>{esc(S['h1'])}</h1>
  <div class="sub">{esc(S['sub'])}</div>

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
    print('canvas %dx%d · %d participantes · %d mensagens · %d fragmentos'
          % (canvas_w, canvas_h, n, len(msgs), len(frames)))


if __name__ == '__main__':
    main()
