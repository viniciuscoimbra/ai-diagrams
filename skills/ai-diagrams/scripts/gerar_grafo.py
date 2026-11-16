#!/usr/bin/env python3
"""Gera o fonte HTML de um grafo de contexto a partir de um JSON.

Uso: python3 gerar_grafo.py <spec.json> [saida.html] [--tema NOME|caminho.json] [--idioma pt-BR|en|es]

Duas vistas, escolhidas pelo campo "vista" do JSON:

  afirmacoes  o contexto como grafo: nó é entidade ou valor; aresta é afirmação
              (fato, regra declarada, relação ou elo de identidade), com o carimbo
              observador, tempo válido e tempo de gravação escrito na aresta.
  produtos    os produtos de contexto e o harness: quem compõe quem, quem traduz
              entre áreas, que versão o harness consulta, que evento volta, quem decide.

Antes do desenho, confere o grafo pelas regras do modelo (lista em
references/grafo.md) e para com GRAFO REPROVOU <código>. Depois o elkjs
(estados/elk-layout.cjs) decide posição e roteamento ortogonal; o desenho é
desta skill. Sem saída explícita, grava <spec>.html ao lado do JSON. O build e
o lint são do conceitual.py.
"""
import json, os, sys, html, math, re, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
ELK = os.path.join(AQUI, '..', 'estados', 'elk-layout.cjs')

# medidas fixas: o tema não muda a geometria
C_PT = 9.6        # 17px peso 600
C_PS = 8.1        # 15px
C_TAG = 8.6       # 11px mono maiúsculo com espaçamento
C_LAB = 8.2       # 15px, rótulo da aresta
C_CAR = 7.9       # 12.5px mono, carimbo
L_LAB, L_CAR = 20, 18
NO_W = {'entidade': 228, 'valor': 176, 'produto': 268, 'traducao': 268, 'harness': 300, 'consumidor': 228}
LARGURA_MAX = 1320
# arestas que o layout recebe invertidas, para o desenho correr de contexto para harness e
# de harness para quem age; a seta continua no sentido declarado
INVERTIDAS = ('consulta', 'revisa')
DATA = re.compile(r'^\d{4}-\d{2}-\d{2}$')

VISTAS = {
    'afirmacoes': {
        'nos': ('entidade', 'valor'),
        'arestas': {
            'fato': (('entidade',), ('valor',)),
            'regra': (('entidade',), ('valor', 'entidade')),
            'relacao': (('entidade',), ('entidade',)),
            'identidade': (('entidade',), ('entidade',)),
        },
    },
    'produtos': {
        'nos': ('produto', 'traducao', 'harness', 'consumidor'),
        'arestas': {
            'compoe': (('produto', 'traducao'), ('produto', 'traducao')),
            'traduz': (('traducao',), ('produto',)),
            'consulta': (('harness',), ('produto', 'traducao')),
            'evento': (('produto', 'traducao'), ('harness',)),
            'decide': (('harness',), ('consumidor',)),
            'revisa': (('consumidor',), ('harness',)),
        },
    },
}


def esc(t):
    return html.escape(str(t), quote=False)


def code_html(t):
    """`trecho` vira <code>."""
    partes = re.split(r'`([^`]+)`', str(t))
    return ''.join(esc(p) if i % 2 == 0 else '<code>%s</code>' % esc(p) for i, p in enumerate(partes))


def erro(codigo, msg):
    sys.exit('GRAFO REPROVOU %s: %s' % (codigo, msg))


def quebra(texto, largura, char):
    """Quebra em linhas que cabem em largura px; devolve a lista de linhas."""
    linhas, atual = [], ''
    for tok in str(texto).split():
        teste = (atual + ' ' + tok).strip()
        if atual and len(teste.replace('`', '')) * char > largura:
            linhas.append(atual)
            atual = tok
        else:
            atual = teste
    return linhas + [atual] if atual else linhas


def tempo_txt(v, tr):
    ini, fim = v
    if fim:
        return tr['grafo.valido_de_a'].format(ini=ini, fim=fim)
    return tr['grafo.valido_desde'].format(ini=ini)


# ---------------------------------------------------------------- conferência

