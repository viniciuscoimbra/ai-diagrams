#!/usr/bin/env python3
"""Gera o fonte HTML de um fluxo em raias (swimlane conceitual) a partir de um JSON.

Uso: python3 gerar_raias.py <spec.json> [saida.html]

Coordenadas calculadas, nunca escritas à mão: raia é linha (o ator), fase é
coluna (o momento). Cada elemento ocupa uma célula raia × fase; a sequência liga
células com setas ortogonais pelo corredor entre as colunas. Cada seta tem altura
de saída, altura de chegada e x de corredor próprios, e o corredor alarga com o
número de setas: duas setas nunca correm na mesma linha. Seta que atravessaria
um painel reprova com mensagem. Sem saída
explícita, grava <spec>.html ao lado do JSON. O build e o lint são do
conceitual.py. Formato do JSON em references/raias.md.
"""
import json, os, sys, html, itertools

LW, AX = 152, 170           # largura do rótulo da raia; x da primeira fase
PH = 124                    # altura do painel; largura do painel e dos corredores são calculadas
TOPO = 38                   # faixa dos títulos das fases
CHIP_H = 24


def esc(t):
    return html.escape(str(t), quote=False)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    S = json.load(open(spec_path))
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(spec_path)[0] + '.html'

    raias, fases, els = S['raias'], S['fases'], S['elementos']
    for e in els:
        assert 0 <= e['raia'] < len(raias) and 0 <= e['fase'] < len(fases), e
    celula = {(e['raia'], e['fase']): e for e in els}
    assert len(celula) == len(els), 'dois elementos na mesma célula raia × fase'

    # Plano das setas antes das coordenadas: o número de corredores define a largura entre as fases.
    seq = [tuple(s) for s in S['sequencia']]
    def livre_raia(l, f1, f2):
        return not any((l, f) in celula for f in range(f1, f2))
    def livre_coluna(f, l1, l2):
        return not any((l, f) in celula for l in range(min(l1, l2) + 1, max(l1, l2)))
    plano = []
    for la, fa, lb, fb in seq:
        if (la, fa) not in celula or (lb, fb) not in celula:
            sys.exit('sequência liga célula vazia: %s' % [la, fa, lb, fb])
        if fa == fb:
            if la == lb:
                sys.exit('sequência liga um painel a ele mesmo: %s' % [la, fa, lb, fb])
            if not livre_coluna(fa, la, lb):
                sys.exit('a seta %s atravessaria outro painel da mesma fase; mude a fase ou a raia de um deles' % [la, fa, lb, fb])
            plano.append({'tipo': 'coluna', 'la': la, 'fa': fa, 'lb': lb, 'fb': fb})
            continue
        if fb < fa:
            sys.exit('a sequência anda da esquerda para a direita: %s' % [la, fa, lb, fb])
        # a seta dobra no corredor logo depois da origem (corre na raia de destino) ou
        # logo antes do destino (corre na raia de origem); vale a opção sem painel no caminho
        opcoes = sorted({g for g, livre in ((fa, livre_raia(lb, fa + 1, fb)), (fb - 1, livre_raia(la, fa + 1, fb))) if livre})
        if not opcoes:
            sys.exit('a seta %s atravessaria um painel nas fases do meio; reorganize as raias ou as fases' % [la, fa, lb, fb])
        plano.append({'tipo': 'lateral', 'la': la, 'fa': fa, 'lb': lb, 'fb': fb, 'opcoes': opcoes})

    # cada seta sai e chega em altura própria quando o painel tem mais de uma
    def distribuir(chave, ordem, campo):
        grupos = {}
        for p in plano:
            if p['tipo'] == 'lateral':
                grupos.setdefault(chave(p), []).append(p)
        for g in grupos.values():
            g.sort(key=ordem)
            for k, p in enumerate(g):
                p[campo] = (k + 1, len(g))
    distribuir(lambda p: (p['la'], p['fa']), lambda p: (p['lb'], p['fb']), 'saida')
    distribuir(lambda p: (p['lb'], p['fb']), lambda p: (p['la'], p['fa']), 'entrada')

    # a raia só reserva a faixa do chip se algum elemento dela tem chip
    tem_chip = [any(e.get('chip') for e in els if e['raia'] == r) for r in range(len(raias))]
    alt = [12 + PH + (8 + CHIP_H + 8 if tem_chip[r] else 12) for r in range(len(raias))]
    top = [TOPO]
    for h in alt[:-1]:
        top.append(top[-1] + h)
    PT = [t + 12 for t in top]
    CHIP_T = [p + PH + 8 for p in PT]

    def rotear(escolha):
        """Coordenadas de todas as setas para uma escolha de corredor por seta lateral."""
        laterais = [p for p in plano if p['tipo'] == 'lateral']
        for p, g in zip(laterais, escolha):
            p['gap'] = g
            p['y1'] = round(PT[p['la']] + PH * p['saida'][0] / (p['saida'][1] + 1))
            p['y2'] = round(PT[p['lb']] + PH * p['entrada'][0] / (p['entrada'][1] + 1))
        # corredores: cada seta que dobra num corredor ganha um x próprio; as que sobem
        # ficam à esquerda, as que descem à direita, para não se cruzarem na saída
        corredores = {}
        for p in laterais:
            if p['y1'] != p['y2']:
                corredores.setdefault(p['gap'], []).append(p)
        for g in corredores.values():
            sobe = sorted([p for p in g if p['y2'] < p['y1']], key=lambda p: p['y1'])
            desce = sorted([p for p in g if p['y2'] > p['y1']], key=lambda p: -p['y1'])
            for k, p in enumerate(sobe + desce):
                p['slot'] = (k + 1, len(g))
        # só o corredor com várias setas alarga (12px por seta); se o canvas passar de
        # 1320px, os painéis estreitam até 140px antes de a página crescer
        gw = [max(26, 12 * (len(corredores.get(g, [])) + 1)) for g in range(len(fases) - 1)]
        PW = max(140, min(170, (1320 - AX - sum(gw)) // len(fases)))
        FX = [AX]
        for g in gw:
            FX.append(FX[-1] + PW + g)
        colunas = {}
        for p in plano:
            if p['tipo'] == 'coluna':
                colunas.setdefault(p['fa'], []).append(p)
        for g in colunas.values():
            g.sort(key=lambda p: (min(p['la'], p['lb']), p['la']))
            for k, p in enumerate(g):
                p['cx'] = round(FX[p['fa']] + PW * (k + 1) / (len(g) + 1))
        rotas = []
        for p in plano:
            la, fa, lb, fb = p['la'], p['fa'], p['lb'], p['fb']
            if p['tipo'] == 'coluna':
                cx = p['cx']
                if lb > la:
                    y1 = CHIP_T[la] + CHIP_H if celula[(la, fa)].get('chip') else PT[la] + PH
                    rotas.append([(cx, y1), (cx, PT[lb])])
                else:
                    y2 = CHIP_T[lb] + CHIP_H if celula[(lb, fb)].get('chip') else PT[lb] + PH
                    rotas.append([(cx, PT[la]), (cx, y2)])
                continue
            x1, x2, y1, y2 = FX[fa] + PW, FX[fb], p['y1'], p['y2']
            if y1 == y2:
                rotas.append([(x1, y1), (x2, y1)])
                continue
            k, n = p['slot']
            cx = round(FX[p['gap']] + PW + gw[p['gap']] * k / (n + 1))
            rotas.append([(x1, y1), (cx, y1), (cx, y2), (x2, y2)])
        return rotas, PW, FX

    def custo(rotas):
        """Cruzamentos entre setas, e verticais correndo a menos de 20px uma da outra."""
        segs = [[(a, b) for a, b in zip(r, r[1:])] for r in rotas]
        total = 0
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                for (p1, p2) in segs[i]:
                    for (q1, q2) in segs[j]:
                        for (h1, h2), (v1, v2) in (((p1, p2), (q1, q2)), ((q1, q2), (p1, p2))):
                            if h1[1] == h2[1] and v1[0] == v2[0]:
                                if min(h1[0], h2[0]) < v1[0] < max(h1[0], h2[0]) and min(v1[1], v2[1]) < h1[1] < max(v1[1], v2[1]):
                                    total += 10
                        if p1[0] == p2[0] and q1[0] == q2[0] and abs(p1[0] - q1[0]) < 20:
                            ov = min(max(p1[1], p2[1]), max(q1[1], q2[1])) - max(min(p1[1], p2[1]), min(q1[1], q2[1]))
                            if ov > 0:
                                total += 1
        return total

    # cada seta longa tem até duas opções de corredor; fica a combinação com menos cruzamentos
    laterais = [p for p in plano if p['tipo'] == 'lateral']
    combinacoes = list(itertools.product(*[p['opcoes'] for p in laterais]))
    if len(combinacoes) > 4096:
        combinacoes = [tuple(p['opcoes'][-1] for p in laterais)]
    def trocar_ordem(escolha):
        """Troca a ordem de saída e de chegada nos painéis enquanto isso tirar cruzamento."""
        atual = custo(rotear(escolha)[0])
        mudou = True
        while mudou:
            mudou = False
            for campo, chave in (('saida', lambda p: (p['la'], p['fa'])), ('entrada', lambda p: (p['lb'], p['fb']))):
                grupos = {}
                for p in laterais:
                    grupos.setdefault(chave(p), []).append(p)
                for g in grupos.values():
                    for i in range(len(g)):
                        for j in range(i + 1, len(g)):
                            g[i][campo], g[j][campo] = g[j][campo], g[i][campo]
                            c = custo(rotear(escolha)[0])
                            if c < atual:
                                atual, mudou = c, True
                            else:
                                g[i][campo], g[j][campo] = g[j][campo], g[i][campo]
        return atual

    melhor = None
    for _ in range(2):
        melhor = min(combinacoes, key=lambda c: custo(rotear(c)[0]))
        if trocar_ordem(melhor) == 0:
            break
    rotas, PW, FX = rotear(melhor)
    canvas_w = FX[-1] + PW
    canvas_h = top[-1] + alt[-1] + 6

    out = []
    for i, r in enumerate(raias):
        out.append(f'      <div class="lane" style="left:0px;top:{top[i]}px;width:{canvas_w}px;height:{alt[i]}px">')
        out.append(f'        <div class="lt">{esc(r["nome"])}</div>')
        if r.get('sub'):
            out.append(f'        <div class="ls">{esc(r["sub"])}</div>')
        out.append('      </div>')
    for i, f in enumerate(fases):
        out.append(f'      <div class="fase" style="left:{FX[i]}px;width:{PW}px">{i + 1} · {esc(f)}</div>')
    for e in els:
        x, y = FX[e['fase']], PT[e['raia']]
        cls = 'painel' + (' ' + e['estilo'] if e.get('estilo') else '')
        out.append(f'      <div class="{cls}" style="left:{x}px;top:{y}px;width:{PW}px;height:{PH}px">')
        if e.get('titulo'):
            out.append(f'        <div class="pt">{esc(e["titulo"])}</div>')
        margem = '' if e.get('titulo') else ' style="margin-top:0"'
        out.append(f'        <div class="ps"{margem}>{esc(e["texto"])}</div>')
        out.append('      </div>')
        if e.get('chip'):
            out.append(f'      <div class="chip" style="left:{x}px;top:{CHIP_T[e["raia"]]}px">{esc(e["chip"])}</div>')

    paths = []
    for r in rotas:
        d = 'M%d,%d' % r[0]
        for (x0, y0), (x, y) in zip(r, r[1:]):
            d += ' H%d' % x if y == y0 else ' V%d' % y
        paths.append(d)

    svg = [f'      <svg class="edges" viewBox="0 0 {canvas_w} {canvas_h}">',
           '        <defs><marker id="s" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">',
           '          <path d="M0,0 L9,4.5 L0,9 z" style="fill:var(--apoio)"/></marker></defs>']
    for d in paths:
        svg.append(f'        <path d="{d}" stroke-width="1.6" fill="none" marker-end="url(#s)" style="stroke:var(--apoio)"/>')
    svg.append('      </svg>')

    secoes = []
    for s in S.get('secoes', []):
        secoes.append(f'  <div class="sec">{esc(s["titulo"])}</div>')
        n = len(s['itens'])
        if s.get('tipo') == 'destinos':
            secoes.append(f'  <div class="destinos" style="grid-template-columns:repeat({n},1fr)">')
            for t, d in s['itens']:
                secoes.append(f'    <div class="destino"><div class="dt">{esc(t)}</div><div class="dd">{esc(d)}</div></div>')
        else:
            secoes.append(f'  <div class="legenda" style="grid-template-columns:repeat({n},1fr)">')
            for t, d in s['itens']:
                secoes.append(f'    <div class="passo"><div class="pn">{esc(t)}</div><div class="pd">{esc(d)}</div></div>')
        secoes.append('  </div>')

    faixa = ''
    if S.get('faixa'):
        f2 = f'\n    <div class="f2">{esc(S["faixa"]["f2"])}</div>' if S['faixa'].get('f2') else ''
        faixa = f'  <div class="faixa">\n    <div class="f1">{esc(S["faixa"]["f1"])}</div>{f2}\n  </div>'

    # a página cresce com o desenho: legibilidade vence a largura padrão de 1400px
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

  <div class="kicker"><span class="sq">■</span> {esc(S['kicker'])}</div>
  <h1>{esc(S['h1'])}</h1>
  <div class="sub">{esc(S['sub'])}</div>

  <div class="canvas" style="width:{canvas_w}px;height:{canvas_h}px">
{chr(10).join(out)}
{chr(10).join(svg)}
  </div>

{chr(10).join(secoes)}
{faixa}

  <div class="foot"><span>{esc(fe)}</span><span>{esc(fd)}</span></div>

</div>
</body></html>
'''
    open(saida, 'w').write(doc)
    print(saida)
    print('canvas %dx%d · %d raias · %d fases · %d setas' % (canvas_w, canvas_h, len(raias), len(fases), len(paths)))


if __name__ == '__main__':
    main()
