"""BPMN XML and tabular inputs for the native ai-diagrams formats."""
import csv
import io
import json
import re
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat
import compat
from import_mermaid import ImportError, reject

BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
DI = {'http://www.omg.org/spec/BPMN/20100524/DI', 'http://www.omg.org/spec/DD/20100524/DC', 'http://www.omg.org/spec/DD/20100524/DI'}


def bpmn(text, base):
    builder, source_lines = ET.TreeBuilder(), {}
    parser = expat.ParserCreate(namespace_separator='}')
    def expanded(value): return '{' + value if '}' in value else value
    def start(tag, attrs):
        element = builder.start(expanded(tag), {expanded(k): v for k, v in attrs.items()})
        source_lines[element] = parser.CurrentLineNumber
    def forbidden(*args): reject('BPMN-UNSUPPORTED', parser.CurrentLineNumber, 'DTD, entity or XML processing instruction')
    parser.StartElementHandler = start
    parser.EndElementHandler = lambda tag: builder.end(expanded(tag))
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = forbidden
    parser.EntityDeclHandler = forbidden
    parser.ProcessingInstructionHandler = forbidden
    try:
        parser.Parse(text, True)
        root = builder.close()
    except expat.ExpatError as e:
        reject('BPMN-UNSUPPORTED', e.lineno, str(e))
    def bad(msg, el=None): reject('BPMN-UNSUPPORTED', source_lines.get(el, 1), msg)
    def name(el): return el.tag.rsplit('}', 1)[-1]
    attrs = {
        'definitions': {'id', 'targetNamespace', 'exporter', 'exporterVersion', 'expressionLanguage', 'typeLanguage'},
        'process': {'id', 'name', 'isExecutable'}, 'laneSet': {'id'}, 'lane': {'id', 'name'},
        'sequenceFlow': {'id', 'name', 'sourceRef', 'targetRef'},
        'documentation': {'textFormat'}, 'incoming': set(), 'outgoing': set(), 'flowNodeRef': set(),
        'timerEventDefinition': {'id'}, 'messageEventDefinition': {'id'}, 'conditionalEventDefinition': {'id'},
        'condition': {'{http://www.w3.org/2001/XMLSchema-instance}type'},
        'collaboration': {'id', 'name'}, 'participant': {'id', 'name', 'processRef'},
    }
    types = {'task', 'callActivity', 'startEvent', 'endEvent', 'exclusiveGateway', 'parallelGateway', 'intermediateCatchEvent', 'intermediateThrowEvent'}
    for kind in types: attrs[kind] = {'id', 'name'} | ({'gatewayDirection'} if 'Gateway' in kind else set())
    parents = {'definitions': {'process', 'collaboration', 'BPMNDiagram'}, 'process': types | {'laneSet', 'sequenceFlow', 'documentation'},
               'collaboration': {'participant'}, 'laneSet': {'lane'}, 'lane': {'flowNodeRef'}, 'sequenceFlow': set()}
    for kind in types:
        parents[kind] = {'incoming', 'outgoing', 'documentation'}
        if 'Event' in kind: parents[kind] |= {'timerEventDefinition', 'messageEventDefinition', 'conditionalEventDefinition'}
    parents['conditionalEventDefinition'] = {'condition'}
    def check(el):
        kind = name(el)
        ns = el.tag[1:].split('}')[0] if el.tag.startswith('{') else ''
        if ns in DI:
            geometry = {'BPMNDiagram', 'BPMNPlane', 'BPMNShape', 'BPMNEdge', 'BPMNLabel', 'BPMNLabelStyle', 'Bounds', 'waypoint', 'Font'}
            if kind not in geometry: bad('layout element ' + kind, el)
            for child in el:
                if not any(child.tag.startswith('{' + uri + '}') for uri in DI): bad('element inside the layout ' + child.tag, child)
                check(child)
            return
        if ns != BPMN or kind not in attrs: bad('element ' + el.tag, el)
        for attr in el.attrib:
            if attr not in attrs[kind]: bad(kind + ' attribute ' + attr, el)
        if kind == 'documentation' and el.get('textFormat', 'text/plain') != 'text/plain': bad('documentation must be plain text', el)
        if kind not in {'documentation', 'incoming', 'outgoing', 'flowNodeRef', 'condition'} and (el.text or '').strip(): bad('unexpected text in ' + kind, el)
        for child in el:
            if name(child) not in parents.get(kind, set()): bad(kind + '/' + name(child), child)
            if (child.tail or '').strip(): bad('unexpected text after ' + name(child), child)
            check(child)
    if root.tag != '{' + BPMN + '}definitions': bad('the root must be BPMN definitions')
    check(root)
    processes = root.findall('{' + BPMN + '}process')
    if len(processes) != 1: bad('exactly one process is supported')
    proc = processes[0]
    if not proc.get('id'): bad('process without id', proc)
    if proc.get('isExecutable', 'false') not in ('false', '0'): bad('executable process; the engine imports descriptive models', proc)
    collaborations = root.findall('{' + BPMN + '}collaboration')
    if len(collaborations) > 1: bad('only one collaboration is supported', collaborations[1])
    if collaborations:
        participants = list(collaborations[0])
        if len(participants) != 1 or participants[0].get('processRef') != proc.get('id'):
            bad('the collaboration must hold one participant for the imported process', collaborations[0])
        if participants[0].get('name') and proc.get('name') and participants[0].get('name') != proc.get('name'):
            bad('different pool and process names do not fit the native model', participants[0])
    all_ids = [el.get('id') for el in root.iter() if el.get('id')]
    if len(all_ids) != len(set(all_ids)): bad('repeated ids')
    if any(not re.fullmatch(r'[A-Za-z_][\w.-]*', key) for key in all_ids): bad('invalid XML id')
    lanes, lane_map, nodes, flows = [], {}, [], []
    lane_sets = proc.findall('{' + BPMN + '}laneSet')
    if len(lane_sets) > 1: bad('only one laneSet is supported', lane_sets[1])
    for lane in proc.findall('./{' + BPMN + '}laneSet/{' + BPMN + '}lane'):
        if not lane.get('id'): bad('lane without id')
        lanes.append({'id': lane.get('id'), 'name': lane.get('name', lane.get('id'))})
        for ref in lane.findall('{' + BPMN + '}flowNodeRef'):
            key = (ref.text or '').strip()
            if key in lane_map: bad('node in two lanes: ' + key)
            lane_map[key] = lane.get('id')
    if not lanes: lanes = [{'id': 'process', 'name': proc.get('name', base['h1'])}]
    for el in proc:
        kind, key = name(el), el.get('id')
        if kind in types:
            if not key: bad(kind + ' without id')
            if lane_sets and key not in lane_map: bad('node outside any lane: ' + key, el)
            node = {'id': key, 'name': el.get('name', key), 'type': kind, 'lane': lane_map.get(key, lanes[0]['id'])}
            defs = [x for x in el if name(x).endswith('EventDefinition')]
            if len(defs) > 1: bad('multiple event definitions')
            if defs:
                node['event'] = {'timerEventDefinition': 'timer', 'messageEventDefinition': 'message', 'conditionalEventDefinition': 'condition'}[name(defs[0])]
                if node['event'] in {'timer', 'condition'} and kind not in {'startEvent', 'intermediateCatchEvent'}:
                    bad('event type incompatible with ' + kind, defs[0])
                if node['event'] == 'condition':
                    cond = defs[0].find('{' + BPMN + '}condition')
                    if cond is None or not cond.text: bad('empty condition')
                    node['condition'] = cond.text
            docs = el.findall('{' + BPMN + '}documentation')
            if docs: node['doc'] = '\n'.join(doc.text or '' for doc in docs)
            nodes.append(node)
        elif kind == 'sequenceFlow':
            if not key or not el.get('sourceRef') or not el.get('targetRef'): bad('sequenceFlow without id/sourceRef/targetRef')
            if list(el): bad('sequenceFlow documentation does not fit the native model')
            flow = {'from': el.get('sourceRef'), 'to': el.get('targetRef')}
            if el.get('name'): flow['name'] = el.get('name')
            flows.append(flow)
    nodeids = {n['id'] for n in nodes}
    if not nodes or set(lane_map) - nodeids: bad('empty process or unknown flowNodeRef')
    if any(f['from'] not in nodeids or f['to'] not in nodeids for f in flows): bad('sequenceFlow to a missing node')
    flowids = {e.get('id'): e for e in proc if name(e) == 'sequenceFlow'}
    for el in proc:
        if name(el) in {'exclusiveGateway', 'parallelGateway'}:
            direction = el.get('gatewayDirection', 'Unspecified')
            outgoing = sum(f['from'] == el.get('id') for f in flows)
            expected = 'Diverging' if outgoing > 1 else 'Converging'
            if direction not in {'Unspecified', expected}: bad('gatewayDirection cannot be represented: ' + direction, el)
        for ref in el:
            if name(ref) in ('incoming', 'outgoing'):
                flow = flowids.get((ref.text or '').strip())
                attr = 'targetRef' if name(ref) == 'incoming' else 'sourceRef'
                if flow is None or flow.get(attr) != el.get('id'): bad('inconsistent incoming/outgoing reference')
    docs = proc.findall('{' + BPMN + '}documentation')
    title = proc.get('name') or (participants[0].get('name') if collaborations else None) or base['h1']
    return 'bpmn', {'id': proc.get('id'), 'title': title,
                    'subtitle': '\n'.join(d.text or '' for d in docs) or base['sub'], 'idioma': base['idioma'],
                    'cabecalho': base['cabecalho'], 'rodape': ' · '.join(base['rodape']),
                    'lanes': lanes, 'nodes': nodes, 'flows': flows}


