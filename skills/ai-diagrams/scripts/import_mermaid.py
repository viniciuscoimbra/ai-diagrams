"""Strict Mermaid subset translated to the existing native model formats."""
import re

ID = r'[A-Za-z_][\w-]*'


class ImportError(ValueError):
    pass


def reject(code, line, text):
    raise ImportError(f'{code}: line {line}: {text}')


def fail(line, text):
    reject('MERMAID-UNSUPPORTED', line, text)


def lines(text):
    for i, s in enumerate(text.splitlines(), 1):
        if s.lstrip().startswith('%%{'):
            fail(i, 'unsupported Mermaid directive')
    return [(i, s.strip()) for i, s in enumerate(text.splitlines(), 1)
            if s.strip() and not s.lstrip().startswith('%%')]


def label(value, line):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    if not value or any(c in value for c in '<>"{}[]'):
        fail(line, 'empty label, HTML or unsupported label syntax')
    return value


def sequence(rows, base):
    people, messages, stack = {}, [], []
    current = messages
    for n, s in rows:
        m = re.fullmatch(r'(participant|actor) (' + ID + r')(?: as (.+))?', s)
        if m:
            kind, key, name = m.groups()
            if key in people:
                fail(n, 'repeated participant: ' + key)
            people[key] = {'id': key, 'nome': label(name or key, n), 'tipo': 'ator' if kind == 'actor' else 'servico'}
            continue
        m = re.fullmatch(r'(alt|loop|opt) (.+)', s)
        if m:
            part = {'fragmento': m[1], 'ramos': [{'guarda': label(m[2], n), 'mensagens': []}]}
            current.append(part)
            stack.append((current, part, n))
            current = part['ramos'][0]['mensagens']
            continue
        if s.startswith('else '):
            if not stack or stack[-1][1]['fragmento'] != 'alt':
                fail(n, 'else outside alt')
            branch = {'guarda': label(s[5:], n), 'mensagens': []}
            stack[-1][1]['ramos'].append(branch)
            current = branch['mensagens']
            continue
        if s == 'end':
            if not stack:
                fail(n, 'end without a fragment')
            current = stack.pop()[0]
            continue
        m = re.fullmatch(r'Note over (' + ID + r'): (.+)', s, re.I)
        if m:
            if m[1] not in people:
                fail(n, 'undeclared participant: ' + m[1])
            current.append({'nota': label(m[2], n), 'sobre': m[1]})
            continue
        m = re.fullmatch(r'(' + ID + r'?)(-->>|->>|-\))(' + ID + r')\s*:\s*(.+)', s)
        if not m:
            fail(n, s)
        a, arrow, b, text = m.groups()
        for key in (a, b):
            if key not in people:
                people[key] = {'id': key, 'nome': key, 'tipo': 'servico'}
        current.append({'de': a, 'para': b, 'texto': label(text, n),
                        'tipo': {'->>': 'sincrona', '-->>': 'resposta', '-)': 'assincrona'}[arrow]})
    if stack:
        fail(stack[-1][2], 'fragment without end')
    if not messages:
        fail(1, 'sequence without messages')
    return 'sequence', dict(base, participantes=list(people.values()), mensagens=messages)


def state(rows, base):
    states, transitions, initial, terminal = {}, [], None, set()
    def add(key):
        states.setdefault(key, {'id': key, 'nome': key, 'desc': key})
    for n, s in rows:
        m = re.fullmatch(r'state "([^"<>]+)" as (' + ID + r')', s)
        if m:
            add(m[2]); states[m[2]].update(nome=m[1], desc=m[1]); continue
        m = re.fullmatch(r'direction (LR|TB)', s)
        if m:
            base['direcao'] = {'LR': 'RIGHT', 'TB': 'DOWN'}[m[1]]; continue
        m = re.fullmatch(r'(' + ID + r'|\[\*\])\s*-->\s*(' + ID + r'|\[\*\])(?:\s*:\s*(.+))?', s)
        if not m:
            fail(n, s)
        a, b, event = m.groups()
        if a == '[*]':
            if b == '[*]' or initial or event:
                fail(n, 'only one unlabeled initial entry')
            initial = b; add(b)
        elif b == '[*]':
            if event:
                fail(n, 'the final state takes no outgoing event')
            add(a); terminal.add(a)
        else:
            if not event:
                fail(n, 'transition needs an event')
            add(a); add(b)
            transitions.append({'de': a, 'para': b, 'evento': label(event, n)})
    if not initial:
        fail(1, 'missing [*] --> initial state')
    for key in terminal:
        states[key]['final'] = True
    return 'states', dict(base, inicial=initial, estados=list(states.values()), transicoes=transitions)


