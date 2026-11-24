#!/usr/bin/env python3
"""Draws every view of a C4 model: one JSON with people, systems, containers, components,
deployment nodes and relationships, and the views to draw from it.

Usage: python3 build_c4.py <model.json> [--no-build] [--theme NAME|path.json] [--lang pt-BR|en|es]

Writes one HTML source per view next to the JSON: <name>.html for the main view and
<name>-<key>.html for the others. Then builds each one through build.py and its gate,
unless --no-build. A model in Structurizr DSL is read by `ai-diagrams import`.

Views (field "type"):
  landscape   people and software systems, no focus;
  context     level 1: the system in focus and who and what it talks to;
  container   level 2: the system becomes a boundary with its containers inside;
  component   level 3: a container becomes a boundary with its components inside;
  dynamic     numbered steps between elements of any level, in order;
  deployment  deployment nodes of one environment, with container instances and
              infrastructure nodes inside.
A view may narrow what it shows with "include" and "exclude" (lists of element ids).

Relationships are written once, at the most detailed level. A view that does not show
the source or the target draws the relationship to the nearest visible ancestor (implied
relationship), once per pair; a relationship written at that level wins over an implied one.

Each arrow carries its own label: what it does and [technology]. The label sits on the
arrow and never touches a box, a border, another arrow or another label. Position and
routing come from elkjs (c4/elk-batch.cjs); several layout variants are tried and the
one with the fewest crossings, then the fewest bends, the shortest arrows and the
smallest area, is kept. Box and label sizes are measured in Chrome with the default theme,
so the geometry does not depend on the theme.

Stops with a message when:
  C4-DUPLICATE      two elements share an id;
  C4-UNKNOWN        a relationship, step, view or parent names an unknown id;
  C4-PARENT         a container outside a system, a component outside a container, a node
                    or instance outside a deployment node, an instance of a non-container;
  C4-NO-DESCRIPTION an element or relationship without description;
  C4-NO-TECHNOLOGY  a container, component, infrastructure node or relationship without technology;
  C4-SHAPE          an unknown shape (web, database, queue, mobile);
  C4-VIEW           a view with an unknown type, a missing scope or nothing to draw;
  C4-NO-ROOM        no layout leaves room for every label.
"""
import json, os, sys, html, math, re, subprocess, tempfile, textwrap

AQUI = os.path.dirname(os.path.abspath(__file__))
ELK = os.path.join(AQUI, '..', 'c4', 'elk-batch.cjs')
R = lambda v: int(round(v))
SHAPES = ('web', 'database', 'queue', 'mobile')
TIPOS = ('person', 'system', 'container', 'component', 'deploymentNode', 'infrastructureNode', 'containerInstance')
VISTAS = ('landscape', 'context', 'container', 'component', 'dynamic', 'deployment')
BOX_W, PERSON_W, INFRA_W = 260, 250, 230
HEAD, HEAD_OFF = 40, 28          # cabeça da pessoa: diâmetro e quanto ela sobe acima do corpo
REL_MAX = 210                    # largura máxima do rótulo da relação


def esc(t):
    return html.escape(str(t), quote=False)


def erro(codigo, msg):
    sys.exit('C4 FAILED %s: %s' % (codigo, msg))


# ------------------------------------------------------------------ modelo

class Modelo:
    def __init__(self, S):
        self.S = S
        self.el = {}
        for e in S.get('elements', []):
            if e.get('id') in self.el:
                erro('C4-DUPLICATE', 'two elements with id "%s"' % e.get('id'))
            self.el[e['id']] = e
        self.rels = S.get('relationships', [])
        self.conferir()

    def ancestrais(self, i):
        out = []
        p = self.el[i].get('parent')
        while p:
            out.append(p)
            p = self.el[p].get('parent')
        return out

    def filhos(self, i, tipo=None):
        return [e['id'] for e in self.S['elements'] if e.get('parent') == i and (tipo is None or e['type'] == tipo)]

    def conferir(self):
        for e in self.S['elements']:
            t = e.get('type')
            if t not in TIPOS:
                erro('C4-UNKNOWN', 'element "%s" has type "%s"; use one of %s' % (e['id'], t, ', '.join(TIPOS)))
            if not str(e.get('name', '')).strip() and t != 'containerInstance':
                erro('C4-NO-DESCRIPTION', 'element "%s" has no name' % e['id'])
            if t in ('person', 'system', 'container', 'component') and not str(e.get('description', '')).strip():
                erro('C4-NO-DESCRIPTION', 'element "%s" needs a description: what it is or does, in one sentence' % e['id'])
            if t in ('container', 'component', 'infrastructureNode') and not str(e.get('technology', '')).strip():
                erro('C4-NO-TECHNOLOGY', '%s "%s" needs its technology' % (t, e['id']))
            if e.get('shape') and e['shape'] not in SHAPES:
                erro('C4-SHAPE', 'element "%s" has shape "%s"; use %s' % (e['id'], e['shape'], ', '.join(SHAPES)))
            p = e.get('parent')
            if p is not None and p not in self.el:
                erro('C4-UNKNOWN', 'the parent of "%s" is "%s", which is not an element' % (e['id'], p))
            esperado = {'container': ('system',), 'component': ('container',), 'deploymentNode': ('deploymentNode', None),
                        'infrastructureNode': ('deploymentNode',), 'containerInstance': ('deploymentNode',),
                        'person': (None,), 'system': (None,)}[t]
            if (self.el[p]['type'] if p else None) not in esperado:
                erro('C4-PARENT', '%s "%s" must be inside a %s' % (t, e['id'], ' or '.join(x or 'nothing' for x in esperado)))
            if t == 'deploymentNode' and not p and not e.get('environment'):
                erro('C4-PARENT', 'the top deployment node "%s" needs "environment"' % e['id'])
            if t == 'containerInstance':
                c = e.get('container')
                if c not in self.el or self.el[c]['type'] != 'container':
                    erro('C4-PARENT', 'instance "%s" must name a container in "container"' % e['id'])
        for r in self.rels:
            for k in ('from', 'to'):
                if r.get(k) not in self.el:
                    erro('C4-UNKNOWN', 'a relationship names "%s", which is not an element' % r.get(k))
            if not str(r.get('description', '')).strip():
                erro('C4-NO-DESCRIPTION', 'relationship %s -> %s needs a description: what it does' % (r['from'], r['to']))
            if not str(r.get('technology', '')).strip():
                erro('C4-NO-TECHNOLOGY', 'relationship %s -> %s needs its technology' % (r['from'], r['to']))

    def ambiente(self, i):
        while self.el[i].get('parent'):
            i = self.el[i]['parent']
        return self.el[i].get('environment')


