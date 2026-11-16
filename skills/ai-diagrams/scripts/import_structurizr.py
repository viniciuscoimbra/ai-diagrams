"""Structurizr DSL (workspace.dsl) -> the C4 model that build_c4.py draws.

Reads the part of the DSL that describes the software and its views:
  workspace, model, views, group, enterprise (transparent blocks);
  person, softwareSystem, container, component (identifier = ..., name, description,
  technology, tags; the same fields as statements inside the element block);
  a -> b "description" "technology", also `-> b` and `this -> b` inside an element block;
  deploymentEnvironment, deploymentNode (with instances), infrastructureNode, containerInstance;
  systemLandscape, systemContext, container, component, dynamic and deployment views, with
  include (`*` or identifiers), exclude, title, description and autoLayout (lr/rl becomes
  orientation horizontal, tb/bt vertical);
  filtered views by tag; styles that set a shape (Cylinder, WebBrowser, Pipe, MobileDevice*);
  !identifiers, !impliedRelationships, configuration, properties, perspectives, theme(s),
  branding and terminology are accepted and do not change the drawing (colors come from the theme).
Anything else stops with DSL-UNSUPPORTED: <keyword> at line N.

A software system is external when it has the tag External (or `location External`), or when
the workspace has an enterprise block and the system is outside it.
"""
import re

FORMAS = {'cylinder': 'database', 'webbrowser': 'web', 'pipe': 'queue',
          'mobiledeviceportrait': 'mobile', 'mobiledevicelandscape': 'mobile'}
IGNORADOS = {'configuration', 'properties', 'perspectives', 'theme', 'themes', 'branding', 'terminology',
             'url', 'docs', 'adrs', '!docs', '!adrs', 'animation', 'autolayout', 'default', 'users', 'scope',
             'visibility', 'healthcheck', 'instances', 'deploymentgroup', 'relationship', 'icon', 'border',
             'opacity', 'metadata', 'description_', 'stroke', 'strokewidth', 'color', 'colour', 'fontsize',
             'width', 'height', 'background', 'routing', 'thickness', 'style', 'position', 'dashed', 'linestyle'}


class DSLError(Exception):
    pass


def tokens(texto):
    """Lista de linhas lógicas: (número da linha, [tokens]). Strings entre aspas viram ('s', valor)."""
    out = []
    texto = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), texto, flags=re.S)
    for n, linha in enumerate(texto.split('\n'), 1):
        toks, i = [], 0
        while i < len(linha):
            c = linha[i]
            if c.isspace():
                i += 1
            elif c == '"':
                j, buf = i + 1, ''
                while j < len(linha) and linha[j] != '"':
                    if linha[j] == '\\' and j + 1 < len(linha):
                        j += 1
                    buf += linha[j]
                    j += 1
                if j >= len(linha):
                    raise DSLError('DSL-INVALID: unclosed quote at line %d' % n)
                toks.append(('s', buf))
                i = j + 1
            elif linha.startswith('//', i) or (c == '#' and not toks):
                break
            elif c in '{}=':
                toks.append(('p', c))
                i += 1
            elif linha.startswith('->', i):
                toks.append(('p', '->'))
                i += 2
            else:
                m = re.match(r'[^\s{}="]+', linha[i:])
                palavra = m.group(0)
                if palavra.startswith('->'):
                    palavra = palavra[2:]
                toks.append(('w', palavra))
                i += len(m.group(0))
        # chave abrindo ou fechando no meio da linha separa instruções: `element "Tag" { shape Cylinder }`
        atual = []
        for t in toks:
            if t == ('p', '}') and atual:
                out.append((n, atual))
                atual = []
            atual.append(t)
            if t in (('p', '{'), ('p', '}')):
                out.append((n, atual))
                atual = []
        if atual:
            out.append((n, atual))
    return out


def slug(t):
    s = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    return s or 'x'