def sql(text, base):
    # shortcut: deliberately limited DDL grammar; add an explicit parser before supporting quoted identifiers or ALTER.
    clean = re.sub(r'--[^\n]*', '', text)
    ident = r'[A-Za-z_][A-Za-z_0-9]*'
    qualified = ident + r'(?:\.' + ident + r')?'
    tables, schemas = {}, {}
    def full(key): return key if '.' in key else 'public.' + key
    def bad(pos, msg): reject('SQL-UNSUPPORTED', clean[:pos].count('\n') + 1, msg)
    pos = 0
    for raw in clean.split(';'):
        start = pos; pos += len(raw) + 1
        s = raw.strip()
        if not s: continue
        m = re.fullmatch(r'CREATE\s+SCHEMA\s+(' + ident + ')', s, re.I)
        if m: schemas[m[1]] = m[1]; continue
        m = re.fullmatch(r'CREATE\s+TABLE\s+(' + qualified + r')\s*\((.*)\)', s, re.I | re.S)
        if not m: bad(start, s[:100])
        key, body = full(m[1]), m[2]
        if key in tables: bad(start, 'repeated table ' + key)
        schemas.setdefault(key.split('.')[0], key.split('.')[0])
        columns, constraints = [], []
        parts = re.split(r',\s*(?![^()]*\))', body)
        for part in parts:
            part = part.strip()
            cons = re.fullmatch(r'(?:CONSTRAINT\s+' + ident + r'\s+)?(PRIMARY KEY|UNIQUE)\s*\(\s*(' + ident + r')\s*\)', part, re.I)
            fk = re.fullmatch(r'(?:CONSTRAINT\s+' + ident + r'\s+)?FOREIGN KEY\s*\(\s*(' + ident + r')\s*\)\s+REFERENCES\s+(' + qualified + r')(?:\s*\(\s*(' + ident + r')\s*\))?', part, re.I)
            if cons: constraints.append((cons[2], 'PK' if cons[1].upper() == 'PRIMARY KEY' else 'UQ', None, None)); continue
            if fk: constraints.append((fk[1], 'FK', full(fk[2]), fk[3])); continue
            col = re.fullmatch(r'(' + ident + r')\s+([A-Za-z][A-Za-z_0-9]*(?:\(\d+(?:\s*,\s*\d+)?\))?)(.*)', part, re.S)
            if not col: bad(start, part)
            name, kind, rest = col.groups()
            if any(c[0] == name for c in columns): bad(start, 'repeated column ' + name)
            flags, target, targetcol, default = set(), None, None, None
            while rest.strip():
                rest = rest.strip()
                token = re.match(r'^(PRIMARY KEY|NOT NULL|UNIQUE|NULL)\b', rest, re.I)
                ref = re.match(r'^REFERENCES\s+(' + qualified + r')(?:\s*\(\s*(' + ident + r')\s*\))?', rest, re.I)
                df = re.match(r"^DEFAULT\s+(now\(\)|CURRENT_TIMESTAMP|true|false|NULL|-?\d+(?:\.\d+)?|'(?:[^']|'')*')(?=\s|$)", rest, re.I)
                if token:
                    flags.add(token[1].upper()); rest = rest[token.end():]
                elif ref and not target:
                    target, targetcol, rest = full(ref[1]), ref[2], rest[ref.end():]
                elif df and default is None:
                    default, rest = df[1], rest[df.end():]
                else: bad(start, 'constraint ' + rest)
            if target and ('PRIMARY KEY' in flags or 'UNIQUE' in flags): bad(start, 'FK with PK/UNIQUE does not fit the native cardinality')
            entry = [name, re.sub(r'\s+', '', kind), 'FK' if target else 'PK' if 'PRIMARY KEY' in flags else 'UQ' if 'UNIQUE' in flags else '']
            if target: entry.extend([target, 'NOT NULL' in flags])
            columns.append(entry)
            constraints.append((name, '_meta', {'not_null': 'NOT NULL' in flags or 'PRIMARY KEY' in flags, 'default': default, 'target_column': targetcol}, None))
        metadata = {name: value for name, flag, value, _ in constraints if flag == '_meta'}
        for name, flag, target, targetcol in constraints:
            matches = [c for c in columns if c[0] == name]
            if not matches: bad(start, 'constraint names a missing column ' + name)
            if flag == '_meta': continue
            column = matches[0]
            if column[2] and column[2] != flag: bad(start, 'multiple keys on column ' + name)
            column[2] = flag
            if flag == 'PK': metadata[name]['not_null'] = True
            if flag == 'FK': column[:] = column[:3] + [target, metadata.get(name, {}).get('not_null', False)]; metadata.setdefault(name, {})['target_column'] = targetcol
        tables[key] = {'tipo': 'dependente' if any(c[2] == 'FK' for c in columns) else 'forte', 'rotulo': key.split('.')[1], 'colunas': columns, 'sql': metadata}
    if not tables: bad(0, 'DDL without CREATE TABLE')
    for table in tables.values():
        for c in table['colunas']:
            if c[2] == 'FK':
                if c[3] not in tables: bad(0, 'FK names a missing table ' + c[3])
                tc = table['sql'][c[0]].get('target_column')
                target_keys = [x for x in tables[c[3]]['colunas'] if x[2] in ('PK', 'UQ') and (x[0] == tc if tc else x[2] == 'PK')]
                if len(target_keys) != 1: bad(0, 'FK must point to one existing unique key in ' + c[3])
    return 'er', {'idioma': base['idioma'], 'cabecalho': base['h1'], 'rodape': ' · '.join(base['rodape']),
                   'schemas': schemas, 'tabelas': tables, 'schemaComum': None, 'schemaLeitura': None, 'colunasControle': []}