# ------------------------------------------------------------------ vistas

def derivar(M, v, tr):
    """Uma vista vira: árvore de caixas e molduras, arestas (já implícitas e sem repetição) e o que a legenda mostra."""
    t = v.get('type')
    if t not in VISTAS:
        erro('C4-VIEW', 'view "%s" has type "%s"; use %s' % (v.get('key'), t, ', '.join(VISTAS)))
    escopo = v.get('scope')
    if t in ('context', 'container', 'component', 'deployment') and escopo not in M.el:
        erro('C4-VIEW', 'view "%s" needs "scope": the id of the %s' % (v.get('key'), 'container' if t == 'component' else 'system'))
    if t in ('context', 'container', 'deployment') and M.el[escopo]['type'] != 'system':
        erro('C4-VIEW', 'the scope of view "%s" must be a system' % v.get('key'))
    if t == 'component' and M.el[escopo]['type'] != 'container':
        erro('C4-VIEW', 'the scope of view "%s" must be a container' % v.get('key'))
    E = M.S['elements']
    pessoas = [e['id'] for e in E if e['type'] == 'person']
    sistemas = [e['id'] for e in E if e['type'] == 'system']
    moldura, nucleo, nivel = None, [], []
    if t == 'landscape':
        nucleo = pessoas + sistemas
        nivel = nucleo
    elif t == 'context':
        nucleo = [escopo]
        nivel = pessoas + sistemas
    elif t == 'container':
        nucleo = M.filhos(escopo, 'container')
        nivel = pessoas + [s for s in sistemas if s != escopo] + nucleo
        moldura = escopo
    elif t == 'component':
        sistema = M.el[escopo]['parent']
        nucleo = M.filhos(escopo, 'component')
        nivel = pessoas + [s for s in sistemas if s != sistema] + [c for c in M.filhos(sistema, 'container') if c != escopo] + nucleo
        moldura = escopo

    arestas, visiveis = [], []
    if t in ('landscape', 'context', 'container', 'component'):
        em_nivel = set(nivel)

        def rep(i):
            for x in [i] + M.ancestrais(i):
                if x in em_nivel:
                    return x
            return None
        nuc = set(nucleo)
        vistos = {}
        for r in M.rels:
            a, b = rep(r['from']), rep(r['to'])
            if not a or not b or a == b:
                continue
            if t != 'landscape' and a not in nuc and b not in nuc:
                continue
            direta = a == r['from'] and b == r['to']
            k = (a, b)
            if k not in vistos or (direta and not vistos[k]['_direta']):
                vistos[k] = dict(r, **{'from': a, 'to': b, '_direta': direta})
        arestas = list(vistos.values())
        usados = set(nucleo) | {x for r in arestas for x in (r['from'], r['to'])}
        visiveis = [i for i in nivel if i in usados]
        if t == 'landscape':
            visiveis = nivel[:]
    elif t == 'dynamic':
        passos = v.get('steps') or []
        for n, p in enumerate(passos, 1):
            for k in ('from', 'to'):
                if p.get(k) not in M.el:
                    erro('C4-UNKNOWN', 'step %d of view "%s" names "%s", which is not an element' % (n, v.get('key'), p.get(k)))
            r = dict(p)
            if not r.get('technology') or not r.get('description'):
                igual = next((x for x in M.rels if x['from'] == p['from'] and x['to'] == p['to']), None)
                if igual:
                    r.setdefault('technology', igual['technology'])
                    r.setdefault('description', igual['description'])
            if not str(r.get('description', '')).strip():
                erro('C4-NO-DESCRIPTION', 'step %d of view "%s" needs a description' % (n, v.get('key')))
            if not str(r.get('technology', '')).strip():
                erro('C4-NO-TECHNOLOGY', 'step %d of view "%s" needs its technology' % (n, v.get('key')))
            r['_n'] = n
            arestas.append(r)
            for k in ('from', 'to'):
                if r[k] not in visiveis:
                    visiveis.append(r[k])
        if escopo:
            if escopo not in M.el:
                erro('C4-UNKNOWN', 'the scope of view "%s" is "%s", which is not an element' % (v.get('key'), escopo))
            if any(escopo in M.ancestrais(i) for i in visiveis):
                moldura = escopo
    elif t == 'deployment':
        amb = v.get('environment')
        nos = [e['id'] for e in E if e['type'] in ('deploymentNode', 'infrastructureNode', 'containerInstance') and M.ambiente(e['id']) == amb]
        if not nos:
            erro('C4-VIEW', 'view "%s": no deployment node in environment "%s"' % (v.get('key'), amb))
        inst = {e['id']: e['container'] for e in E if e['type'] == 'containerInstance' and e['id'] in nos
                and M.el[e['container']].get('parent') == escopo}
        folhas = [i for i in nos if M.el[i]['type'] == 'infrastructureNode'] + list(inst)
        por_cont = {}
        for i, c in inst.items():
            por_cont.setdefault(c, []).append(i)
        vistos = set()
        for r in M.rels:
            if r['from'] in folhas and r['to'] in folhas:
                arestas.append(dict(r))
                continue

            def cont(i):
                for x in [i] + M.ancestrais(i):
                    if x in por_cont:
                        return x
                return None
            a, b = cont(r['from']), cont(r['to'])
            if a and b and a != b:
                for ia in por_cont[a]:
                    for ib in por_cont[b]:
                        if (ia, ib) not in vistos:
                            vistos.add((ia, ib))
                            arestas.append(dict(r, **{'from': ia, 'to': ib}))
        visiveis = folhas
        # só os nós que levam a alguma folha
        com_folha = {a for f in folhas for a in M.ancestrais(f)}
        d_nos = [i for i in nos if M.el[i]['type'] == 'deploymentNode' and i in com_folha]

    inc, exc = v.get('include'), set(v.get('exclude') or [])
    for i in list(inc or []) + list(exc):
        if i not in M.el:
            erro('C4-UNKNOWN', 'view "%s" includes or excludes "%s", which is not an element' % (v.get('key'), i))
    if inc:
        manter = set(inc) | set(nucleo)
        visiveis = [i for i in visiveis if i in manter]
    visiveis = [i for i in visiveis if i not in exc]
    arestas = [r for r in arestas if r['from'] in visiveis and r['to'] in visiveis]
    if not visiveis:
        erro('C4-VIEW', 'view "%s" has nothing to draw' % v.get('key'))
    out = {'tipo': t, 'moldura': moldura, 'caixas': visiveis, 'arestas': arestas, 'escopo': escopo}
    if t == 'deployment':
        out['_nos'] = d_nos
    return out