class Leitor:
    def __init__(self, texto):
        self.linhas = tokens(texto)
        self.k = 0
        self.el = []                # elementos do modelo C4, em ordem
        self.por_id = {}
        self.ids = {}               # identificador DSL -> id do modelo
        self.rels = []
        self.views = []
        self.formas = {}            # tag -> forma
        self.tags = {}              # id -> set de tags
        self.hierarquico = False
        self.enterprise = None      # ids dentro do bloco enterprise, se houver
        self.nome = None
        self.descricao = None

    # -------------------------------------------------------------- utilidades
    def erro(self, n, msg):
        raise DSLError('%s at line %d' % (msg, n))

    def proxima(self):
        if self.k >= len(self.linhas):
            return None, None
        r = self.linhas[self.k]
        self.k += 1
        return r

    def pular_bloco(self):
        nivel = 1
        while nivel:
            n, t = self.proxima()
            if t is None:
                raise DSLError('DSL-INVALID: a block is not closed')
            nivel += t.count(('p', '{')) - t.count(('p', '}'))

    def novo_id(self, base):
        i, k = slug(base), 2
        usados = {e['id'] for e in self.el}
        cand = i
        while cand in usados:
            cand = '%s-%d' % (i, k)
            k += 1
        return cand

    def ref(self, n, nome, contexto):
        if nome == 'this' and contexto:
            return contexto
        if nome in self.ids:
            return self.ids[nome]
        self.erro(n, 'DSL-UNKNOWN: "%s" is not an identifier declared before' % nome)

    @staticmethod
    def strings(t):
        return [v for k, v in t if k == 's']

    # -------------------------------------------------------------- leitura
    def ler(self):
        while True:
            n, t = self.proxima()
            if t is None:
                break
            if t[0] == ('w', 'workspace'):
                s = self.strings(t)
                self.nome = s[0] if s else None
                self.descricao = s[1] if len(s) > 1 else None
                if ('p', '{') not in t:
                    self.erro(n, 'DSL-INVALID: workspace needs a block')
                self.workspace()
            elif t[0][1].startswith('!'):
                self.diretiva(n, t)
            else:
                self.erro(n, 'DSL-UNSUPPORTED: %s' % t[0][1])
        return self

    def diretiva(self, n, t):
        d = t[0][1].lower()
        if d == '!identifiers':
            self.hierarquico = len(t) > 1 and t[1][1] == 'hierarchical'
        elif d in ('!impliedrelationships',):
            pass
        else:
            self.erro(n, 'DSL-UNSUPPORTED: %s (expand includes and scripts before importing)' % t[0][1])

    def workspace(self):
        while True:
            n, t = self.proxima()
            if t is None or t == [('p', '}')]:
                return
            w = t[0][1].lower()
            if t[0][0] == 'w' and w.startswith('!'):
                self.diretiva(n, t)
            elif w == 'model':
                self.modelo(None, None)
            elif w == 'views':
                self.vistas()
            elif w == 'name':
                self.nome = self.strings(t)[0]
            elif w == 'description':
                self.descricao = self.strings(t)[0]
            elif w in IGNORADOS:
                if ('p', '{') in t:
                    self.pular_bloco()
            else:
                self.erro(n, 'DSL-UNSUPPORTED: %s' % t[0][1])

    def modelo(self, pai, prefixo, dentro_enterprise=False, ambiente=None):
        """Lê um bloco do modelo até a chave que o fecha. pai: id do elemento dono do bloco."""
        while True:
            n, t = self.proxima()
            if t is None:
                raise DSLError('DSL-INVALID: the model block is not closed')
            if t == [('p', '}')]:
                return
            ident = None
            if len(t) > 2 and t[1] == ('p', '=') and t[0][0] == 'w':
                ident, t = t[0][1], t[2:]
            # relação: a -> b, -> b, this -> b
            if ('p', '->') in t:
                i = t.index(('p', '->'))
                origem = self.ref(n, t[0][1], pai) if i == 1 else pai
                if origem is None:
                    self.erro(n, 'DSL-INVALID: a relationship without a source')
                destino = self.ref(n, t[i + 1][1], pai)
                s = self.strings(t[i + 2:])
                r = {'from': origem, 'to': destino}
                if s:
                    r['description'] = s[0]
                if len(s) > 1:
                    r['technology'] = s[1]
                self.rels.append(r)
                if ('p', '{') in t:
                    self.pular_bloco()
                continue
            w = t[0][1]
            wl = w.lower()
            if t[0][0] == 'w' and wl.startswith('!'):
                self.diretiva(n, t)
                continue
            dono = self.por_id.get(pai)
            if dono is not None and not ident:
                if wl in ('description', 'technology') and self.strings(t):
                    dono[wl] = self.strings(t)[0]
                    continue
                if wl in ('tags', 'tag'):
                    self.tags[pai] |= {x.strip() for s in self.strings(t) for x in s.split(',') if x.strip()}
                    continue
                if wl == 'location':
                    if len(t) > 1 and t[1][1].lower() == 'external':
                        self.tags[pai].add('External')
                    continue
                if wl == 'instances' and len(t) > 1:
                    try:
                        dono['instances'] = int((self.strings(t) or [t[1][1]])[0])
                    except ValueError:
                        pass
                    continue
            tipo = {'person': 'person', 'softwaresystem': 'system', 'container': 'container', 'component': 'component',
                    'deploymentnode': 'deploymentNode', 'infrastructurenode': 'infrastructureNode'}.get(wl)
            if tipo:
                s = self.strings(t)
                if not s:
                    self.erro(n, 'DSL-INVALID: %s needs a name' % w)
                e = {'id': self.novo_id(ident or s[0]), 'type': tipo, 'name': s[0]}
                campos = {'person': ['description', 'tags'], 'system': ['description', 'tags'],
                          'container': ['description', 'technology', 'tags'], 'component': ['description', 'technology', 'tags'],
                          'deploymentNode': ['description', 'technology', 'tags', 'instances'],
                          'infrastructureNode': ['description', 'technology', 'tags']}[tipo]
                for campo, v in zip(campos, s[1:]):
                    e[campo] = v
                tags = {x.strip() for x in e.pop('tags', '').split(',') if x.strip()}
                if 'instances' in e:
                    try:
                        e['instances'] = int(e['instances'])
                    except ValueError:
                        e.pop('instances')
                if pai:
                    e['parent'] = pai
                if ambiente and not pai:
                    e['environment'] = ambiente
                if tipo == 'person' or tipo == 'system':
                    e.pop('parent', None)
                self.el.append(e)
                self.por_id[e['id']] = e
                self.tags[e['id']] = tags | {{'person': 'Person', 'system': 'Software System', 'container': 'Container',
                                               'component': 'Component'}.get(tipo, 'Element')}
                if dentro_enterprise:
                    self.enterprise.add(e['id'])
                self.registra(ident, e['id'], prefixo)
                if ('p', '{') in t:
                    novo_prefixo = ((prefixo + '.') if prefixo else '') + ident if (ident and self.hierarquico) else prefixo
                    self.elemento(e, novo_prefixo, ambiente)
                continue
            if wl == 'containerinstance':
                alvo = self.ref(n, t[1][1], None)
                e = {'id': self.novo_id(ident or t[1][1] + '-' + slug(ambiente or 'env')), 'type': 'containerInstance',
                     'container': alvo, 'parent': pai}
                self.el.append(e)
                self.por_id[e['id']] = e
                self.tags[e['id']] = {'Container Instance'}
                self.registra(ident, e['id'], prefixo)
                if ('p', '{') in t:
                    self.elemento(e, prefixo, ambiente)
                continue
            if wl == 'softwaresysteminstance':
                self.erro(n, 'DSL-UNSUPPORTED: softwareSystemInstance (draw the system containers as containerInstance)')
            if wl == 'deploymentenvironment':
                nome = self.strings(t)[0] if self.strings(t) else t[1][1]
                self.registra(ident, None, prefixo)
                self.modelo(None, prefixo, ambiente=nome)
                continue
            if wl in ('group', 'enterprise'):
                if wl == 'enterprise':
                    self.enterprise = self.enterprise or set()
                self.modelo(pai, prefixo, dentro_enterprise or wl == 'enterprise', ambiente)
                continue
            if wl in ('deploymentgroup',):
                continue
            if wl in IGNORADOS:
                if ('p', '{') in t:
                    self.pular_bloco()
                continue
            self.erro(n, 'DSL-UNSUPPORTED: %s' % w)

    def registra(self, ident, id_, prefixo):
        if not ident:
            return
        if self.hierarquico and prefixo:
            self.ids[prefixo + '.' + ident] = id_
        self.ids.setdefault(ident, id_)

    def elemento(self, e, prefixo, ambiente):
        """Bloco de um elemento: campos como instruções, filhos e relações com a origem implícita."""
        self.modelo(e['id'], prefixo, False, ambiente)

    def vistas(self):
        while True:
            n, t = self.proxima()
            if t is None:
                raise DSLError('DSL-INVALID: the views block is not closed')
            if t == [('p', '}')]:
                return
            w = t[0][1].lower()
            if w == 'styles':
                self.estilos()
                continue
            if w in IGNORADOS or w == 'properties':
                if ('p', '{') in t:
                    self.pular_bloco()
                continue
            tipos = {'systemlandscape': ('landscape', 0), 'systemcontext': ('context', 1), 'container': ('container', 1),
                     'component': ('component', 1), 'dynamic': ('dynamic', 1), 'deployment': ('deployment', 2),
                     'filtered': ('filtered', 0)}
            if w not in tipos:
                self.erro(n, 'DSL-UNSUPPORTED: %s view' % t[0][1])
            tipo, nargs = tipos[w]
            args = [x for x in t[1:] if x != ('p', '{')]
            v = {'type': tipo}
            if tipo == 'filtered':
                base, modo, tags = args[0][1], args[1][1].lower(), args[2][1]
                v.update({'_base': base, '_modo': modo, '_tags': [x.strip() for x in tags.split(',')]})
                resto = args[3:]
            else:
                if nargs >= 1:
                    alvo = args[0][1]
                    if alvo != '*':
                        v['scope'] = self.ref(n, alvo, None)
                if tipo == 'deployment':
                    v['environment'] = args[1][1]
                resto = args[nargs:]
            if resto:
                v['key'] = resto[0][1]
            if len(resto) > 1:
                v['description'] = resto[1][1]
            if ('p', '{') in t:
                self.vista(v)
            self.views.append(v)

    def vista(self, v):
        passos = []
        while True:
            n, t = self.proxima()
            if t is None:
                raise DSLError('DSL-INVALID: a view block is not closed')
            if t == [('p', '}')]:
                break
            w = t[0][1].lower() if t[0][0] == 'w' else ''
            if ('p', '->') in t and v['type'] == 'dynamic':
                i = t.index(('p', '->'))
                if i != 1:
                    self.erro(n, 'DSL-UNSUPPORTED: dynamic step without a source')
                s = self.strings(t[i + 2:])
                p = {'from': self.ref(n, t[0][1], None), 'to': self.ref(n, t[i + 1][1], None)}
                if s:
                    p['description'] = s[0]
                if len(s) > 1:
                    p['technology'] = s[1]
                passos.append(p)
            elif w == 'include' or w == 'exclude':
                for x in t[1:]:
                    nome = x[1]
                    if nome == '*':
                        continue
                    if '->' in nome or x == ('p', '->') or nome.startswith('element.') or nome.startswith('relationship'):
                        self.erro(n, 'DSL-UNSUPPORTED: %s expression "%s" (use * or identifiers)' % (w, nome))
                    v.setdefault(w, []).append(self.ref(n, nome, None))
            elif w == 'title':
                v['title'] = self.strings(t)[0]
            elif w == 'description':
                v['description'] = self.strings(t)[0]
            elif w == '{':
                self.erro(n, 'DSL-UNSUPPORTED: parallel blocks in a dynamic view')
            elif w == 'autolayout' and len(t) > 1 and t[1][1].lower() in ('lr', 'rl', 'tb', 'bt'):
                # rank direction: left-right becomes a horizontal view, top-bottom a vertical one;
                # bare autoLayout leaves the choice to build_c4.py ("auto")
                v['orientation'] = 'horizontal' if t[1][1].lower() in ('lr', 'rl') else 'vertical'
            elif w in IGNORADOS or w in ('autolayout', 'animation', 'default'):
                if ('p', '{') in t:
                    self.pular_bloco()
            else:
                self.erro(n, 'DSL-UNSUPPORTED: %s in a view' % t[0][1])
        if v['type'] == 'dynamic':
            v['steps'] = passos

    def estilos(self):
        while True:
            n, t = self.proxima()
            if t is None or t == [('p', '}')]:
                return
            if t[0][1].lower() == 'element' and ('p', '{') in t:
                tag = self.strings(t)[0]
                while True:
                    n2, t2 = self.proxima()
                    if t2 is None or t2 == [('p', '}')]:
                        break
                    if t2[0][1].lower() == 'shape' and len(t2) > 1:
                        forma = FORMAS.get(t2[1][1].lower())
                        if forma:
                            self.formas[tag] = forma
                    if ('p', '{') in t2:
                        self.pular_bloco()
            elif ('p', '{') in t:
                self.pular_bloco()