def conferir_comum(S, vista):
    V = VISTAS[vista]
    ids = {}
    grupos = {g['id'] for g in S.get('grupos', [])}
    for n in S.get('nos', []):
        if not n.get('id') or not str(n.get('nome', '')).strip():
            erro('NO-INCOMPLETO', 'nó sem id ou sem nome: %s' % json.dumps(n, ensure_ascii=False))
        if n['id'] in ids:
            erro('DUPLICADO', 'dois nós com o id "%s"' % n['id'])
        if n.get('tipo') not in V['nos']:
            erro('TIPO-INVALIDO', 'nó "%s" com tipo "%s"; na vista %s os tipos são %s'
                 % (n['id'], n.get('tipo'), vista, ', '.join(V['nos'])))
        if n.get('grupo') and n['grupo'] not in grupos:
            erro('DESCONHECIDO', 'nó "%s" cita o grupo "%s", que não está em grupos' % (n['id'], n['grupo']))
        ids[n['id']] = n
    if not ids:
        erro('VAZIO', 'declare ao menos um nó em "nos"')
    for k, a in enumerate(S.get('arestas', [])):
        for lado in ('de', 'para'):
            if a.get(lado) not in ids:
                erro('DESCONHECIDO', 'aresta %d cita "%s", que não está em nos' % (k + 1, a.get(lado)))
        if a.get('tipo') not in V['arestas']:
            erro('TIPO-INVALIDO', 'aresta %s -> %s com tipo "%s"; na vista %s os tipos são %s'
                 % (a['de'], a['para'], a.get('tipo'), vista, ', '.join(V['arestas'])))
        if a['de'] == a['para']:
            erro('LACO', 'aresta %s -> %s liga o nó a ele mesmo' % (a['de'], a['para']))
        de_ok, para_ok = V['arestas'][a['tipo']]
        if ids[a['de']]['tipo'] not in de_ok or ids[a['para']]['tipo'] not in para_ok:
            erro('FRONTEIRA', '%s não liga %s (%s) a %s (%s); aceita %s -> %s'
                 % (a['tipo'], a['de'], ids[a['de']]['tipo'], a['para'], ids[a['para']]['tipo'],
                    '|'.join(de_ok), '|'.join(para_ok)))
    return ids


def conferir_afirmacoes(S, ids):
    obs = {}
    for o in S.get('observadores', []):
        obs[o['id']] = set(o.get('autoridade', []))
    if not obs:
        erro('SEM-OBSERVADORES', 'declare "observadores" com id e autoridade (tipos de fato) de cada produto de contexto')
    definidos = set(S.get('definicoes', []))
    for a in S['arestas']:
        nome = '%s -> %s (%s)' % (a['de'], a['para'], a['tipo'])
        for campo in ('observador', 'gravado'):
            if not a.get(campo):
                erro('SEM-CARIMBO', '%s sem "%s": toda afirmação tem entidade, observador, tempo válido e tempo de gravação' % (nome, campo))
        if a['tipo'] != 'identidade' and not a.get('valido'):
            erro('SEM-CARIMBO', '%s sem "valido": [início, fim ou null]' % nome)
        if a['observador'] not in obs:
            erro('OBSERVADOR-DESCONHECIDO', '%s cita o observador "%s", que não está em observadores' % (nome, a['observador']))
        if not DATA.match(str(a['gravado'])):
            erro('DATA-INVALIDA', '%s: gravado "%s" não é AAAA-MM-DD' % (nome, a['gravado']))
        v = a.get('valido')
        if v is not None:
            if not (isinstance(v, list) and len(v) == 2 and DATA.match(str(v[0]))
                    and (v[1] is None or DATA.match(str(v[1])))):
                erro('DATA-INVALIDA', '%s: valido precisa ser ["AAAA-MM-DD", "AAAA-MM-DD" ou null]' % nome)
            if v[1] and v[1] < v[0]:
                erro('DATA-INVALIDA', '%s: o tempo válido termina (%s) antes de começar (%s)' % (nome, v[1], v[0]))
        if a['tipo'] in ('fato', 'regra') and not a.get('atributo'):
            erro('SEM-ATRIBUTO', '%s sem "atributo": o tipo de fato que a afirmação muda' % nome)
        if a['tipo'] == 'regra':
            if not a.get('condicao'):
                erro('REGRA-SEM-CONDICAO', '%s sem "condicao"; sem condição é fato' % nome)
            faltam = [t for t in a.get('termos', []) if t not in definidos]
            if faltam and not a.get('derivada'):
                erro('TERMO-SEM-DEFINICAO', '%s usa %s sem definição em "definicoes". Termo sem definição faz a regra virar '
                     'derivada: declare a definição ou marque "derivada": true' % (nome, ', '.join(faltam)))
        if a['tipo'] == 'relacao' and not a.get('rotulo'):
            erro('SEM-ROTULO', '%s sem "rotulo" (titular, controla, responsável)' % nome)
        if a['tipo'] == 'identidade':
            c = a.get('confianca')
            if not isinstance(c, (int, float)) or isinstance(c, bool) or not 0 < c <= 1:
                erro('IDENTIDADE-SEM-CONFIANCA', '%s: elo de identidade precisa de "confianca" entre 0 e 1' % nome)
            ga, gb = ids[a['de']].get('grupo'), ids[a['para']].get('grupo')
            if ga and ga == gb:
                erro('IDENTIDADE-MESMA-AREA', '%s liga duas entidades da mesma área (%s); identidade liga áreas diferentes' % (nome, ga))
        a['_sem_autoridade'] = a['tipo'] in ('fato', 'regra') and a['atributo'] not in obs[a['observador']]
    for n in ids.values():
        if n['tipo'] == 'valor' and not any(a['para'] == n['id'] for a in S['arestas']):
            erro('VALOR-SOLTO', 'o valor "%s" não é alvo de nenhuma afirmação' % n['id'])