# ------------------------------------------------------------------ caixas

def classe(M, i, d):
    e = M.el[i]
    t = e['type']
    if t == 'containerInstance':
        e = M.el[e['container']]
        t = 'container'
    cls = ['bchip', 'c4']
    if t == 'person':
        cls.append('pessoa')
    elif t == 'system':
        if d['tipo'] == 'landscape' and not e.get('external'):
            cls.append('outro')  # na paisagem não há foco: todo sistema da empresa tem a mesma caixa
        elif d['tipo'] in ('context', 'dynamic') and i == d['escopo']:
            cls.append('foco')
        elif e.get('external'):
            cls.append('externo')
        else:
            cls.append('outro')
    elif t == 'component':
        cls += ['comp', 'parte']
    elif t == 'container':
        cls.append('parte')  # contêineres e componentes são partes do sistema em foco: a cor dele
    elif t == 'infrastructureNode':
        cls.append('infra')
    if e.get('shape') == 'database':
        cls.append('banco')
    elif e.get('shape') in ('web', 'queue', 'mobile'):
        cls.append({'web': 'web', 'queue': 'fila', 'mobile': 'movel'}[e['shape']])
    return ' '.join(cls)


def tipo_txt(M, i, tr):
    e = M.el[i]
    t = e['type']
    if t == 'containerInstance':
        e, t = M.el[e['container']], 'container'
    if t == 'person':
        return tr['c4.tipo.pessoa']
    if t == 'system':
        base = tr['c4.tipo.externo'] if e.get('external') else tr['c4.tipo.sistema']
        return base + (' · ' + e['owner'] if e.get('owner') else '')
    return {'container': tr['c4.tipo.conteiner'], 'component': tr['c4.tipo.componente'],
            'infrastructureNode': tr['c4.tipo.infra']}[t] + ' · ' + e['technology']


def caixa_html(M, i, d, tr, drill, style):
    e = M.el[i]
    base = M.el[e['container']] if e['type'] == 'containerInstance' else e
    icon = '\n    <img src="%s">' % esc(base['icon']) if base.get('icon') else ''
    desc = base.get('description') or e.get('description') or ''
    bs = '\n    <div class="bs">%s</div>' % esc(desc) if desc else ''
    dr = ''
    if drill:
        dr = '\n    <a class="drill" href="%s">%s</a>' % (esc(drill[0]), esc(tr['c4.ver'].replace('{vista}', drill[1])))
    return ('  <div class="%s" style="%s">%s\n    <div class="bn">%s</div>\n    <div class="bt">%s</div>%s%s\n  </div>'
            % (classe(M, i, d), style, icon, esc(tipo_txt(M, i, tr)), esc(base['name']), bs, dr))


def largura(M, i):
    t = M.el[i]['type']
    return PERSON_W if t == 'person' else INFRA_W if t == 'infrastructureNode' else BOX_W


def rel_html(r, style, edge, lado=''):
    n = '<span class="rn">%d</span>' % r['_n'] if r.get('_n') else ''
    # ao lado de uma seta vertical, o texto encosta no lado da seta
    st = style + {'esq': ';align-items:flex-end;text-align:right', 'dir': ';align-items:flex-start;text-align:left'}.get(lado, '')
    return ('  <div class="rel" data-edge="%d" style="%s">%s<span class="rd">%s</span><span class="rt">[%s]</span></div>'
            % (edge, st, n, esc(r['description']), esc(r['technology'])))


_MEDIDAS = {}


def medir(amostras):
    """Tamanho de cada amostra (caixa na largura fixa, rótulo até REL_MAX, nome de moldura), medido no Chrome com o
    tema padrão. Guarda o que já mediu: o gerar() manda as amostras de todas as vistas numa chamada só."""
    import theme as tema, poster_lint
    faltam = [h for h in dict.fromkeys(amostras) if h not in _MEDIDAS]
    if faltam:
        chrome = poster_lint.find_chrome()
        if not chrome:
            sys.exit('C4 FAILED NO-CHROME: the C4 layout measures boxes and labels in Chrome; install it or set POSTER_CHROME')
        corpo = []
        for k, h in enumerate(faltam):
            alvo = '<div class="flabel"' if '<div class="flabel"' in h else '<div class="'
            corpo.append(h.replace(alvo, alvo.replace('<div ', '<div data-m="m%d" ' % k), 1))
        pagina = ('<!doctype html><html><head><meta charset="utf-8"><style>%s</style></head><body><div class="page">'
                  '<div class="canvas" style="width:6000px;height:6000px">\n%s\n</div></div><script>'
                  'window.addEventListener("load",function(){document.fonts.ready.then(function(){var o={};'
                  'document.querySelectorAll("[data-m]").forEach(function(el){var r=el.getBoundingClientRect();'
                  'o[el.getAttribute("data-m")]=[r.width,r.height]});document.body.setAttribute("data-medida",JSON.stringify(o))})});'
                  '</script></body></html>') % (tema.MARCADOR, '\n'.join(corpo))
        css = open(os.path.join(AQUI, '..', 'assets', 'style.css')).read()
        pagina = tema.aplicar(pagina, css, tema.tema('ai-diagrams'))
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
            f.write(pagina)
            tmp = f.name
        try:
            r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=5000',
                                '--dump-dom', 'file://' + tmp], capture_output=True, timeout=180)
        finally:
            os.unlink(tmp)
        m = re.search(r'data-medida="([^"]+)"', r.stdout.decode())
        if not m:
            sys.exit('C4 FAILED MEASURE-FAILED: Chrome did not return the sizes of boxes and labels')
        medida = json.loads(html.unescape(m.group(1)))
        for k, h in enumerate(faltam):
            _MEDIDAS[h] = medida['m%d' % k]
    return [_MEDIDAS[h] for h in amostras]


def amostras(M, S, v, d, tr, base, principal):
    """O que a vista desenha antes de ter posição: drill-downs, nomes de moldura e as amostras a medir."""
    fundo = {}
    for w in S['views']:
        if w['type'] in ('container', 'component'):
            fundo.setdefault(w['scope'], w)
    drills = {}
    for i in d['caixas']:
        alvo = fundo.get(i)
        if alvo and alvo['key'] != v['key'] and M.el[i]['type'] in ('system', 'container'):
            drills[i] = (arquivo_de(base, alvo, principal), tr['c4.vista.' + alvo['type']].replace(' de {nome}', '').replace(' of {nome}', ''))
    nomes = {}
    if d['moldura']:
        e = M.el[d['moldura']]
        nomes[d['moldura']] = '%s · %s' % (e['name'], tr['c4.foco'] if e['type'] == 'system' else tr['c4.conteiner_foco'])
    for n in d.get('_nos', []):
        e = M.el[n]
        nomes[n] = e['name'] + (' · ' + e['technology'] if e.get('technology') else '') + (' · ×%d' % e['instances'] if e.get('instances', 1) > 1 else '')
    cx = [caixa_html(M, i, d, tr, drills.get(i), 'left:0;top:0;width:%dpx' % largura(M, i)) for i in d['caixas']]
    rl = [rel_html(r, 'left:0;top:0;max-width:%dpx' % REL_MAX, 0) for r in d['arestas']]
    fr = ['<div class="frame limite" style="left:0;top:0;width:10px;height:10px"><div class="flabel">%s</div></div>' % esc(x)
          for x in nomes.values()]
    return drills, nomes, cx, rl, fr