def flow(rows, base):
    nodes, edges, lanes, active = {}, [], [], None
    def node(raw, n):
        m = re.fullmatch(r'(' + ID + r')(?:\[([^\[\]]+)\]|\{([^{}]+)\}|\(\(([^()]+)\)\))?', raw.strip())
        if not m:
            fail(n, raw)
        key, box, diamond, circle = m.groups()
        shape = 'task' if box else 'exclusiveGateway' if diamond else 'event' if circle else None
        text = label(box or diamond or circle or key, n)
        if key not in nodes:
            nodes[key] = {'id': key, 'name': text, 'type': shape or 'task', '_line': n, '_defined': bool(shape), 'lane': active}
        else:
            old = nodes[key]
            if shape:
                if old['_defined'] and (old['name'] != text or old['type'] != shape):
                    fail(n, 'node redefined: ' + key)
                old.update(name=text, type=shape, _defined=True)
            if active is not None:
                if old['lane'] is not None and old['lane'] != active:
                    fail(n, 'node in two lanes: ' + key)
                old['lane'] = active
        return key
    for n, s in rows:
        m = re.fullmatch(r'subgraph (' + ID + r')(?:\s*\[([^\[\]]+)\])?', s)
        if m:
            if active is not None or any(x['id'] == m[1] for x in lanes):
                fail(n, 'nested or repeated subgraph')
            active = m[1]; lanes.append({'id': active, 'name': label(m[2] or active, n)}); continue
        if s == 'end':
            if active is None:
                fail(n, 'end without subgraph')
            active = None; continue
        m = re.fullmatch(r'(.+?)\s*-->(?:\|([^|]+)\|)?\s*(.+)', s)
        if m:
            a, b = node(m[1], n), node(m[3], n)
            edge = {'from': a, 'to': b, '_line': n}
            if m[2]: edge['name'] = label(m[2], n)
            edges.append(edge)
        else:
            node(s, n)
    if active:
        fail(rows[-1][0], 'subgraph without end')
    if not nodes:
        fail(1, 'empty flowchart')
    if lanes:
        for node_ in nodes.values():
            if node_['lane'] is None or node_['type'] != 'task':
                fail(node_['_line'], 'swimlanes need rectangular nodes inside a subgraph')
        if any('name' in e for e in edges):
            fail(next(e['_line'] for e in edges if 'name' in e), 'swimlanes do not support arrow labels')
        incoming = {key: sum(e['to'] == key for e in edges) for key in nodes}
        order, pending = [], list(nodes)
        while pending:
            ready = [k for k in pending if not incoming[k]]
            if not ready:
                fail(nodes[pending[0]]['_line'], 'cycles are not supported in swimlanes')
            for key in ready:
                order.append(key); pending.remove(key)
                for e in edges:
                    if e['from'] == key: incoming[e['to']] -= 1
        positions = {key: [next(i for i, l in enumerate(lanes) if l['id'] == nodes[key]['lane']), i] for i, key in enumerate(order)}
        return 'swimlanes', dict(base, raias=[{'nome': l['name'], 'sub': ''} for l in lanes],
                            fases=[str(i + 1) for i in range(len(order))],
                            elementos=[{'raia': positions[k][0], 'fase': positions[k][1], 'texto': nodes[k]['name']} for k in order],
                            sequencia=[positions[e['from']] + positions[e['to']] for e in edges], secoes=[])
    for key, value in nodes.items():
        ent, out = any(e['to'] == key for e in edges), any(e['from'] == key for e in edges)
        if value['type'] == 'event':
            if ent and out or not ent and not out:
                fail(value['_line'], 'a circle must be only a start or an end')
            value['type'] = 'endEvent' if ent else 'startEvent'
        value['lane'] = 'process'
    # Flowcharts do not require start/end symbols; boundaries become explicit BPMN events.
    for key in list(nodes):
        for incoming, event_type in ((True, 'startEvent'), (False, 'endEvent')):
            field = 'to' if incoming else 'from'
            if nodes[key]['type'] == event_type or any(e[field] == key for e in edges):
                continue
            event_id = '__import_' + ('start_' if incoming else 'end_') + key
            while event_id in nodes: event_id += '_'
            nodes[event_id] = {'id': event_id, 'name': '', 'type': event_type, 'lane': 'process'}
            edges.append({'from': event_id if incoming else key, 'to': key if incoming else event_id})
    return 'bpmn', {'id': 'imported', 'title': base['h1'], 'subtitle': base['sub'], 'idioma': base['idioma'],
                    'cabecalho': base['cabecalho'], 'rodape': ' · '.join(base['rodape']),
                    'lanes': [{'id': 'process', 'name': base['h1']}],
                    'nodes': [{k: v for k, v in d.items() if not k.startswith('_')} for d in nodes.values()],
                    'flows': [{k: v for k, v in e.items() if not k.startswith('_')} for e in edges]}