def conferir_produtos(S, ids):
    autoridade = {}
    for n in ids.values():
        if n['tipo'] in ('produto', 'traducao'):
            for campo in ('dono', 'versao'):
                if not n.get(campo):
                    erro('SEM-' + campo.upper(), 'o produto "%s" não tem "%s"; dono e versão são propriedades do produto' % (n['id'], campo))
            for t in n.get('autoridade', []):
                chave = (n.get('area'), t)
                if chave in autoridade:
                    erro('AUTORIDADE-DUPLICADA', '"%s" e "%s" declaram autoridade sobre %s%s' % (
                        autoridade[chave], n['id'], t, ' na área ' + n['area'] if n.get('area') else ''))
                autoridade[chave] = n['id']
        if n['tipo'] == 'harness':
            if not n.get('politicas'):
                erro('HARNESS-SEM-POLITICA', 'o harness "%s" não lista "politicas"' % n['id'])
            for campo in ('dono', 'desde'):
                if not n.get(campo):
                    erro('POLITICA-SEM-AUTOR', 'o harness "%s" não tem "%s": a política registra quem definiu e desde quando vale' % (n['id'], campo))
    for a in S['arestas']:
        if a['tipo'] in ('compoe', 'consulta') and not a.get('versao'):
            erro('REFERENCIA-SEM-VERSAO', '%s -> %s (%s) sem "versao": produtos se referem por número de versão, não por relógio'
                 % (a['de'], a['para'], a['tipo']))
        if a['tipo'] == 'evento' and not a.get('rotulo'):
            erro('SEM-ROTULO', 'evento %s -> %s sem "rotulo" (o que mudou: dividiu, fundiu, nova versão)' % (a['de'], a['para']))
    # composição sem ciclo
    filhos = {}
    for a in S['arestas']:
        if a['tipo'] == 'compoe':
            filhos.setdefault(a['de'], []).append(a['para'])
    cor = {}

    def visita(v, cam):
        cor[v] = 1
        for w in filhos.get(v, []):
            if cor.get(w) == 1:
                erro('CICLO-COMPOSICAO', 'composição em ciclo: %s' % ' -> '.join(cam + [v, w]))
            if not cor.get(w):
                visita(w, cam + [v])
        cor[v] = 2
    for v in list(filhos):
        if not cor.get(v):
            visita(v, [])


# ---------------------------------------------------------------- nós e rótulos