def grafo(M, d, tam, rel_tam, variante, rotulo_w=None):
    direcao, ordem, colocacao, extremos, folga = variante
    filhos_de = {}
    raiz = []

    def node(i):
        w, h = tam[i]
        n = {'id': i, 'width': w, 'height': h}
        lo = {}
        e = M.el[i]
        if extremos and d['tipo'] in ('landscape', 'context', 'container', 'component', 'dynamic'):
            sai = any(r['from'] == i for r in d['arestas'])
            entra = any(r['to'] == i for r in d['arestas'])
            if e['type'] == 'person' or (sai and not entra and i not in nucleo_de(d, M)):
                lo['elk.layered.layering.layerConstraint'] = 'FIRST'
            elif entra and not sai and e['type'] == 'system' and i != d['escopo']:
                lo['elk.layered.layering.layerConstraint'] = 'LAST'
        elif e['type'] == 'person':
            lo['elk.layered.layering.layerConstraint'] = 'FIRST'
        if lo:
            n['layoutOptions'] = lo
        return n

    def frame(fid, filhos, pad):
        # folga dos lados para o nome caber ao lado da seta que entra ou sai pelo meio da borda
        # (o elkjs não respeita largura mínima de nó com filhos quando a hierarquia é única)
        lado = 34
        if len(filhos) == 1 and 'children' not in filhos[0]:
            miolo = max(f['width'] for f in filhos)
            lado = max(34, math.ceil((2 * (rotulo_w or {}).get(fid, 0) + 48 - miolo) / 2))
        return {'id': '__f_' + fid, 'children': filhos, 'layoutOptions': {
            'elk.padding': '[top=%d,left=%d,bottom=%d,right=%d]' % (pad[0], lado, pad[1], lado)}}

    if d['tipo'] == 'deployment':
        nos = d['_nos']
        def monta(pai):
            out = []
            for i in nos + d['caixas']:
                if M.el[i].get('parent') == pai:
                    if i in nos:
                        out.append(frame(i, monta(i), (44, 44)))
                    else:
                        out.append(node(i))
            return out
        raiz = [n for i in nos if not M.el[i].get('parent') for n in [frame(i, monta(i), (44, 44))]]
    else:
        dentro = [node(i) for i in d['caixas'] if d['moldura'] and d['moldura'] in M.ancestrais(i)]
        fora = [node(i) for i in d['caixas'] if not (d['moldura'] and d['moldura'] in M.ancestrais(i))]
        raiz = fora + ([frame(d['moldura'], dentro, (34, 52))] if dentro else [])
    edges = []
    for k, r in enumerate(d['arestas']):
        w, h = rel_tam[k]
        a, b = (r['to'], r['from']) if invertida(M, d, k) else (r['from'], r['to'])
        edges.append({'id': ('i%d' if a != r['from'] else 'e%d') % k, 'sources': [a], 'targets': [b],
                      'labels': [{'id': 'l%d' % k, 'width': w + 8, 'height': h + 8, 'text': 'x'}]})
    entre, gap = 56 + 30 * folga, 64 + 20 * folga
    return {'id': 'root', 'children': raiz, 'edges': edges, 'layoutOptions': {
        'elk.algorithm': 'layered', 'elk.direction': direcao,
        'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
        'elk.json.edgeCoords': 'ROOT', 'elk.json.shapeCoords': 'ROOT',
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.layered.considerModelOrder.strategy': ordem,
        'elk.layered.nodePlacement.strategy': colocacao,
        'elk.layered.crossingMinimization.thoroughness': '30',
        'elk.spacing.nodeNode': str(gap), 'elk.layered.spacing.nodeNodeBetweenLayers': str(entre),
        'elk.spacing.edgeEdge': '26', 'elk.spacing.edgeNode': '32',
        'elk.layered.spacing.edgeEdgeBetweenLayers': '26', 'elk.layered.spacing.edgeNodeBetweenLayers': '32',
        'elk.spacing.edgeLabel': '6', 'elk.edgeLabels.placement': 'CENTER',
        'elk.padding': '[top=16,left=16,bottom=16,right=16]'}}


def nucleo_de(d, M):
    if d['moldura']:
        return {i for i in d['caixas'] if d['moldura'] in M.ancestrais(i)}
    return {d['escopo']} if d['escopo'] else set()


def invertida(M, d, k):
    """Volta (resposta a uma pessoa, ou o caminho inverso de uma relação já desenhada) entra no layout no sentido
    da ida: fica paralela a ela em vez de dar a volta por fora; a seta continua apontando para o destino real."""
    r = d['arestas'][k]
    if M.el[r['to']]['type'] == 'person' and M.el[r['from']]['type'] != 'person':
        return True
    return any(x['from'] == r['to'] and x['to'] == r['from'] for x in d['arestas'][:k])


def caminhos(L):
    """Pontos de cada aresta, na ordem de d['arestas'], com as seções emendadas."""
    out = {}
    for a in L['edges']:
        pts = []
        for s in a.get('sections', []):
            seq = [s['startPoint']] + s.get('bendPoints', []) + [s['endPoint']]
            for p in seq:
                q = [p['x'], p['y']]
                if not pts or abs(pts[-1][0] - q[0]) > .01 or abs(pts[-1][1] - q[1]) > .01:
                    pts.append(q)
        out[int(a['id'][1:])] = pts[::-1] if a['id'][0] == 'i' else pts
    return [out[k] for k in sorted(out)]


def posicoes(L):
    pos = {}
    def walk(n):
        for c in n.get('children', []):
            pos[c['id']] = c
            walk(c)
    walk(L)
    return pos