def er(rows, base):
    tables, relations, current = {}, [], None
    for n, s in rows:
        if s == '}':
            if not current: fail(n, 'closing brace without an entity')
            current = None; continue
        if current:
            m = re.fullmatch(r'([\w()\[\],]+) (' + ID + r')(?: (PK|FK|UK))?(?: "([^"<>]*)")?', s)
            if not m: fail(n, s)
            kind, name, key, comment = m.groups()
            if any(c[0] == name for c in tables[current]['colunas']): fail(n, 'repeated attribute')
            tables[current]['colunas'].append([name, kind, {'UK': 'UQ'}.get(key, key or '')])
            if comment is not None: fail(n, 'ER attribute comments do not fit the native model')
            continue
        m = re.fullmatch(r'(' + ID + r')\s*\{', s)
        if m:
            current = 'public.' + m[1]
            if current in tables: fail(n, 'repeated entity')
            tables[current] = {'tipo': 'forte', 'rotulo': m[1], 'colunas': []}; continue
        m = re.fullmatch(r'(' + ID + r')\s+(\|\||\|o)\s*(--|\.\.)\s*(o\{|\|\{)\s+(' + ID + r')\s*:\s*(.+)', s)
        if not m: fail(n, s)
        a, one, link, many, b, text = m.groups()
        if link != '..' or many != 'o{':
            fail(n, 'the native ER supports only non-identifying one/zero-or-one to zero-or-many relationships (..o{)')
        relations.append((n, 'public.' + a, 'public.' + b, one == '||', label(text, n)))
    if current: fail(rows[-1][0], 'entity without }')
    if not tables: fail(1, 'ER diagram without entities')
    for n, parent, child, required, text in relations:
        if parent not in tables or child not in tables: fail(n, 'relationship names an undeclared entity')
        fks = [c for c in tables[child]['colunas'] if c[2] == 'FK' and len(c) == 3]
        pks = [c for c in tables[parent]['colunas'] if c[2] == 'PK']
        matching = [c for c in fks if pks and (c[0] == pks[0][0] or c[0] == parent.split('.')[1].lower() + '_' + pks[0][0])]
        if len(matching) != 1 and len(fks) == 1: matching = fks
        if len(matching) != 1: fail(n, 'relationship needs one unambiguous FK in the dependent entity')
        matching[0].extend([parent, required])
        tables[child]['tipo'] = 'dependente'
        tables[child].setdefault('relacoes', {})[matching[0][0]] = text
    for table in tables.values():
        if any(c[2] == 'FK' and len(c) == 3 for c in table['colunas']): fail(1, 'FK without a relationship')
    return 'er', {'idioma': base['idioma'], 'cabecalho': base['h1'], 'rodape': ' · '.join(base['rodape']),
                   'schemas': {'public': base['h1']}, 'tabelas': tables, 'schemaComum': None, 'schemaLeitura': None, 'colunasControle': []}


def parse(text, base):
    rows = lines(text)
    if not rows: fail(1, 'empty file')
    n, header = rows.pop(0)
    if re.fullmatch(r'(flowchart|graph) (TD|TB|LR)', header): return flow(rows, base)
    if header == 'sequenceDiagram': return sequence(rows, base)
    if header == 'stateDiagram-v2': return state(rows, base)
    if header == 'erDiagram': return er(rows, base)
    fail(n, header)