def linhas_no(n, tr):
    """(classe, texto) de cada linha do nó, já com o tamanho estimado."""
    t = n['tipo']
    w = n.get('largura', NO_W[t])
    if type(w) is not int or w < 120:
        erro('LARGURA-INVALIDA', 'largura do nó "%s" precisa ser um inteiro de 120 ou mais' % n['id'])
    util = w - 34
    tag = n.get('tag')
    if not tag:
        tag = {
            'entidade': tr['grafo.tag.entidade'],
            'valor': tr['grafo.tag.valor'],
            'produto': tr['grafo.tag.produto'] + (' · v' + str(n.get('versao')) if n.get('versao') else ''),
            'traducao': tr['grafo.tag.traducao'] + (' · v' + str(n.get('versao')) if n.get('versao') else ''),
            'harness': tr['grafo.tag.harness'],
            'consumidor': tr['grafo.tag.consumidor'],
        }[t]
    L = [('ptag', tag)]
    if len(tag) * C_TAG > util:
        erro('TEXTO-LONGO', 'tag do nó "%s" não cabe em uma linha' % n['id'])
    L += [('pt', l) for l in quebra(n['nome'], util, C_PT)]
    subs = []
    if n.get('sub'):
        subs.append(n['sub'])
    if t in ('produto', 'traducao'):
        subs.append(tr['grafo.dono'] + ': ' + n['dono'])
        if n.get('autoridade'):
            subs.append(tr['grafo.autoridade'] + ': ' + ', '.join(n['autoridade']))
        if n.get('camada'):
            subs.append(tr['grafo.camada'] + ': ' + n['camada'])
    if t == 'harness':
        subs += ['· ' + p for p in n['politicas']]
        subs.append(tr['grafo.definida'].format(dono=n['dono'], desde=n['desde']))
    for s in subs:
        L += [('ps', l) for l in quebra(s, util, C_PS)]
    h = 26 + 3
    for cls, _ in L:
        h += {'ptag': 19, 'pt': 21, 'ps': 20}[cls]
    h += 5 if any(c == 'ps' for c, _ in L) else 0
    return L, w, int(math.ceil(h)) + 4


def rotulo_aresta(a, vista, tr):
    """Linhas do rótulo: (classe, texto). A primeira diz o que a aresta afirma; as outras, o carimbo."""
    t = a['tipo']
    L = []
    if vista == 'afirmacoes':
        if t == 'fato':
            L.append(('ev', a['atributo']))
        elif t == 'regra':
            L.append(('ev', a['atributo']))
            L.append(('gd', tr['grafo.se'] + ' ' + a['condicao']))
        elif t == 'relacao':
            L.append(('ev', a['rotulo']))
        elif t == 'identidade':
            L.append(('ev', tr['grafo.mesmo_ente'] + ' · ' + ('%.2f' % a['confianca']).replace('.', tr['grafo.decimal'])))
        L.append(('carimbo', a['observador']))
        if a.get('valido'):
            L.append(('carimbo', tempo_txt(a['valido'], tr)))
        L.append(('carimbo', tr['grafo.gravado'] + ' ' + a['gravado']))
        if a.get('_sem_autoridade'):
            L.append(('alerta', tr['grafo.sem_autoridade']))
        if t == 'regra' and a.get('derivada'):
            L.append(('alerta', tr['grafo.derivada']))
    else:
        base = a.get('rotulo') or tr['grafo.aresta.' + t]
        if a.get('versao'):
            base += ' · v' + str(a['versao'])
        L.append(('ev', base))
    saida = []
    for cls, txt in L:
        char = C_CAR if cls in ('carimbo', 'alerta') else C_LAB
        for l in quebra(txt, 230, char):
            saida.append((cls, l))
    w = max(40, max(len(l) * (C_CAR if c in ('carimbo', 'alerta') else C_LAB) for c, l in saida))
    h = sum(L_CAR if c in ('carimbo', 'alerta') else L_LAB for c, _ in saida)
    return saida, int(w) + 10, h + 2


def rotulo_html(linhas):
    return ''.join('<span class="gl %s">%s</span>' % (cls, code_html(l)) for cls, l in linhas)


# ---------------------------------------------------------------- layout