def ajusta_pessoas(M, pos, linhas):
    """A cabeça fica no alto do nó da pessoa: a seta que chega ou sai por cima vai até o corpo, ao lado da cabeça."""
    for pts in linhas:
        for fim in (0, -1):
            x, y = pts[fim]
            for i, p in pos.items():
                if i in M.el and M.el[i]['type'] == 'person' and abs(y - p['y']) < .5 and p['x'] <= x <= p['x'] + p['width']:
                    cx = p['x'] + p['width'] / 2
                    corpo = p['y'] + HEAD_OFF
                    viz = pts[1] if fim == 0 else pts[-2]
                    if abs(x - cx) < HEAD / 2 + 10:
                        nx = cx + (HEAD / 2 + 26) * (1 if x >= cx else -1)
                        acima = p['y'] - 16
                        novo = [[x, acima], [nx, acima], [nx, corpo]]
                        if abs(viz[0] - x) < .5 and viz[1] < acima:
                            if fim == -1:
                                pts[-1:] = novo
                            else:
                                pts[:1] = novo[::-1]
                        else:
                            pts[fim] = [x, corpo]
                    else:
                        pts[fim] = [x, corpo]


def sem_degrau(pts):
    """Tira o degrau de poucos pixels que o roteamento deixa numa seta quase reta: o trecho final passa a seguir
    o anterior (a ponta continua na mesma borda, só desliza um pouco)."""
    k = 1
    while k + 2 < len(pts):
        a, b, c, e = pts[k - 1], pts[k], pts[k + 1], pts[k + 2] if k + 2 < len(pts) else None
        if abs(a[0] - b[0]) < .5 and abs(b[1] - c[1]) < .5 and 0 < abs(b[0] - c[0]) < 10 and k + 2 == len(pts) - 1:
            dx = b[0] - c[0]
            pts[k + 1][0] += dx
            pts[k + 2][0] += dx
            del pts[k:k + 2]
            continue
        k += 1


def cruzamentos(linhas):
    segs = [(k, a, b) for k, pts in enumerate(linhas) for a, b in zip(pts, pts[1:])]
    n = 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            k1, a1, b1 = segs[i]
            k2, a2, b2 = segs[j]
            if k1 == k2:
                continue
            h1, h2 = abs(a1[1] - b1[1]) < .5, abs(a2[1] - b2[1]) < .5
            if h1 == h2:
                continue
            hz, vt = ((a1, b1), (a2, b2)) if h1 else ((a2, b2), (a1, b1))
            x, y = vt[0][0], hz[0][1]
            if min(hz[0][0], hz[1][0]) + 2 < x < max(hz[0][0], hz[1][0]) - 2 and min(vt[0][1], vt[1][1]) + 2 < y < max(vt[0][1], vt[1][1]) - 2:
                n += 1
    return n


def colados(linhas):
    """Trechos de setas diferentes na mesma linha, um emendando no outro (folga menor que 16px): lidos como uma seta só."""
    segs = [(k, a, b) for k, pts in enumerate(linhas) for a, b in zip(pts, pts[1:])]
    n = 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            k1, a1, b1 = segs[i]
            k2, a2, b2 = segs[j]
            if k1 == k2:
                continue
            for ax in (0, 1):
                o = 1 - ax
                if abs(a1[o] - b1[o]) < .5 and abs(a2[o] - b2[o]) < .5 and abs(a1[o] - a2[o]) < 3:
                    lo1, hi1 = sorted((a1[ax], b1[ax]))
                    lo2, hi2 = sorted((a2[ax], b2[ax]))
                    if max(lo1, lo2) - min(hi1, hi2) < 16:
                        n += 1
    return n


class SemEspaco(Exception):
    pass


def sobrepoe(r1, r2):
    return r1[0] < r2[2] and r2[0] < r1[2] and r1[1] < r2[3] and r2[1] < r1[3]


def seg_ret(p, q, pad=0):
    return (min(p[0], q[0]) - pad, min(p[1], q[1]) - pad, max(p[0], q[0]) + pad, max(p[1], q[1]) + pad)


def coloca_rotulos(caixas, molduras, linhas, rel_tam, elk_rot=None):
    """Quando um rótulo fica sem lugar porque outro tomou o espaço dele, tenta de novo com ele na frente."""
    ordem = list(range(len(linhas)))
    for _ in range(len(linhas) + 1):
        try:
            return _coloca_rotulos(caixas, molduras, linhas, rel_tam, elk_rot, ordem)
        except SemEspaco as e:
            if e.args[0] == ordem[0] or e.args[0] == 'frame':
                raise
            ordem.remove(e.args[0])
            ordem.insert(0, e.args[0])
    raise SemEspaco(ordem[0])


def _coloca_rotulos(caixas, molduras, linhas, rel_tam, elk_rot, ordem):
    """Cada rótulo vai em cima da própria seta, no trecho livre mais longo; sem trecho livre, ao lado dela.
    Não encosta em caixa, borda de moldura, outra seta nem outro rótulo."""
    obst = [(x1 - 6, y1 - 6, x2 + 6, y2 + 6) for x1, y1, x2, y2 in caixas]
    for x1, y1, x2, y2 in molduras:
        obst += [(x1 - 5, y1 - 5, x2 + 5, y1 + 5), (x1 - 5, y2 - 5, x2 + 5, y2 + 5),
                 (x1 - 5, y1 - 5, x1 + 5, y2 + 5), (x2 - 5, y1 - 5, x2 + 5, y2 + 5)]
    postos, saida = [], {}
    for k in ordem:
        pts = linhas[k]
        w, h = rel_tam[k]
        w, h = w + 2, h + 2
        own = list(zip(pts, pts[1:]))
        ordem = sorted(own, key=lambda pq: -(abs(pq[0][0] - pq[1][0]) + abs(pq[0][1] - pq[1][1])))
        achou = None
        for lado in ('on', 'beside'):
            for p, q in ordem:
                comp = abs(p[0] - q[0]) + abs(p[1] - q[1])
                vertical = abs(p[0] - q[0]) < 1
                if comp < 24:
                    continue
                for off in [0] + [s * sg for s in range(6, int(comp / 2), 6) for sg in (1, -1)]:
                    t = .5 + off / comp
                    cx, cy = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                    if lado == 'on':
                        cand = [(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)]
                        # a seta precisa aparecer antes e depois do rótulo
                        if vertical and (min(p[1], q[1]) + 10 > cy - h / 2 or max(p[1], q[1]) - 10 < cy + h / 2):
                            continue
                        if not vertical and (min(p[0], q[0]) + 10 > cx - w / 2 or max(p[0], q[0]) - 10 < cx + w / 2):
                            continue
                    elif vertical:
                        cand = [(cx + 10, cy - h / 2, cx + 10 + w, cy + h / 2, 'dir'), (cx - 10 - w, cy - h / 2, cx - 10, cy + h / 2, 'esq')]
                    else:
                        cand = [(cx - w / 2, cy - h - 8, cx + w / 2, cy - 8), (cx - w / 2, cy + 8, cx + w / 2, cy + 8 + h)]
                    for rc in cand:
                        if any(sobrepoe(rc, b) for b in obst) or any(sobrepoe(rc, b) for b in postos):
                            continue
                        if any(sobrepoe(rc, seg_ret(a, b, 4)) for k2, pts2 in enumerate(linhas) if k2 != k for a, b in zip(pts2, pts2[1:])):
                            continue
                        if lado == 'beside' and any(sobrepoe(rc, seg_ret(a, b, 4)) for a, b in own):
                            continue
                        achou = rc
                        break
                    if achou:
                        break
                if achou:
                    break
            if achou:
                break
        if not achou and elk_rot and elk_rot[k]:
            # último recurso: o lugar que o próprio elkjs reservou para o rótulo, se continua livre e junto da seta
            x, y = elk_rot[k]
            rc = (x + 4 - 1, y + 4 - 1, x + 4 + w - 1, y + 4 + h - 1)
            perto = min(math.hypot(max(rc[0] - max(a[0], b[0]), 0, min(a[0], b[0]) - rc[2]),
                                   max(rc[1] - max(a[1], b[1]), 0, min(a[1], b[1]) - rc[3])) for a, b in own)
            if perto <= 12 and not any(sobrepoe(rc, b) for b in obst) and not any(sobrepoe(rc, b) for b in postos) \
                    and not any(sobrepoe(rc, seg_ret(a, b, 4)) for k2, pts2 in enumerate(linhas) if k2 != k for a, b in zip(pts2, pts2[1:])):
                achou = rc
        if not achou:
            raise SemEspaco(k)
        postos.append((achou[0] - 6, achou[1] - 6, achou[2] + 6, achou[3] + 6))
        saida[k] = (achou[0] + 1, achou[1] + 1, achou[4] if len(achou) > 4 else '')
    return [saida[k] for k in range(len(linhas))]