def modelo_c4(texto, base):
    """texto do workspace.dsl -> modelo C4 (chaves públicas). base: header, footer e lang da importação."""
    L = Leitor(texto).ler()
    if not L.el:
        raise DSLError('DSL-INVALID: the workspace has no model elements')
    for e in L.el:
        tags = L.tags.get(e['id'], set())
        for tag, forma in L.formas.items():
            if tag in tags and e['type'] in ('container', 'component', 'system'):
                e['shape'] = forma
        if e['type'] == 'system':
            if 'External' in tags or (L.enterprise is not None and e['id'] not in L.enterprise):
                e['external'] = True
    # vistas: chave única em minúsculas, título padrão, filtradas viram include/exclude da vista base
    chaves = set()
    vistas = []
    por_chave = {v.get('key'): v for v in L.views}
    for k, v in enumerate(L.views, 1):
        if v['type'] == 'filtered':
            b = por_chave.get(v['_base'])
            if not b:
                raise DSLError('DSL-UNKNOWN: filtered view names the base view "%s", which does not exist' % v['_base'])
            nv = {x: y for x, y in b.items() if x not in ('key', 'include', 'exclude')}
            com_tag = [e['id'] for e in L.el if L.tags.get(e['id'], set()) & set(v['_tags'])]
            nv['include' if v['_modo'] == 'include' else 'exclude'] = com_tag
            nv['key'] = v.get('key') or b.get('key', 'view') + '-filtered'
            if v.get('description'):
                nv['description'] = v['description']
            v = nv
        if v['type'] in ('context', 'container', 'component', 'deployment') and 'scope' not in v:
            raise DSLError('DSL-UNSUPPORTED: %s view of "*" (name the system or container)' % v['type'])
        chave = slug(v.get('key') or '%s-%d' % (v['type'], k))
        while chave in chaves:
            chave += '-2'
        chaves.add(chave)
        v = {x: y for x, y in v.items() if not x.startswith('_')}
        v['key'] = chave
        vistas.append(v)
    if not vistas:
        vistas = [{'type': 'landscape', 'key': 'landscape'}]
    for v in vistas:
        # sem title, o gerador escreve "<escopo>: <nome da visão>" no idioma do diagrama
        v.setdefault('description', L.descricao or '')
    titulo = L.nome or base['title']
    out = {'lang': base['lang'], 'header': [titulo, 'V1'], 'footer': [base['footer'], titulo],
           'elements': L.el, 'relationships': L.rels, 'views': vistas}
    principal = next((v['key'] for v in vistas if v['type'] == 'container'), None)
    if principal:
        out['main'] = principal
    return out