def zonas_produtos(S, ids, tr):
    """Na vista de produtos, a fronteira contexto/harness é desenhada sempre: grupos fixos."""
    gr = [{'id': '__ctx', 'nome': tr['grafo.zona.contexto'], 'cls': 'ctx'},
          {'id': '__har', 'nome': tr['grafo.zona.harness'], 'cls': 'har'}]
    for n in ids.values():
        if n['tipo'] in ('produto', 'traducao'):
            n['grupo'] = '__ctx'
        elif n['tipo'] == 'harness':
            n['grupo'] = '__har'
        else:
            n['grupo'] = None
    return gr


def layout(S, grupos, nos, direcao, vista):
    filhos_raiz, por_grupo = [], {g['id']: [] for g in grupos}
    for n in nos:
        item = {'id': n['id'], 'width': n['_w'], 'height': n['_h']}
        (por_grupo[n['grupo']] if n.get('grupo') else filhos_raiz).append(item)
    for g in grupos:
        if por_grupo[g['id']]:
            filhos_raiz.append({'id': '__g_' + g['id'], 'children': por_grupo[g['id']],
                                'layoutOptions': {'elk.padding': '[top=40,left=24,bottom=24,right=24]'}})
    arestas = []
    for k, a in enumerate(S['arestas']):
        de, para = (a['para'], a['de']) if a['tipo'] in INVERTIDAS else (a['de'], a['para'])
        arestas.append({'id': 'a%d' % k, 'sources': [de], 'targets': [para],
                        'labels': [{'id': 'l%d' % k, 'width': a['_w'], 'height': a['_h'], 'text': 'x'}]})
    g = {'id': 'raiz', 'children': filhos_raiz, 'edges': arestas, 'layoutOptions': {
        'elk.algorithm': 'layered',
        'elk.direction': direcao,
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
        'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
        'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
        'elk.spacing.nodeNode': '48',
        'elk.layered.spacing.nodeNodeBetweenLayers': '64',
        'elk.spacing.edgeEdge': '22',
        'elk.spacing.edgeNode': '26',
        'elk.layered.spacing.edgeEdgeBetweenLayers': '22',
        'elk.layered.spacing.edgeNodeBetweenLayers': '26',
        'elk.spacing.edgeLabel': '8',
        'elk.spacing.labelNode': '10',
        'elk.edgeLabels.placement': 'CENTER',
        'elk.padding': '[top=20,left=20,bottom=20,right=20]',
    }}
    r = subprocess.run(['node', ELK], input=json.dumps(g), capture_output=True, text=True)
    if r.returncode:
        sys.exit('elkjs falhou: ' + r.stderr.strip())
    return json.loads(r.stdout)


# ---------------------------------------------------------------- página

def notacao(vista, S, tr):
    itens = []

    def lin(cls, rot):
        itens.append(f'<div class="nt"><div class="lin {cls}"></div>{esc(rot)}</div>')

    if vista == 'afirmacoes':
        itens.append(f'<div class="nt"><div class="no-mini"></div>{esc(tr["grafo.tag.entidade"])}</div>')
        itens.append(f'<div class="nt"><div class="no-mini valor"></div>{esc(tr["grafo.tag.valor"])}</div>')
        tipos = {a['tipo'] for a in S['arestas']}
        for t in ('fato', 'regra', 'relacao', 'identidade'):
            if t in tipos:
                lin('g-' + t, tr['grafo.nota.' + t])
        itens.append(f'<div class="nt"><span class="nt-rot"><span class="carimbo">{esc(tr["grafo.observador"])}</span></span>'
                     f'{esc(tr["grafo.nota.carimbo"])}</div>')
        if any(a.get('_sem_autoridade') or a.get('derivada') for a in S['arestas']):
            lin('g-alerta', tr['grafo.nota.alerta'])
    else:
        itens.append(f'<div class="nt"><div class="no-mini"></div>{esc(tr["grafo.nota.produto"])}</div>')
        itens.append(f'<div class="nt"><div class="no-mini har"></div>{esc(tr["grafo.nota.harness"])}</div>')
        tipos = {a['tipo'] for a in S['arestas']}
        for t in ('compoe', 'traduz', 'consulta', 'evento', 'decide', 'revisa'):
            if t in tipos:
                lin('g-' + t, tr['grafo.nota.' + t])
    return f'  <div class="sec">{esc(tr["comum.notacao"])}</div>\n  <div class="notacao wrap">' + ''.join(itens) + '</div>'