def coloca_nome_moldura(fr, texto_w, linhas, caixas, outros, topo_primeiro):
    """Rótulo da moldura no primeiro trecho da borda (de baixo ou de cima) sem seta nem caixa."""
    x0, y0, x1, y1 = fr
    th = 22
    alvos = [('top', y0 + 6), ('bottom', y1 - 6 - th)]
    if not topo_primeiro:
        alvos.reverse()
    segs = [seg_ret(a, b, 4) for pts in linhas for a, b in zip(pts, pts[1:])]
    for lado, y in alvos:
        for x in range(R(x0 + 10), R(x1 - 10 - texto_w), 6):
            rc = (x, y, x + texto_w, y + th)
            if any(sobrepoe(rc, s) for s in segs) or any(sobrepoe(rc, (a - 4, b - 4, c + 4, e + 4)) for a, b, c, e in caixas) \
                    or any(sobrepoe(rc, o) for o in outros):
                continue
            return lado, x - x0, rc
    raise SemEspaco('frame')


VARIANTES = [(o, c, x) for x in (True, False) for o in ('NODES_AND_EDGES', 'NONE')
             for c in ('NETWORK_SIMPLEX', 'BRANDES_KOEPF')]
# Which elkjs directions a view tries. "auto" (the default) tries both and the cost prefers a landscape drawing;
# "vertical" is what every view but deployment did before: top to bottom only.
ORIENTACOES = {'horizontal': ('RIGHT',), 'vertical': ('DOWN',), 'auto': ('RIGHT', 'DOWN')}
PAISAGEM = 1.35      # page width / page height that "auto" aims for (slide, book spread, wide monitor)
PESO_RETRATO = 6     # cost per px of page height above page width / PAISAGEM, in "auto"
MOLDURA_PAGINA = 470 # page height around the canvas: header, title, subtitle, legend and footer
LARGURA_MAX = 1660   # wider than this costs 120 per px, in "auto" and "vertical"
LARGURA_MAX_H = 2560 # in "horizontal" the view asked for a wide page (slide, spread): the limit moves here


def orientacao(S, v):
    o = v.get('orientation', S.get('orientation', 'auto'))
    if o not in ORIENTACOES:
        erro('C4-VIEW', 'view "%s" has orientation "%s"; use horizontal, vertical or auto' % (v.get('key'), o))
    return o


def melhor_layout(M, d, tam, rel_tam, rotulo_moldura_w, orient='auto'):
    variantes = [(dr,) + v + (0,) for dr in ORIENTACOES[orient] for v in VARIANTES]
    melhor = None
    for folga in range(4):
        gs = [grafo(M, d, tam, rel_tam, v[:4] + (folga,), rotulo_moldura_w) for v in variantes]
        r = subprocess.run(['node', ELK], input=json.dumps(gs), capture_output=True, text=True)
        if r.returncode:
            sys.exit('C4 FAILED elkjs: ' + r.stderr.strip())
        for v, L in zip(variantes, json.loads(r.stdout)):
            if 'erro' in L:
                continue
            pos = posicoes(L)
            linhas = caminhos(L)
            ajusta_pessoas(M, pos, linhas)
            for pts in linhas:
                sem_degrau(pts)
            caixas = [(p['x'], p['y'] + (HEAD_OFF if M.el[i]['type'] == 'person' else 0), p['x'] + p['width'], p['y'] + p['height'])
                      for i, p in pos.items() if not i.startswith('__f_')]
            fr = {i[4:]: (p['x'], p['y'], p['x'] + p['width'], p['y'] + p['height']) for i, p in pos.items() if i.startswith('__f_')}
            try:
                nomes = {}
                ocupados = []
                for fid, ret in sorted(fr.items(), key=lambda kv: (kv[1][1], kv[1][0])):
                    lado, dx, rc = coloca_nome_moldura(ret, rotulo_moldura_w[fid], linhas, caixas, ocupados,
                                                       topo_primeiro=d['tipo'] == 'deployment')
                    nomes[fid] = (lado, dx)
                    ocupados.append(rc)
                elk_rot = {}
                for a in L['edges']:
                    lb = (a.get('labels') or [{}])[0]
                    elk_rot[int(a['id'][1:])] = (lb['x'], lb['y']) if 'x' in lb else None
                rot = coloca_rotulos(caixas + [(a, b, c, e) for a, b, c, e in ocupados], list(fr.values()), linhas, rel_tam,
                                     [elk_rot.get(k) for k in range(len(linhas))])
            except SemEspaco:
                continue
            curvas = sum(max(len(p) - 2, 0) for p in linhas)
            compr = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for p in linhas for a, b in zip(p, p[1:]))
            W, H = L['width'], L['height']
            custo = cruzamentos(linhas) * 5000 + colados(linhas) * 3000 + curvas * 60 + compr + max(0, W - (LARGURA_MAX_H if orient == 'horizontal' else LARGURA_MAX)) * 120 + W * H / 300
            if orient == 'auto':
                # the page, not the canvas, is what the reader sees: at least 1400 wide, title and legend on top of the canvas
                custo += max(0, H + MOLDURA_PAGINA - max(1400, W + 96) / PAISAGEM) * PESO_RETRATO
            if melhor is None or custo < melhor[0]:
                melhor = (custo, L, pos, linhas, rot, nomes, fr)
        if melhor:
            return melhor
    erro('C4-NO-ROOM', 'no layout of view "%s" leaves room for every label; shorten descriptions or split the view' % d.get('key'))


