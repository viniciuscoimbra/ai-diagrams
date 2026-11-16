// The compatibility table of docs/models.md, written from docs/models/runs.json.
// Usage: node site/src/models-table.mjs           prints the table
//        node site/src/models-table.mjs --write   replaces the table between the markers in docs/models.md
import {readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve, join} from 'node:path';
import {fileURLToPath} from 'node:url';

const SUP = {0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹'};
const sup = n => String(n).split('').map(d => SUP[d]).join('');
const TYPE_NAMES = {
  'aws-architecture': 'AWS architecture poster', 'step-flow': 'Numbered-step flow', 'comparison-table': 'Comparison table',
  'er-schema': 'ER diagram per schema', 'dependency-matrix': 'Schema dependency matrix', swimlanes: 'Swimlanes',
  'card-catalog': 'Cards catalog', bpmn: 'BPMN 2.0', sequence: 'Sequence diagram', 'state-machine': 'State machine', c4: 'C4 container diagram',
};
const WORD = {pass: 'pass', gate_only: 'gate 0', defect: 'defect', fail: 'fail', not_measured: 'not measured'};
export const START = '<!-- models-table:start (written by site/src/models-table.mjs from docs/models/runs.json) -->';
export const END = '<!-- models-table:end -->';

export function modelsTable(runs) {
  const id = column => `${column.cli}:${column.model || 'default'}`;
  const head = ['Type', ...runs.columns.map(c => [c.cli_label, c.model_label].filter(Boolean).join(' · '))];
  const lines = [`| ${head.join(' | ')} |`, `|${head.map(() => '---').join('|')}|`];
  for (const type of runs.types) {
    const cells = runs.columns.map(column => {
      const run = runs.runs.find(r => r.type === type && `${r.cli}:${r.model || 'default'}` === id(column));
      if (!run) return 'not measured';
      return `${WORD[run.result]}${run.note ? `: ${run.note}` : ''}${run.source ? ` ${sup(run.source)}` : ''}`;
    });
    lines.push(`| ${TYPE_NAMES[type] || type} | ${cells.join(' | ')} |`);
  }
  return `${START}\n${lines.join('\n')}\n${END}`;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
  const runs = JSON.parse(await readFile(join(repo, 'docs/models/runs.json'), 'utf8'));
  const table = modelsTable(runs);
  if (process.argv.includes('--write')) {
    const path = join(repo, 'docs/models.md');
    const md = await readFile(path, 'utf8');
    const s = md.indexOf(START), e = md.indexOf(END);
    if (s < 0 || e < 0) throw new Error('docs/models.md has no models-table markers');
    await writeFile(path, md.slice(0, s) + table + md.slice(e + END.length));
    console.log('docs/models.md table written');
  } else console.log(table);
}