def main():
    sys.path.insert(0, AQUI)
    import tema, idioma
    flag_tema, sys.argv[1:] = tema.tirar_flag(sys.argv[1:])
    flag_idioma, sys.argv[1:] = idioma.tirar_flag(sys.argv[1:])
    tm = tema.tema(flag_tema)
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    S = json.load(open(spec_path))
    tr = idioma.idioma(flag_idioma, fonte_json=S)
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(spec_path)[0] + '.html'
    tema_html = tema.para_gerador(tm, saida)
    tema_meta = tema_html['meta'] + '\n' if tema_html['meta'] else ''
    idioma_meta = idioma.para_gerador(tr)

    vista = S.get('vista')
    if vista not in VISTAS:
        erro('VISTA-INVALIDA', '"vista" precisa ser afirmacoes ou produtos')
    S.setdefault('arestas', [])
    ids = conferir_comum(S, vista)
    if vista == 'afirmacoes':
        conferir_afirmacoes(S, ids)
        grupos = [dict(g, cls='area') for g in S.get('grupos', [])]
    else:
        conferir_produtos(S, ids)
        grupos = zonas_produtos(S, ids, tr)

    nos = S['nos']
    for n in nos:
        n['_L'], n['_w'], n['_h'] = linhas_no(n, tr)
    for a in S['arestas']:
        a['_L'], a['_w'], a['_h'] = rotulo_aresta(a, vista, tr)

    g = layout(S, grupos, nos, S.get('direcao', 'RIGHT'), vista)
    if g['width'] > LARGURA_MAX and 'direcao' not in S:
        g2 = layout(S, grupos, nos, 'DOWN', vista)
        if g2['width'] < g['width']:
            g = g2
    canvas_w, canvas_h = int(math.ceil(g['width'])), int(math.ceil(g['height']))
    R = lambda v: int(round(v))

    # origem absoluta de cada contêiner do ELK
    origem, pos = {'raiz': (0, 0)}, {}
    for c in g['children']:
        if c['id'].startswith('__g_'):
            origem[c['id']] = (c['x'], c['y'])
            for k in c.get('children', []):
                pos[k['id']] = (c['x'] + k['x'], c['y'] + k['y'])
        else:
            pos[c['id']] = (c['x'], c['y'])

    out = []
    for n in nos:
        x, y = pos[n['id']]
        cls = 'painel gno ' + n['tipo'] + (' ' + n['estilo'] if n.get('estilo') else '')
        corpo = ''.join(f'<div class="{c}">{code_html(t)}</div>' for c, t in n['_L'])
        out.append(f'      <div class="{cls}" style="left:{R(x)}px;top:{R(y)}px;width:{n["_w"]}px;height:{n["_h"]}px">{corpo}</div>')

    svg, segs = [], []
    for e in g['edges']:
        k = int(e['id'][1:])
        a = S['arestas'][k]
        ox, oy = origem.get(e.get('container', 'raiz'), (0, 0))
        estilo = 'g-' + a['tipo'] + (' g-alerta' if a.get('_sem_autoridade') or a.get('derivada') else '')
        seta = a['tipo'] != 'identidade'
        for s in e.get('sections', []):
            pts = [s['startPoint']] + s.get('bendPoints', []) + [s['endPoint']]
            if a['tipo'] in INVERTIDAS:
                pts.reverse()
            d = 'M%d,%d ' % (R(pts[0]['x'] + ox), R(pts[0]['y'] + oy)) + ' '.join(
                'L%d,%d' % (R(p['x'] + ox), R(p['y'] + oy)) for p in pts[1:])
            segs += [(R(p['x'] + ox), R(p['y'] + oy), R(q['x'] + ox), R(q['y'] + oy)) for p, q in zip(pts, pts[1:])]
            mk = ' marker-end="url(#s)"' if seta else ''
            svg.append(f'        <path class="{estilo}" d="{d}" fill="none"{mk}/>')
        lb = e['labels'][0]
        out.append(f'      <div class="mlabel glabel" style="left:{R(lb["x"] + ox)}px;top:{R(lb["y"] + oy)}px;width:{a["_w"]}px">'
                   f'{rotulo_html(a["_L"])}</div>')

    # moldura da área: o nome fica na borda de cima, no primeiro trecho que nenhuma seta cruza;
    # sem trecho livre em cima, tenta a borda de baixo
    gnome = {gg['id']: gg for gg in grupos}
    molduras = []
    for c in g['children']:
        if not c['id'].startswith('__g_'):
            continue
        gg = gnome[c['id'][4:]]
        fx, fy, fw, fh = R(c['x']), R(c['y']), R(c['width']), R(c['height'])
        lw = int(len(gg['nome']) * C_TAG + 24)

        def livre(bx, faixa):
            x1, x2, (y1, y2) = bx - 4, bx + lw + 4, faixa
            for (a1, b1, a2, b2) in segs:
                if max(a1, a2) >= x1 and min(a1, a2) <= x2 and max(b1, b2) >= y1 and min(b1, b2) <= y2:
                    return False
            return True
        lugar = None
        # em cima o nome corta a borda; embaixo fica dentro do respiro de 24 px da área
        for borda, faixa in (('', (fy - 12, fy + 12)), (' baixo', (fy + fh - 24, fy + fh + 2))):
            for dx in range(14, max(15, fw - lw - 13), 8):
                if livre(fx + dx, faixa):
                    lugar = (borda, dx)
                    break
            if lugar:
                break
        if not lugar:
            erro('MOLDURA-SEM-LUGAR', 'toda a borda da área "%s" é cruzada por setas; aumente a área ou mude a direção' % gg['nome'])
        molduras.append(f'      <div class="frame gframe {gg["cls"]}" style="left:{fx}px;top:{fy}px;'
                        f'width:{fw}px;height:{fh}px"><div class="flabel{lugar[0]}" style="left:{lugar[1]}px">{esc(gg["nome"])}</div></div>')
    out = molduras + out

    svg_html = (f'      <svg class="edges" viewBox="0 0 {canvas_w} {canvas_h}">\n'
                '        <defs><marker id="s" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">\n'
                '          <path d="M0,0 L9,4.5 L0,9 z" style="fill:var(--apoio)"/></marker></defs>\n'
                + '\n'.join(svg) + '\n      </svg>')

    secoes = []
    com_desc = [n for n in nos if n.get('desc')]
    if com_desc:
        secoes.append(f'  <div class="sec">{esc(tr["grafo.nos"])}</div>\n  <div class="passos-seq estados-leg">')
        for n in com_desc:
            secoes.append(f'    <div class="ps-item"><div class="pd"><b>{code_html(n["nome"])}</b> {code_html(n["desc"])}</div></div>')
        secoes.append('  </div>')
    secoes.append(notacao(vista, S, tr))

    faixa = ''
    if S.get('faixa'):
        f2 = f'\n    <div class="f2">{esc(S["faixa"]["f2"])}</div>' if S['faixa'].get('f2') else ''
        faixa = f'  <div class="faixa">\n    <div class="f1">{esc(S["faixa"]["f1"])}</div>{f2}\n  </div>'

    pagina = canvas_w + 80
    largura_meta = f'<meta name="largura" content="{pagina}">\n' if pagina > 1400 else ''
    largura_css = f'\nbody{{width:{pagina}px}}' if pagina > 1400 else ''
    he, hd = S['cabecalho']
    fe, fd = S['rodape']
    kicker = S.get('kicker', tr['grafo.kicker.' + vista])
    doc = f'''<!doctype html><html lang="{tr['_codigo']}"><head><meta charset="utf-8">
<title>{esc(S['titulo_pagina'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{tema_html['link']}
{tema_meta}{idioma_meta}{largura_meta}<style>/*ESTILO*/{largura_css}</style></head><body>
<div class="page">

  <div class="hdr"><span>{esc(he)}</span><span>{esc(hd)}</span></div>

  <div class="kicker"><span class="sq">■</span> {esc(kicker)}</div>
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
    print('canvas %dx%d · vista %s · %d nós · %d arestas' % (canvas_w, canvas_h, vista, len(nos), len(S['arestas'])))


if __name__ == '__main__':
    main()