# ------------------------------------------------------------------ página

def legenda(usados, tr, tipo):
    itens = []
    def it(sw, chave):
        itens.append('<div class="it"><div class="sw %s"></div>%s</div>' % (sw, esc(tr[chave])))
    ordem = [('pessoa', 'pessoa', 'c4.leg.pessoa'), ('foco', 'foco', 'c4.leg.foco'), ('sistema', 'outro', 'c4.leg.sistema'), ('limite', 'limite', 'c4.leg.limite'),
             ('limite_c', 'limite', 'c4.leg.limite_conteiner'), ('dnode', 'dnode', 'c4.leg.no'),
             ('conteiner', 'parte', 'c4.leg.conteiner'), ('web', 'web parte', 'c4.leg.web'), ('movel', 'movel parte', 'c4.leg.movel'),
             ('banco', 'banco parte', 'c4.leg.banco'), ('fila', 'fila parte', 'c4.leg.fila'), ('comp', 'comp parte', 'c4.leg.componente'),
             ('infra', 'infra', 'c4.leg.infra'), ('outro', 'outro', 'c4.leg.outro'), ('externo', 'externo', 'c4.leg.externo'),
             ('drill', 'drill', 'c4.leg.detalhe')]
    for chave, sw, rot in ordem:
        if chave == 'drill' and chave in usados:
            itens.append('<div class="it"><span class="sw drill">%s</span>%s</div>'
                         % (esc(tr['c4.ver'].replace('{vista}', '').replace('  ', ' ').strip()), esc(tr[rot])))
        elif chave in usados:
            it(sw, rot)
    n = '<b>1</b>' if tipo == 'dynamic' else ''
    itens.append('<div class="it"><span class="seta">%s<i></i></span>%s <code>[%s]</code></div>'
                 % (n, esc(tr['c4.leg.passo'] if tipo == 'dynamic' else tr['c4.leg.relacao']), esc(tr['c4.leg.tecnologia'])))
    return '<div class="sec">%s</div>\n<div class="c4leg">\n%s\n</div>' % (esc(tr['c4.legenda']), '\n'.join(itens))


def nome_vista(v, M, tr):
    if v.get('label'):
        return v['label']
    t = v['type']
    if t == 'component':
        return tr['c4.vista.component'].replace('{nome}', M.el[v['scope']]['name'])
    return tr['c4.vista.' + t]


def arquivo_de(base, v, principal):
    return base + ('' if v['key'] == principal else '-' + v['key']) + '.html'


