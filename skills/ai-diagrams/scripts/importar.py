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

import idioma
import tema
import importar_dados as dados
import importar_mermaid as mermaid

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
        raise mermaid.ImportError('ENTRADA-INVALIDA: o arquivo precisa usar UTF-8') from error
    source = base(language)
    ext = path.suffix.lower()
    if ext in ('.mmd', '.mermaid'): kind, model = mermaid.parse(text, source)
    elif ext in ('.bpmn', '.xml'): kind, model = dados.bpmn(text, source)
    elif ext == '.sql': kind, model = dados.sql(text, source)
    elif ext == '.csv': kind, model = 'catalogo', dados.catalog(text)
    elif ext in ('.yaml', '.yml'): kind, model = 'comparacao', dados.yaml_comparison(text)
    else: raise mermaid.ImportError('FORMATO-NAO-SUPORTADO: use .mmd, .mermaid, .bpmn, .sql, .csv ou .yaml')
    if requested and not (requested == kind or kind == 'der' and requested == 'matriz' and ext == '.sql'):
        raise mermaid.ImportError(f'TIPO-INCOMPATIVEL: {ext} produz {kind}, não {requested}')
    return requested or kind, model


def position_bpmn(model):
    """Place each topological layer in a column; cycles receive a stable BFS column."""
    nodes = {n['id']: n for n in model['nodes']}
    if any(f['from'] not in nodes or f['to'] not in nodes for f in model['flows']):
        raise mermaid.ImportError('BPMN-NAO-SUPORTADO: fluxo cita nó inexistente')
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
    title = source.get('titulo', TEXT[language][4 if kind == 'catalogo' else 5])
    subtitle = source.get('subtitulo', TEXT[language][1])
    if not isinstance(subtitle, str): raise mermaid.ImportError('YAML-NAO-SUPORTADO: subtitulo deve ser texto')
    return f'''<!doctype html><html lang="{language}"><head><meta charset="utf-8">
<meta name="idioma" content="{language}"><title>{esc(title)}</title>
{theme_html['link']}{theme_html['meta']}<style>/*ESTILO*/</style></head><body><div class="page">
<div class="hdr"><span>{esc(title)}</span><span>V1</span></div>
<div class="kicker"><span class="sq">■</span> {esc(TEXT[language][2])}</div>
<h1>{esc(title)}</h1><div class="sub">{esc(subtitle)}</div>{body}
<div class="foot">{esc(TEXT[language][2])}</div></div></body></html>'''


def native_html(kind, model, language, theme, output=None):
    esc = html.escape
    if kind == 'catalogo':
        headers, *rows = model
        cards = []
        for i, row in enumerate(rows, 1):
            # Five source columns fit the native card as name, three facts and slug.
            facts = ''.join(f'<div class="linha"><div class="rot">{esc(k)}</div><div class="txt">{esc(v)}</div></div>' for k, v in zip(headers[1:4], row[1:4]))
            slug = f'<div class="slug">{esc(headers[4])}: {esc(row[4])}</div>' if len(row) == 5 else ''
            cards.append(f'<div class="card"><div class="sid">{i:02d} · {esc(headers[0])}</div><div class="snome">{esc(row[0])}</div>{facts}{slug}</div>')
        return document({}, '<div class="grid">' + ''.join(cards) + '</div>', language, kind, theme, output)
    header = '<tr><th>' + esc(TEXT[language][3]) + '</th>' + ''.join('<th>' + esc(x) + '</th>' for x in model['opcoes']) + '</tr>'
    rows = ''.join('<tr><td>' + esc(c['nome']) + '</td>' + ''.join('<td>' + esc(x) + '</td>' for x in c['valores']) + '</tr>' for c in model['criterios'])
    return document(model, '<table class="comp">' + header + rows + '</table>', language, kind, theme, output)


def der_layout(model, schema, model_name):
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
        raise mermaid.ImportError('SQL-NAO-SUPORTADO: layout automático limitado a 16 FKs internas por schema; divida o modelo')
    return {'modelo': model_name, 'schema': schema, 'titulo': model['schemas'][schema], 'sub': TEXT[model['idioma']][1],
            'canvas': {'w': 1700}, 'tabelas': positions, 'arestas': edges, 'idioma': model['idioma']}