def catalog(text):
    try:
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except csv.Error as e: reject('CSV-UNSUPPORTED', 1, str(e))
    if len(rows) < 2 or not 2 <= len(rows[0]) <= 5: reject('CSV-UNSUPPORTED', 1, 'header with 2 to 5 columns and at least one row')
    if len(rows[0]) != len(set(rows[0])) or any(not x.strip() for x in rows[0]): reject('CSV-UNSUPPORTED', 1, 'empty or repeated headers')
    if len(rows) > 11: reject('CSV-UNSUPPORTED', 12, 'at most 10 cards per page')
    for n, row in enumerate(rows[1:], 2):
        if len(row) != len(rows[0]) or any(not x.strip() for x in row): reject('CSV-UNSUPPORTED', n, 'missing or empty columns')
    return rows


# 0.1.x comparison keys, still read until 0.3.0
YAML_OLD = {'titulo': 'title', 'subtitulo': 'subtitle', 'opcoes': 'options', 'criterios': 'criteria', 'nome': 'name', 'valores': 'values'}


def yaml_comparison(text):
    """Comparison table: title, subtitle, options and criteria (name, values). Returns the English keys."""
    # JSON is a YAML subset; block YAML below intentionally accepts only this small comparison schema.
    def bad(n, msg): reject('YAML-UNSUPPORTED', n, msg)
    old = []
    def key(k):
        if k in YAML_OLD:
            if k not in old: old.append(k)
            return YAML_OLD[k]
        return k
    def scalar(value, n):
        value = value.strip()
        if value.startswith(('"', '[')):
            try: return json.loads(value)
            except ValueError: bad(n, 'string/list needs JSON quotes')
        if not value or value.startswith(('&', '*', '!', '{', '|', '>', "'")) or ' # ' in value or ': ' in value: bad(n, value)
        return value
    def unique(pairs):
        result = {}
        for k, value in pairs:
            k = key(k)
            if k in result: bad(1, 'repeated key: ' + k)
            result[k] = value
        return result
    if text.lstrip().startswith('{'):
        try: data = json.loads(text, object_pairs_hook=unique)
        except ValueError as e: bad(1, str(e))
    else:
        data, section, item, block = {}, None, None, False
        for n, raw in enumerate(text.splitlines(), 1):
            if not raw.strip() or raw.lstrip().startswith('#'): continue
            if '\t' in raw: bad(n, 'tab character')
            if not raw.startswith(' '):
                m = re.fullmatch(r'(title|subtitle|options|criteria|titulo|subtitulo|opcoes|criterios):(?: (.+))?', raw)
                if not m or key(m[1]) in data: bad(n, raw)
                section, value = key(m[1]), m[2]
                block = value is None
                data[section] = scalar(value, n) if value else []
            elif section == 'options' and raw.startswith('  - '):
                if not block or not isinstance(data[section], list): bad(n, 'options needs a block list')
                data[section].append(scalar(raw[4:], n))
            elif section == 'criteria' and re.match(r'  - (name|nome): ', raw):
                if not block or not isinstance(data[section], list): bad(n, 'criteria needs a block list')
                field, value = raw[4:].split(': ', 1)
                item = {key(field): scalar(value, n)}; data[section].append(item)
            elif section == 'criteria' and re.match(r'    (values|valores): ', raw) and item is not None and 'values' not in item:
                field, value = raw[4:].split(': ', 1)
                item[key(field)] = scalar(value, n)
            else: bad(n, raw)
    if not isinstance(data, dict) or set(data) - {'title', 'subtitle', 'options', 'criteria'}: bad(1, 'accepted fields: title, subtitle, options, criteria')
    if not isinstance(data.get('title'), str) or not data['title']: bad(1, 'title is required')
    if 'subtitle' in data and not isinstance(data['subtitle'], str): bad(1, 'subtitle must be text')
    if not isinstance(data.get('options'), list) or not 2 <= len(data['options']) <= 4 or not all(isinstance(x, str) and x for x in data['options']): bad(1, '2 to 4 text options')
    if not isinstance(data.get('criteria'), list) or not data['criteria']: bad(1, 'criteria are required')
    for item in data['criteria']:
        if not isinstance(item, dict) or set(item) != {'name', 'values'} or not isinstance(item['name'], str) or not isinstance(item['values'], list) or len(item['values']) != len(data['options']) or not all(isinstance(x, str) and x for x in item['values']): bad(1, 'each criterion needs a name and one text value per option')
    if old: compat.warn('the comparison keys ' + ', '.join(old), ', '.join(YAML_OLD[k] for k in old))
    return data