def pagina(M, S, v, d, tr, tm_link, meta, base, principal):
    import theme as tema
    vistas = S['views']
    drills, nomes_moldura, cx, rl, fr_am = amostras(M, S, v, d, tr, base, principal)
    ids = list(d['caixas'])
    mc, mr, mf = medir(cx), medir(rl), medir(fr_am)
    tam = {}
    for i, (w, h) in zip(ids, mc):
        h = math.ceil(h / 2) * 2 + 4
        tam[i] = (largura(M, i), h + (HEAD_OFF if M.el[i]['type'] == 'person' else 0))
    # mesma altura para caixas do mesmo tipo: linhas alinhadas, como na regra do C4 à mão
    # (só entre caixas de altura parecida: igualar a mais alta abriria espaço vazio nas outras)
    for grupo in {classe(M, i, d) for i in tam}:
        membros = [i for i in tam if classe(M, i, d) == grupo]
        alturas = sorted(tam[i][1] for i in membros)
        for i in membros:
            vizinhas = [h for h in alturas if 0 <= h - tam[i][1] <= 20]
            tam[i] = (tam[i][0], max(vizinhas))
    rel_tam = [(math.ceil(w), math.ceil(h)) for w, h in mr]
    fw = {f: math.ceil(w) + 6 for f, (w, h) in zip(nomes_moldura, mf)}

    custo, L, pos, linhas, rot, nomes, fr = melhor_layout(M, d, tam, rel_tam, fw, orientacao(S, v))
    cw, ch = math.ceil(L['width']), math.ceil(L['height'])

    usados = set()
    out = []
    for fid, (x0, y0, x1, y1) in sorted(fr.items(), key=lambda kv: (kv[1][2] - kv[1][0]) * (kv[1][3] - kv[1][1]), reverse=True):
        e = M.el[fid]
        cls = 'frame dnode' if e['type'] == 'deploymentNode' else 'frame limite'
        usados.add('dnode' if e['type'] == 'deploymentNode' else 'limite' if e['type'] == 'system' else 'limite_c')
        lado, dx = nomes[fid]
        lpos = ('top:9px' if lado == 'top' else 'top:auto;bottom:9px') + ';left:%dpx' % R(dx)
        out.append('  <div class="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><div class="flabel" style="%s">%s</div></div>'
                   % (cls, R(x0), R(y0), R(x1 - x0), R(y1 - y0), lpos, esc(nomes_moldura[fid])))
    for i in ids:
        p = pos[i]
        x, y = R(p['x']), R(p['y'])
        w, h = tam[i]
        c = classe(M, i, d).split()
        for k in ('pessoa', 'foco', 'web', 'movel', 'banco', 'fila', 'comp', 'infra', 'outro', 'externo'):
            if k in c:
                usados.add(k)
        if M.el[i]['type'] == 'system' and d['tipo'] == 'landscape' and 'outro' in c:
            usados.add('sistema')  # sem foco, não há "outro": é o sistema da empresa
            usados.discard('outro')
        if M.el[i]['type'] in ('container', 'containerInstance') and not ({'web', 'movel', 'banco', 'fila'} & set(c)):
            usados.add('conteiner')
        if i in drills:
            usados.add('drill')
        if M.el[i]['type'] == 'person':
            out.append(caixa_html(M, i, d, tr, drills.get(i), 'left:%dpx;top:%dpx;width:%dpx;height:%dpx' % (x, y + HEAD_OFF, w, h - HEAD_OFF)))
            out.append('  <div class="c4head" style="left:%dpx;top:%dpx"></div>' % (x + w // 2 - HEAD // 2, y))
        else:
            out.append(caixa_html(M, i, d, tr, drills.get(i), 'left:%dpx;top:%dpx;width:%dpx;height:%dpx' % (x, y, w, h)))
    svg = []
    for pts in linhas:
        dd = 'M%d,%d ' % (R(pts[0][0]), R(pts[0][1])) + ' '.join('L%d,%d' % (R(a), R(b)) for a, b in pts[1:])
        svg.append('    <path d="%s" stroke-width="1.6" fill="none" marker-end="url(#a)" style="stroke:var(--support)"/>' % dd)
    rot_html = [rel_html(r, 'left:%dpx;top:%dpx;width:%dpx' % (R(x), R(y), rel_tam[k][0]), k, lado)
                for k, (r, (x, y, lado)) in enumerate(zip(d['arestas'], rot))]
    edges_svg = ('  <svg class="edges" viewBox="0 0 %d %d">\n    <defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">'
                 '<path d="M0,0 L9,4.5 L0,9 z" style="fill:var(--support)"/></marker></defs>\n%s\n  </svg>') % (cw, ch, '\n'.join(svg))

    nav = []
    for w in vistas:
        nome = nome_vista(w, M, tr)
        if w['key'] == v['key']:
            nav.append('<b>%s</b>' % esc(nome))
        else:
            nav.append('<a href="%s">%s</a>' % (esc(arquivo_de(base, w, principal)), esc(nome)))
    nav_html = '<div class="c4nav"><span class="cn">%s</span>%s</div>' % (esc(tr['c4.vistas']), ''.join(nav)) if len(vistas) > 1 else ''

    passos = ''
    if d['tipo'] == 'dynamic':
        nome = lambda i: (M.el[M.el[i]['container']] if M.el[i]['type'] == 'containerInstance' else M.el[i])['name']
        itens = ''.join('\n<div class="cs"><span class="rn">%d</span><div><b>%s → %s.</b> %s <code>[%s]</code></div></div>'
                        % (r['_n'], esc(nome(r['from'])), esc(nome(r['to'])), esc(r['description']), esc(r['technology']))
                        for r in d['arestas'])
        passos = '<div class="sec">%s</div>\n<div class="c4steps">%s\n</div>\n' % (esc(tr['c4.sequencia']), itens)

    W = max(1400, cw + 96)
    he, hd = S['cabecalho']
    fe, fd = S['rodape']
    titulo = v.get('title') or ((M.el[v['scope']]['name'] + ': ') if v.get('scope') in M.el else '') + nome_vista(v, M, tr)
    return f'''<!doctype html><html lang="{tr['_codigo']}"><head><meta charset="utf-8">
<title>{esc(titulo)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{tm_link}
{meta}<meta name="width" content="{W}">
<style>{tema.MARCADOR}
body{{width:{W}px}}</style></head><body>
<div class="page">

<div class="hdr"><span>{esc(he)}</span><span>{esc(hd)}</span></div>
<div class="kicker"><span class="sq">■</span>&nbsp; {esc(v.get('kicker') or tr['c4.kicker.' + v['type']])}</div>
<h1>{esc(titulo)}</h1>
<div class="sub">{esc(v.get('description', ''))}</div>
{nav_html}

<div class="wrap stack"><div class="canvas" style="width:{cw}px;height:{ch}px">
{chr(10).join(out)}
{edges_svg}
{chr(10).join(rot_html)}
</div></div>

{passos}{legenda(usados, tr, d['tipo'])}

<div class="foot" style="display:flex;justify-content:space-between"><span>{esc(fe)}</span><span>{esc(fd)}</span></div>

</div>
</body></html>
'''


def main():
    sys.path.insert(0, AQUI)
    import theme as tema, lang as idioma, spec
    flag_tema, sys.argv[1:] = tema.tirar_flag(sys.argv[1:])
    flag_idioma, sys.argv[1:] = idioma.tirar_flag(sys.argv[1:])
    construir = '--no-build' not in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    caminho = os.path.abspath(args[0])
    S = spec.ler('c4', json.load(open(caminho)))
    gerar(S, caminho, flag_tema, flag_idioma, construir)


def gerar(S, caminho, flag_tema=None, flag_idioma=None, construir=True, saida_dir=None):
    """Escreve (e, com construir, passa pelo build.py) uma página por vista. Devolve os caminhos dos fontes."""
    import theme as tema, lang as idioma
    tm = tema.tema(flag_tema)
    tr = idioma.idioma(flag_idioma, fonte_json=S)
    M = Modelo(S)
    vistas = S.get('views') or []
    if not vistas:
        erro('C4-VIEW', 'the model has no views; add at least one (container, context, ...)')
    chaves = [v.get('key') for v in vistas]
    if any(not k or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', k) for k in chaves) or len(set(chaves)) != len(chaves):
        erro('C4-VIEW', 'every view needs a unique "key" in lowercase letters, digits and hyphens')
    principal = S.get('main') or next((v['key'] for v in vistas if v['type'] == 'container'), chaves[0])
    if principal not in chaves:
        erro('C4-VIEW', '"main" is "%s", which is not the key of a view' % principal)
    pasta = saida_dir or os.path.dirname(caminho)
    base = os.path.splitext(os.path.basename(caminho))[0]
    feitos = []
    derivadas = []
    todas = []
    for v in vistas:
        d = derivar(M, v, tr)
        d['key'] = v['key']
        derivadas.append(d)
        _, _, cx, rl, fr = amostras(M, S, v, d, tr, base, principal)
        todas += cx + rl + fr
    medir(todas)
    for v, d in zip(vistas, derivadas):
        destino = os.path.join(pasta, arquivo_de(base, v, principal))
        th = tema.para_gerador(tm, destino)
        meta = th['meta'] + '\n' if th['meta'] else ''
        doc = pagina(M, S, v, d, tr, th['link'], meta + idioma.para_gerador(tr), base, principal)
        open(destino, 'w').write(doc)
        print(destino)
        feitos.append(destino)
    if construir:
        extra = (['--theme', flag_tema] if flag_tema else []) + (['--lang', flag_idioma] if flag_idioma else [])
        for f in feitos:
            r = subprocess.run([sys.executable, os.path.join(AQUI, 'build.py'), f] + extra)
            if r.returncode:
                sys.exit(r.returncode)
    return feitos


if __name__ == '__main__':
    main()