def run(command):
    result = subprocess.run([str(x) for x in command])
    if result.returncode: raise SystemExit(result.returncode)


def generate(path, out, language, requested=None, source_only=False, theme=None):
    stem = path.stem
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / (stem + '.importacao.json')
    report_path.write_text(json.dumps({'input': str(path), 'gate': 'pending', 'sources': []}) + '\n', encoding='utf-8')
    kind, model = parse(path, language, requested)
    src = out / '_src'
    if kind in ('der', 'matriz'): src = src / stem
    src.mkdir(parents=True, exist_ok=True)
    flags = ['--idioma', language] + (['--tema', theme] if theme else [])
    commands, htmls = [], []
    def write_json(file, value): file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if kind == 'bpmn':
        if any((out / (stem + suffix)).resolve() == path.resolve() for suffix in ('.bpmn', '.html', '.png')):
            raise mermaid.ImportError('SAIDA-CONFLITA: a saída substituiria o arquivo de entrada; escolha outro --saida')
        position_bpmn(model)
        native = src / (stem + '.json'); write_json(native, model)
        command = [sys.executable, SKILL / 'bpmn/gerar_bpmn.py', native, '--out', out] + flags
        run(command + (['--sem-chrome'] if source_only else []))
        htmls = [out / (stem + '.html')]
    elif kind in ('raias', 'sequencia', 'estados'):
        native = src / (stem + '.json'); write_json(native, model)
        run([sys.executable, SKILL / ('scripts/gerar_' + kind + '.py'), native] + flags)
        htmls = [native.with_suffix('.html')]
        commands = [[sys.executable, SKILL / 'scripts/conceitual.py', htmls[0]] + flags]
    elif kind in ('der', 'matriz'):
        native = src / (stem + '.modelo.json'); write_json(native, model)
        if kind == 'matriz':
            htmls = [src / (stem + '.html')]
            run(['node', SKILL / 'der/der-visao-geral.mjs', native, htmls[0]] + flags)
        else:
            for schema in model['schemas']:
                if not any(k.split('.')[0] == schema for k in model['tabelas']): continue
                layout = src / ('der-' + schema + '.layout.mjs')
                layout.write_text('export default ' + json.dumps(der_layout(model, schema, native.name), ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
                run(['node', SKILL / 'der/der-montar.mjs', layout] + flags)
                htmls.append(src / ('der-' + schema + '.html'))
        commands = [[sys.executable, SKILL / 'scripts/build.py', file, '--out', out / stem] + flags for file in htmls]
    else:
        htmls = [src / (stem + '.html')]
        htmls[0].write_text(native_html(kind, model, language, theme, htmls[0]), encoding='utf-8')
        gate = 'conceitual.py' if kind == 'catalogo' else 'build.py'
        commands = [[sys.executable, SKILL / ('scripts/' + gate), htmls[0]] + flags]
    if not source_only:
        for command in commands: run(command)
    report = {'input': str(path), 'type': kind, 'language': language, 'sources': [str(p) for p in htmls],
              'gate': 'pending' if source_only else 'passed'}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('IMPORTADO: ' + kind + ('; fonte gerado, gate e PNG pendentes (--somente-fonte)' if source_only else '; gate aprovado'))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo', type=Path)
    parser.add_argument('--tipo', choices=['der', 'matriz', 'bpmn', 'raias', 'sequencia', 'estados', 'catalogo', 'comparacao'])
    parser.add_argument('--saida', type=Path, default=Path('diagramas'))
    parser.add_argument('--idioma')
    parser.add_argument('--tema')
    parser.add_argument('--somente-fonte', action='store_true', help='gera o fonte pelo motor; gate visual e PNG ficam pendentes')
    args = parser.parse_args(argv)
    language = idioma.idioma(args.idioma)['_codigo']
    try:
        generate(args.arquivo.resolve(), args.saida.resolve(), language, args.tipo, args.somente_fonte, args.tema)
    except (mermaid.ImportError, OSError) as e:
        parser.exit(1, str(e) + '\n')


if __name__ == '__main__': main()
