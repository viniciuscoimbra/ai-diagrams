#!/usr/bin/env python3
"""Gera BPMN 2.0 com BPMNDI a partir de um modelo JSON, mais o viewer e o PNG.

Uso: python3 gerar_bpmn.py <modelo.json> [--out DIR] [--so-bpmn] [--tema NOME|caminho.json]
                         [--idioma pt-BR|en|es] [--sem-chrome]

Saída (na pasta pai quando o modelo está em _src/, senão ao lado dele):
  <nome>.bpmn  editável no Camunda Modeler ou em demo.bpmn.io
  <nome>.html  viewer self-contained com bpmn-js (navegável, funciona offline)
  <nome>.png   captura do viewer via Chrome headless

--sem-chrome gera apenas BPMN e HTML com os checks estáticos. Importação no viewer
e captura continuam pendentes; rode sem essa flag para completar o gate.

O layout é calculado: raia é linha, col e row posicionam cada nó, e as conexões
são roteadas em Manhattan desviando de formas e rótulos. A renderização é do
bpmn-js (vendor/, licença em vendor/LICENSE).

Gate (exit 1 em qualquer falha, nada é gravado):
  ESTRUTURA    ids únicos, conexão para nó existente, nó sem entrada (exceto
               início) ou sem saída (exceto fim), decisão com ramo sem rótulo.
  ALCANCE      todo nó é alcançável a partir de um início e alcança um fim.
  SOBREPOSICAO duas formas no mesmo lugar.
  IMPORTACAO   o bpmn-js importa o XML no Chrome sem erro e sem aviso.
  TEXTO-MARKETING  título ou subtítulo com vocabulário de venda (scripts/texto_tecnico.py).
  COR-FORA-DO-TEMA nó com fill próprio; a cor vem do tema.
Formato do modelo em references/bpmn.md.
"""
import sys, os, html, shutil, subprocess, tempfile
from pathlib import Path
import json, math, heapq, re, copy, unicodedata
import xml.etree.ElementTree as E

NS = dict(bpmn='http://www.omg.org/spec/BPMN/20100524/MODEL',
          bpmndi='http://www.omg.org/spec/BPMN/20100524/DI',
          dc='http://www.omg.org/spec/DD/20100524/DC',
          di='http://www.omg.org/spec/DD/20100524/DI',
          bioc='http://bpmn.io/schema/bpmn/biocolor/1.0',
          xsi='http://www.w3.org/2001/XMLSchema-instance')
for k,v in NS.items(): E.register_namespace(k,v)

# Cores e fontes vêm do tema (scripts/tema.py: --tema, AI_DIAGRAMS_TEMA ou ai-diagrams). O CSS do viewer
# usa var(--…) e recebe o :root do tema; o XML guarda o valor direto, porque o bpmn-js grava bioc:fill e
# bioc:stroke como atributo SVG, que não aceita var(). O tema só muda cor e fonte: a geometria (DI) é a mesma.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import tema as _tema
import idioma as _idioma
TEMA = {}
def tag(p,n): return '{'+NS[p]+'}'+n
def sub(parent, n, attrs=None, text=None, p='bpmn'):
    e=E.SubElement(parent,tag(p,n),{k:str(v) for k,v in (attrs or {}).items()})
    if text is not None: e.text=str(text)
    return e
def bounds(parent, r):
    return sub(parent,'Bounds',dict(zip(('x','y','width','height'),r)),p='dc')

def overlap(a,b,pad=0):
    return a[0]<b[0]+b[2]+pad and a[0]+a[2]>b[0]-pad and a[1]<b[1]+b[3]+pad and a[1]+a[3]>b[1]-pad

