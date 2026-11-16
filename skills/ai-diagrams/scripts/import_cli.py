#!/usr/bin/env python3
"""Import supported source formats through the native generators and their gates."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import compat
import lang as idioma
import spec
import theme as tema
import import_data as dados
import import_mermaid as mermaid
import import_structurizr as structurizr

SKILL = Path(__file__).resolve().parents[1]
TEXT = {
    'pt-BR': ['Diagrama importado', 'Conteúdo do arquivo de entrada. O motor recalcula a disposição dos elementos.', 'Importação', 'Critério', 'Catálogo', 'Comparação'],
    'en': ['Imported diagram', 'Content from the input file. The engine recalculates the layout of the elements.', 'Import', 'Criterion', 'Catalog', 'Comparison'],
    'es': ['Diagrama importado', 'Contenido del archivo de entrada. El motor recalcula la disposición de los elementos.', 'Importación', 'Criterio', 'Catálogo', 'Comparación'],
}


def base(language):
    title, sub, kicker, *_ = TEXT[language]
    return {'idioma': language, 'titulo_pagina': title, 'cabecalho': [title, 'V1'], 'kicker': kicker,
            'h1': title, 'sub': sub, 'rodape': ['', kicker]}


def parse(path, language, requested=None):
    try:
        text = path.read_text(encoding='utf-8-sig')
    except UnicodeError as error:
        raise mermaid.ImportError('INPUT-INVALID: the file must be UTF-8') from error
    source = base(language)
    ext = path.suffix.lower()
    if ext in ('.mmd', '.mermaid'): kind, model = mermaid.parse(text, source)
    elif ext in ('.bpmn', '.xml'): kind, model = dados.bpmn(text, source)
    elif ext == '.sql': kind, model = dados.sql(text, source)
    elif ext == '.csv': kind, model = 'catalog', dados.catalog(text)
    elif ext in ('.yaml', '.yml'): kind, model = 'comparison', dados.yaml_comparison(text)
    elif ext == '.dsl':
        try:
            kind, model = 'c4', structurizr.modelo_c4(text, {'lang': language, 'title': source['h1'], 'footer': TEXT[language][2]})
        except structurizr.DSLError as error:
            raise mermaid.ImportError(str(error)) from error
    else: raise mermaid.ImportError('FORMAT-UNSUPPORTED: use .mmd, .mermaid, .bpmn, .sql, .csv, .yaml or .dsl')
    if requested and not (requested == kind or kind == 'er' and requested == 'matrix' and ext == '.sql'):
        raise mermaid.ImportError(f'TYPE-MISMATCH: {ext} produces {kind}, not {requested}')
    return requested or kind, model


def position_bpmn(model):
    """Place each topological layer in a column; cycles receive a stable BFS column."""
    nodes = {n['id']: n for n in model['nodes']}
    if any(f['from'] not in nodes or f['to'] not in nodes for f in model['flows']):
        raise mermaid.ImportError('BPMN-UNSUPPORTED: a flow names a missing node')
    layers = {n['id']: 0 for n in model['nodes'] if n['type'] == 'startEvent'}
    queue = list(layers)
    while queue:
        key = queue.pop(0)
        for flow in model['flows']:
            if flow['from'] == key and flow['to'] not in layers:
                layers[flow['to']] = layers[key] + 1
                queue.append(flow['to'])
    occupied = {}
    for key, node in nodes.items():
        node['col'] = layers.get(key, 0)
        cell = node['lane'], node['col']
        node['row'] = occupied.get(cell, 0)
        occupied[cell] = node['row'] + 1
    for flow in model['flows']:
        if layers.get(flow['to'], 0) <= layers.get(flow['from'], 0): flow['via'] = 'bottom'


def document(source, body, language, kind, theme, output):
    esc = html.escape
    tm = tema.tema(theme)
    theme_html = tema.para_gerador(tm, output or '')
    title = source.get('title', TEXT[language][4 if kind == 'catalog' else 5])
    subtitle = source.get('subtitle', TEXT[language][1])
    if not isinstance(subtitle, str): raise mermaid.ImportError('YAML-UNSUPPORTED: subtitle must be text')
    return f'''<!doctype html><html lang="{language}"><head><meta charset="utf-8">
<meta name="lang" content="{language}"><title>{esc(title)}</title>
{theme_html['link']}{theme_html['meta']}<style>/*STYLE*/</style></head><body><div class="page">
<div class="hdr"><span>{esc(title)}</span><span>V1</span></div>
<div class="kicker"><span class="sq">■</span> {esc(TEXT[language][2])}</div>
<h1>{esc(title)}</h1><div class="sub">{esc(subtitle)}</div>{body}
<div class="foot">{esc(TEXT[language][2])}</div></div></body></html>'''


def native_html(kind, model, language, theme, output=None):
    esc = html.escape
    if kind == 'catalog':
        headers, *rows = model
        cards = []
        for i, row in enumerate(rows, 1):
            # Five source columns fit the native card as name, three facts and slug.
            facts = ''.join(f'<div class="linha"><div class="rot">{esc(k)}</div><div class="txt">{esc(v)}</div></div>' for k, v in zip(headers[1:4], row[1:4]))
            slug = f'<div class="slug">{esc(headers[4])}: {esc(row[4])}</div>' if len(row) == 5 else ''
            cards.append(f'<div class="card"><div class="sid">{i:02d} · {esc(headers[0])}</div><div class="snome">{esc(row[0])}</div>{facts}{slug}</div>')
        return document({}, '<div class="grid">' + ''.join(cards) + '</div>', language, kind, theme, output)
    header = '<tr><th>' + esc(TEXT[language][3]) + '</th>' + ''.join('<th>' + esc(x) + '</th>' for x in model['options']) + '</tr>'
    rows = ''.join('<tr><td>' + esc(c['name']) + '</td>' + ''.join('<td>' + esc(x) + '</td>' for x in c['values']) + '</tr>' for c in model['criteria'])
    return document(model, '<table class="comp">' + header + rows + '</table>', language, kind, theme, output)


def er_layout(model, schema, model_name):
    tables = {k: v for k, v in model['tabelas'].items() if k.split('.')[0] == schema}
    positions, y = {}, 60
    for key, table in tables.items():
        positions[key] = {'x': 700, 'y': y, 'w': 500, 'desc': table['rotulo']}
        y += 130 + 24 * len(table['colunas'])
    edges, arrivals = [], {}
    for key, table in tables.items():
        for column in table['colunas']:
            if column[2] != 'FK' or column[3] not in tables: continue
            target = column[3]
            arrivals[target] = arrivals.get(target, 0) + 1
            edges.append({'de': key, 'coluna': column[0], 'sai': 'L', 'para': target, 'chega': 'L',
                          'raia': 650 - len(edges) * 34, 'dy': 8 + arrivals[target] * 6,
                          'texto': table.get('relacoes', {}).get(column[0], key + '.' + column[0] + ' → ' + target)})
    # shortcut: 16 internal FK corridors fit the canvas; use a routing engine before accepting larger schemas.
    if len(edges) > 16:
        raise mermaid.ImportError('SQL-UNSUPPORTED: the automatic layout takes at most 16 internal FKs per schema; split the model')
    return {'modelo': model_name, 'schema': schema, 'titulo': model['schemas'][schema], 'sub': TEXT[model['idioma']][1],
            'canvas': {'w': 1700}, 'tabelas': positions, 'arestas': edges, 'idioma': model['idioma']}


def run(command):
    result = subprocess.run([str(x) for x in command])
    if result.returncode: raise SystemExit(result.returncode)


def public(kind, model):
    """Internal model -> the public (English) spec a user reads and edits."""
    if kind == 'bpmn':
        out = spec.escrever('bpmn', model)
        if 'idioma' in out: out['lang'] = out.pop('idioma')
        return out
    out = spec.escrever({'er': 'er_model', 'matrix': 'er_model'}.get(kind, kind), model)
    for table in out.get('tables', {}).values():
        # relationship labels from Mermaid; the layout already carries them as edge text
        if 'relacoes' in table: table['relations'] = table.pop('relacoes')
    return out


def generate(path, out, language, requested=None, source_only=False, theme=None):
    stem = path.stem
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / (stem + '.import.json')
    def rel(p): return os.path.relpath(p, out)
    report_path.write_text(json.dumps({'input': rel(path), 'gate': 'pending', 'sources': []}) + '\n', encoding='utf-8')
    kind, model = parse(path, language, requested)
    src = out / '_src'
    if kind in ('er', 'matrix'): src = src / stem
    src.mkdir(parents=True, exist_ok=True)
    flags = ['--lang', language] + (['--theme', theme] if theme else [])
    commands, htmls = [], []
    def write_json(file, value): file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if kind == 'bpmn':
        if any((out / (stem + suffix)).resolve() == path.resolve() for suffix in ('.bpmn', '.html', '.png')):
            raise mermaid.ImportError('OUTPUT-CONFLICT: the output would replace the input file; choose another --out')
        position_bpmn(model)
        native = src / (stem + '.json'); write_json(native, public(kind, model))
        command = [sys.executable, SKILL / 'bpmn/build_bpmn.py', native, '--out', out] + flags
        run(command + (['--no-chrome'] if source_only else []))
        htmls = [out / (stem + '.html')]
    elif kind == 'c4':
        native = src / (stem + '.json'); write_json(native, model)
        # build_c4.py writes one source per view and builds each one through build.py (or only the sources)
        run([sys.executable, SKILL / 'scripts/build_c4.py', native] + flags + (['--no-build'] if source_only else []))
        htmls = sorted(src.glob(stem + '*.html'), key=lambda p: (p.name != stem + '.html', p.name))
    elif kind in ('swimlanes', 'sequence', 'states'):
        native = src / (stem + '.json'); write_json(native, public(kind, model))
        run([sys.executable, SKILL / ('scripts/build_' + kind + '.py'), native] + flags)
        htmls = [native.with_suffix('.html')]
        commands = [[sys.executable, SKILL / 'scripts/conceptual.py', htmls[0]] + flags]
    elif kind in ('er', 'matrix'):
        native = src / (stem + '.model.json'); write_json(native, public(kind, model))
        if kind == 'matrix':
            htmls = [src / (stem + '.html')]
            run(['node', SKILL / 'er/er-overview.mjs', native, htmls[0]] + flags)
        else:
            for schema in model['schemas']:
                if not any(k.split('.')[0] == schema for k in model['tabelas']): continue
                layout = src / ('er-' + schema + '.layout.mjs')
                value = spec.escrever('er_layout', er_layout(model, schema, native.name))
                layout.write_text('export default ' + json.dumps(value, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
                run(['node', SKILL / 'er/er-build.mjs', layout] + flags)
                htmls.append(src / ('er-' + schema + '.html'))
        commands = [[sys.executable, SKILL / 'scripts/build.py', file, '--out', out / stem] + flags for file in htmls]
    else:
        htmls = [src / (stem + '.html')]
        htmls[0].write_text(native_html(kind, model, language, theme, htmls[0]), encoding='utf-8')
        gate = 'conceptual.py' if kind == 'catalog' else 'build.py'
        commands = [[sys.executable, SKILL / ('scripts/' + gate), htmls[0]] + flags]
    if not source_only:
        for command in commands: run(command)
    report = {'input': rel(path), 'type': kind, 'language': language, 'sources': [rel(p) for p in htmls],
              'gate': 'pending' if source_only else 'passed'}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('IMPORTED: ' + kind + ('; source written, gate and PNG pending (--source-only)' if source_only else '; gate passed'))
    return report


TYPES = ['er', 'matrix', 'bpmn', 'swimlanes', 'sequence', 'states', 'catalog', 'comparison', 'c4']
OLD_TYPES = {'der': 'er', 'matriz': 'matrix', 'raias': 'swimlanes', 'sequencia': 'sequence', 'estados': 'states',
             'catalogo': 'catalog', 'comparacao': 'comparison'}
# new flag -> 0.1.x flag, still accepted until 0.3.0
OLD_FLAGS = {'type': 'tipo', 'out': 'saida', 'lang': 'idioma', 'theme': 'tema', 'source_only': 'somente_fonte'}


def main(argv=None):
    parser = argparse.ArgumentParser(prog='ai-diagrams import', description=__doc__)
    parser.add_argument('file', type=Path, help='input file: .mmd, .mermaid, .bpmn, .sql, .csv, .yaml or .dsl (Structurizr)')
    parser.add_argument('--type', metavar='TYPE', help='expected diagram type: ' + ', '.join(TYPES))
    parser.add_argument('--out', type=Path, help='output folder (default: diagrams)')
    parser.add_argument('--lang', help='pt-BR, en or es')
    parser.add_argument('--theme', help='theme name or .json path')
    parser.add_argument('--source-only', action='store_true', help='write the source through the engine; visual gate and PNG stay pending')
    parser.add_argument('--tipo', help=argparse.SUPPRESS)
    parser.add_argument('--saida', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--idioma', help=argparse.SUPPRESS)
    parser.add_argument('--tema', help=argparse.SUPPRESS)
    parser.add_argument('--somente-fonte', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    for new, old in OLD_FLAGS.items():
        if getattr(args, old) not in (None, False):
            compat.warn('--' + old.replace('_', '-'), '--' + new.replace('_', '-'))
            if getattr(args, new) in (None, False): setattr(args, new, getattr(args, old))
    kind = args.type
    if kind in OLD_TYPES:
        compat.warn('--type ' + kind, '--type ' + OLD_TYPES[kind])
        kind = OLD_TYPES[kind]
    if kind is not None and kind not in TYPES:
        parser.error('--type: invalid choice %r (choose from %s)' % (kind, ', '.join(TYPES)))
    language = idioma.idioma(args.lang)['_codigo']
    try:
        generate(args.file.resolve(), (args.out or Path('diagrams')).resolve(), language, kind, args.source_only, args.theme)
    except (mermaid.ImportError, OSError) as e:
        parser.exit(1, str(e) + '\n')


if __name__ == '__main__': main()