def route(a,b, obstacles, used, W,H, via=None,track=0):
    # Manhattan routing around native shapes and their external label bounds.
    ports=lambda r:[(r[0]+r[2],r[1]+r[3]/2,0),(r[0]+r[2]/2,r[1]+r[3],1),
                    (r[0],r[1]+r[3]/2,2),(r[0]+r[2]/2,r[1],3)]
    dirs=[(1,0),(0,1),(-1,0),(0,-1)]
    grid=10
    def cell(x,y):return (round(x/grid),round(y/grid))
    blocked=set()
    for r in obstacles:
        x,y,w,h=r
        for gx in range(math.floor((x-9)/grid),math.ceil((x+w+9)/grid)+1):
            for gy in range(math.floor((y-9)/grid),math.ceil((y+h+9)/grid)+1):
                blocked.add((gx,gy))
    starts=[]; targets={}
    for x,y,d in ports(a):
        if via=='top' and d!=3:continue
        if via=='bottom' and d!=1:continue
        dx,dy=dirs[d]; c=cell(x+dx*20,y+dy*20)
        if c not in blocked:starts.append((c,d,(x,y)))
    for x,y,d in ports(b):
        dx,dy=dirs[d];c=cell(x+dx*20,y+dy*20)
        if c not in blocked: targets[c]=(x,y,d)
    # Prefer flowing right; the search may choose vertical ports to keep lanes clean.
    heap=[]; dist={}; prev={}; seed={}
    def heuristic(c):return min(abs(c[0]-t[0])+abs(c[1]-t[1]) for t in targets)*10
    for c,d,p in starts:
        st=(*c,d); cost=0 if d in (0,1) else 12
        dist[st]=cost;seed[st]=p;heapq.heappush(heap,(cost+heuristic(c),cost,st))
    found=None
    while heap:
        _,cost,s=heapq.heappop(heap)
        if cost!=dist.get(s):continue
        x,y,d=s
        if (x,y) in targets:
            found=s;break
        for nd,(dx,dy) in enumerate(dirs):
            nx,ny=x+dx,y+dy
            if not (12<=nx<=W//grid and 2<=ny<=H//grid) or (nx,ny) in blocked:continue
            extra=10+(22 if nd!=d else 0)+used.get((nx,ny),0)*18
            ns=(nx,ny,nd);nc=cost+extra
            if nc<dist.get(ns,1e15):
                dist[ns]=nc;prev[ns]=s;seed[ns]=seed[s]
                heapq.heappush(heap,(nc+heuristic((nx,ny)),nc,ns))
    if found is None:
        if via:return route(a,b,obstacles,used,W,H,None,track)
        raise ValueError(f'No route {a} → {b}, via={via}')
    pts=[];s=found
    while True:
        pts.append((s[0]*grid,s[1]*grid))
        if s not in prev:break
        s=prev[s]
    pts.reverse(); pts=[seed[found]]+pts+[targets[found[:2]][:2]]
    clean=[]
    for p in pts:
        if clean and p==clean[-1]:continue
        if len(clean)>1 and ((clean[-2][0]==clean[-1][0]==p[0]) or (clean[-2][1]==clean[-1][1]==p[1])):clean.pop()
        clean.append(p)
    for (x,y),(xx,yy) in zip(clean,clean[1:]):
        steps=max(abs(round(xx-x)),abs(round(yy-y)))//grid
        for j in range(steps+1):
            k=cell(x+(xx-x)*j/max(steps,1),y+(yy-y)*j/max(steps,1)); used[k]=used.get(k,0)+1
    return clean

def label_box(points,name,obstacles,labels):
    w=min(178,max(56,len(name)*7)); h=22*math.ceil(len(name)*7/w)
    candidates=[]
    for index,((x,y),(xx,yy)) in enumerate(zip(points,points[1:])):
        length=abs(xx-x)+abs(yy-y)
        if y==yy:
            for f in (.5,.25,.75):
                candidates += [((x+(xx-x)*f-w/2,y-h-7,w,h),max(0,w+10-length)*100+index*2),((x+(xx-x)*f-w/2,y+7,w,h),max(0,w+10-length)*100+index*2)]
        else:
            candidates += [((x+8,(y+yy-h)/2,w,h),max(0,h+10-length)*100+index*2),((x-w-8,(y+yy-h)/2,w,h),max(0,h+10-length)*100+index*2)]
    def score(candidate):
        r,penalty=candidate
        return sum(10000 for b in obstacles if overlap(r,b,3))+sum(1000 for b in labels if overlap(r,b,3))+penalty
    box=min(candidates,key=score)[0];labels.append(box);return box


def falha(msg):
    sys.exit('BPMN REPROVOU: ' + msg)


def checar(m):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
    import texto_tecnico as tt
    for termo, trecho in tt.marketing([m.get('title', ''), m.get('subtitle', '')]):
        falha('TEXTO-MARKETING "%s" em "%s": %s' % (termo, trecho, tt.MENSAGEM))
    ids = [n['id'] for n in m['nodes']]
    if len(ids) != len(set(ids)):
        falha('ESTRUTURA ids repetidos')
    lookup = {n['id']: n for n in m['nodes']}
    lanes = {l['id'] for l in m['lanes']}
    tipos = {'startEvent', 'endEvent', 'task', 'callActivity', 'exclusiveGateway', 'parallelGateway',
             'intermediateCatchEvent', 'intermediateThrowEvent'}
    for n in m['nodes']:
        if n['type'] not in tipos:
            falha('ESTRUTURA tipo %s não suportado em %s' % (n['type'], n['id']))
        if n['lane'] not in lanes:
            falha('ESTRUTURA raia %s inexistente em %s' % (n['lane'], n['id']))
        if 'fill' in n:
            falha('COR-FORA-DO-TEMA %s define fill; a cor do nó vem do tema' % n['id'])
    for f in m['flows']:
        if f['from'] not in lookup or f['to'] not in lookup:
            falha('ESTRUTURA conexão para nó inexistente: %s -> %s' % (f['from'], f['to']))
    for n in m['nodes']:
        ent = [f for f in m['flows'] if f['to'] == n['id']]
        sai = [f for f in m['flows'] if f['from'] == n['id']]
        if not ent and n['type'] != 'startEvent':
            falha('ESTRUTURA %s sem entrada' % n['id'])
        if not sai and n['type'] != 'endEvent':
            falha('ESTRUTURA %s sem saída' % n['id'])
        if n['type'] == 'exclusiveGateway' and len(sai) > 1 and not all(f.get('name') for f in sai):
            falha('ESTRUTURA decisão %s tem ramo sem rótulo' % n['id'])

    def alcance(inicio, reverso=False):
        visto = set(inicio)
        fila = list(inicio)
        while fila:
            x = fila.pop()
            for f in m['flows']:
                a, b = (f['to'], f['from']) if reverso else (f['from'], f['to'])
                if a == x and b not in visto:
                    visto.add(b)
                    fila.append(b)
        return visto
    if alcance([n['id'] for n in m['nodes'] if n['type'] == 'startEvent']) != set(ids):
        falha('ALCANCE há nó que nenhum início alcança')
    if alcance([n['id'] for n in m['nodes'] if n['type'] == 'endEvent'], True) != set(ids):
        falha('ALCANCE há nó que não chega a nenhum fim')


def emitir(m):
    pid = m['id']
    prefix = lambda x: pid + '_' + x
    definitions = E.Element(tag('bpmn', 'definitions'), {
        'id': 'Definitions_' + pid, 'targetNamespace': 'http://bpmn.io/schema/bpmn',
        'exporter': 'ai-diagrams', 'exporterVersion': '1'})
    collab = sub(definitions, 'collaboration', {'id': prefix('collaboration')})
    sub(collab, 'participant', {'id': prefix('pool'), 'name': m['title'], 'processRef': pid})
    proc = sub(definitions, 'process', {'id': pid, 'name': m['title'], 'isExecutable': 'false'})
    if m.get('subtitle'):
        sub(proc, 'documentation', text=m['subtitle'])
    laneset = sub(proc, 'laneSet', {'id': prefix('lanes')})
    laneels = {l['id']: sub(laneset, 'lane', {'id': prefix(l['id']), 'name': l['name']}) for l in m['lanes']}
    incoming = {n['id']: [] for n in m['nodes']}
    outgoing = {n['id']: [] for n in m['nodes']}
    for j, f in enumerate(m['flows']):
        f['_id'] = prefix('f' + str(j + 1))
        outgoing[f['from']].append(f['_id'])
        incoming[f['to']].append(f['_id'])
    for n in m['nodes']:
        attrs = {'id': prefix(n['id']), 'name': n.get('name', '')}
        if n['type'] in ('exclusiveGateway', 'parallelGateway'):
            attrs['gatewayDirection'] = 'Diverging' if len(outgoing[n['id']]) > 1 else 'Converging'
        el = sub(proc, n['type'], attrs)
        if n.get('doc'):
            sub(el, 'documentation', text=n['doc'] if isinstance(n['doc'], str) else json.dumps(n['doc'], ensure_ascii=False, indent=2))
        for fid in incoming[n['id']]:
            sub(el, 'incoming', text=fid)
        for fid in outgoing[n['id']]:
            sub(el, 'outgoing', text=fid)
        if n.get('event') == 'timer':
            sub(el, 'timerEventDefinition', {'id': prefix(n['id'] + '_timer')})
        if n.get('event') == 'message':
            sub(el, 'messageEventDefinition', {'id': prefix(n['id'] + '_msg')})
        if n.get('event') == 'condition':
            ev = sub(el, 'conditionalEventDefinition', {'id': prefix(n['id'] + '_condition')})
            sub(ev, 'condition', {tag('xsi', 'type'): 'bpmn:tFormalExpression'}, text=n.get('condition', n['name']))
        sub(laneels[n['lane']], 'flowNodeRef', text=prefix(n['id']))
    for f in m['flows']:
        attrs = {'id': f['_id'], 'sourceRef': prefix(f['from']), 'targetRef': prefix(f['to'])}
        if f.get('name'):
            attrs['name'] = f['name']
        sub(proc, 'sequenceFlow', attrs)

    diagram = sub(definitions, 'BPMNDiagram', {'id': 'Diagram_' + pid, 'name': m['title']}, p='bpmndi')
    plane = sub(diagram, 'BPMNPlane', {'id': prefix('plane'), 'bpmnElement': prefix('collaboration')}, p='bpmndi')
    shapes, extlabels, ly, y = {}, {}, {}, 60
    colw = m.get('columnWidth', 240)
    width = round(380 + max(n.get('col', 0) for n in m['nodes']) * colw)
    for lane in m['lanes']:
        maxrow = max([n.get('row', 0) for n in m['nodes'] if n['lane'] == lane['id']] + [0])
        height = m.get('laneHeight', 160) + maxrow * 140
        ly[lane['id']] = (y, height)
        y += height
    poolh = y - 60
    pool = sub(plane, 'BPMNShape', {'id': prefix('pool_di'), 'bpmnElement': prefix('pool'), 'isHorizontal': 'true'}, p='bpmndi')
    bounds(pool, (40, 60, width, poolh))
    for i, lane in enumerate(m['lanes']):
        yy, hh = ly[lane['id']]
        shape = sub(plane, 'BPMNShape', {'id': prefix(lane['id'] + '_di'), 'bpmnElement': prefix(lane['id']), 'isHorizontal': 'true',
                                         tag('bioc', 'fill'): TEMA['papel'] if i % 2 == 0 else TEMA['zona'], tag('bioc', 'stroke'): TEMA['cinza']}, p='bpmndi')
        bounds(shape, (70, yy, width - 30, hh))
    for n in m['nodes']:
        cx = 220 + n.get('col', 0) * colw
        cy = ly[n['lane']][0] + 70 + n.get('row', 0) * 140
        t = n['type']
        sz = (180, 80) if t in ('task', 'callActivity') else ((60, 60) if t.endswith('Gateway') else (40, 40))
        x = round((cx - sz[0] / 2) / 10) * 10
        y = round((cy - sz[1] / 2) / 10) * 10
        r = (x, y, *sz)
        shapes[n['id']] = r
        fill = TEMA['papel']
        if t.endswith('Gateway'):
            fill = TEMA['der-versionada']
        if t == 'endEvent':
            fill = TEMA['der-dominio-fundo']
        attrs = {'id': prefix(n['id'] + '_di'), 'bpmnElement': prefix(n['id']), tag('bioc', 'fill'): fill, tag('bioc', 'stroke'): TEMA['tinta']}
        if t.endswith('Gateway'):
            attrs['isMarkerVisible'] = 'true'
        shape = sub(plane, 'BPMNShape', attrs, p='bpmndi')
        bounds(shape, r)
        if t not in ('task', 'callActivity') and n.get('name'):
            lr = (cx - 83, y + sz[1] + 8, 166, 46)
            extlabels[n['id']] = lr
            label = sub(shape, 'BPMNLabel', p='bpmndi')
            bounds(label, lr)
    itens = list(shapes.items())
    for i, (a, r) in enumerate(itens):
        for b, rr in itens[i + 1:]:
            if overlap(r, rr):
                falha('SOBREPOSICAO %s e %s na mesma posição; mude col ou row' % (a, b))
    obstacles = list(shapes.values()) + list(extlabels.values())
    used, edge_labels = {}, []
    for f in m['flows']:
        pts = route(shapes[f['from']], shapes[f['to']], obstacles, used, width + 70, poolh + 100, f.get('via'), f.get('track', 0))
        edge = sub(plane, 'BPMNEdge', {'id': f['_id'] + '_di', 'bpmnElement': f['_id'], tag('bioc', 'stroke'): TEMA['apoio']}, p='bpmndi')
        for x, y in pts:
            sub(edge, 'waypoint', {'x': x, 'y': y}, p='di')
        if f.get('name'):
            label = sub(edge, 'BPMNLabel', p='bpmndi')
            bounds(label, label_box(pts, f['name'], obstacles, edge_labels))
    E.indent(definitions, space='  ')
    xml = E.tostring(definitions, encoding='utf-8', xml_declaration=True).decode()
    return xml, width + 80, poolh + 120


VIEWER = '''<!doctype html>
<html lang="__IDIOMA__"><head><meta charset="utf-8">
<title>__TITULO__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
__FONTES__
__IDIOMA_META__<style>__BPMN_CSS__</style>
<style>__TEMA__
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--fonte-texto);background:var(--papel);color:var(--tinta)}
.page{padding:36px 48px 28px;width:__LARGURA__px}
.hdr{display:flex;justify-content:space-between;font-family:var(--fonte-mono);font-size:11px;letter-spacing:.15em;color:var(--apoio);font-weight:500;text-transform:uppercase}
.kicker{font-family:var(--fonte-mono);font-size:11px;letter-spacing:.28em;font-weight:500;text-transform:uppercase;color:var(--cinza);margin-top:26px}
.kicker .sq{color:var(--acento)}
h1{font-size:38px;font-weight:600;letter-spacing:-.025em;line-height:1.05;margin-top:10px}
.sub{font-size:15px;color:var(--apoio);margin-top:10px;max-width:900px;line-height:1.5}
#canvas{width:__CW__px;height:__CH__px;margin-top:24px}
.foot{margin-top:18px;font-family:var(--fonte-mono);font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--cinza)}
.djs-label{font-family:var(--fonte-texto)!important}
</style></head><body>
<div class="page">
<div class="hdr"><span>__CAB_E__</span><span>__CAB_D__</span></div>
<div class="kicker"><span class="sq">■</span>&nbsp; __KICKER__</div>
<h1>__TITULO__</h1>
<div class="sub">__SUB__</div>
<div id="canvas"></div>
<div class="foot">__RODAPE__</div>
</div>
<script>__BPMN_JS__</script>
<script>
const xml = __BPMN_DATA__;
const viewer = new BpmnJS({container:'#canvas',textRenderer:{defaultStyle:{fontFamily:__FONTE_JS__,fontSize:13},externalStyle:{fontFamily:__FONTE_JS__,fontSize:12}}});
viewer.importXML(xml).then(function (r) {
  viewer.get('canvas').zoom('fit-viewport');
  document.body.setAttribute('data-importacao', 'ok ' + r.warnings.length + ' ' + r.warnings.map(function (w) { return w.message; }).join(' | '));
}).catch(function (e) {
  document.body.setAttribute('data-importacao', 'erro ' + e.message);
});
</script>
</body></html>
'''


def esc(t):
    return html.escape(str(t), quote=False)


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
    sys.exit('Chrome não encontrado. Aponte POSTER_CHROME.')


def main():
    flag_tema, sys.argv[1:] = _tema.tirar_flag(sys.argv[1:])
    flag_idioma, sys.argv[1:] = _idioma.tirar_flag(sys.argv[1:])
    tm = _tema.tema(flag_tema)
    TEMA.update({k: v for k, v in _tema.tokens(tm)})
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_dir = None
    if '--out' in sys.argv:
        out_dir = sys.argv[sys.argv.index('--out') + 1]
        args = [a for a in args if a != out_dir]
    if not args:
        sys.exit(__doc__)
    fonte = os.path.abspath(args[0])
    m = json.load(open(fonte))
    tr = _idioma.idioma(flag_idioma, fonte_json=m)
    src_dir = os.path.dirname(fonte)
    if out_dir is None:
        out_dir = os.path.dirname(src_dir) if os.path.basename(src_dir) == '_src' else src_dir
    nome = os.path.splitext(os.path.basename(fonte))[0]

    checar(m)
    xml, cw, ch = emitir(m)
    aqui = os.path.dirname(os.path.abspath(__file__))
    largura = cw + 96
    pagina = (VIEWER.replace('__IDIOMA__', tr['_codigo']).replace('__IDIOMA_META__', _idioma.para_gerador(tr))
              .replace('__KICKER__', esc(tr['bpmn.kicker']))
              .replace('__TEMA__', _tema.css_root(tm)).replace('__FONTES__', _tema.link_fontes(tm))
              .replace('__FONTE_JS__', json.dumps(_tema.pilha_texto(tm).replace("'", ''))).replace('__BPMN_CSS__', open(os.path.join(aqui, 'vendor', 'bpmn-js.css')).read())
              .replace('__BPMN_JS__', open(os.path.join(aqui, 'vendor', 'bpmn-navigated-viewer.js')).read())
              .replace('__BPMN_DATA__', json.dumps(xml, ensure_ascii=False).replace('</', '<\\/'))
              .replace('__TITULO__', esc(m['title'])).replace('__SUB__', esc(m.get('subtitle', '')))
              .replace('__CAB_E__', esc(m.get('cabecalho', ['', ''])[0])).replace('__CAB_D__', esc(m.get('cabecalho', ['', ''])[1]))
              .replace('__RODAPE__', m.get('rodape', ''))
              .replace('__LARGURA__', str(largura)).replace('__CW__', str(cw)).replace('__CH__', str(ch)))

    if '--sem-chrome' in sys.argv:
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, nome + '.bpmn'), 'w').write(xml)
        if '--so-bpmn' not in sys.argv:
            open(os.path.join(out_dir, nome + '.html'), 'w').write(pagina)
        print('estrutura, alcance e sobreposição: 0 problemas; importação e PNG pendentes (--sem-chrome)')
        return

    chrome = find_chrome()
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(pagina)
        tmp = f.name
    try:
        r = subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={largura},{ch + 400}',
                            '--virtual-time-budget=6000', '--dump-dom', 'file://' + tmp], capture_output=True, timeout=180)
    finally:
        os.unlink(tmp)
    mm = re.search(r'data-importacao="([^"]*)"', r.stdout.decode('utf-8', 'replace'))
    if not mm:
        falha('IMPORTACAO o viewer não terminou de importar no Chrome')
    res = html.unescape(mm.group(1))
    if not res.startswith('ok 0'):
        falha('IMPORTACAO ' + res)
    print('estrutura, alcance, sobreposição e importação no bpmn-js: 0 problemas')

    bpmn_out = os.path.join(out_dir, nome + '.bpmn')
    open(bpmn_out, 'w').write(xml)
    print('OK ' + bpmn_out)
    if '--so-bpmn' in sys.argv:
        return
    html_out = os.path.join(out_dir, nome + '.html')
    open(html_out, 'w').write(pagina)
    png = os.path.join(out_dir, nome + '.png')
    altura = ch + 260 + 26 * (len(m.get('subtitle', '')) // 110)
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--screenshot={png}',
                    f'--window-size={largura},{altura}', '--virtual-time-budget=6000',
                    '--force-device-scale-factor=1.5', 'file://' + html_out], capture_output=True, timeout=180)
    if not os.path.exists(png):
        falha('o Chrome não gerou o PNG')
    print('OK ' + html_out)
    print('OK ' + png)


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        sys.exit('O Chrome não respondeu a tempo. Confira a rede (as fontes vêm do Google Fonts), '
                 'feche outros Chrome headless presos e confira POSTER_CHROME.')
