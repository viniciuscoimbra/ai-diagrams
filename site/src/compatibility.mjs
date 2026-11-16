// Data of the compatibility page, read from the files the tests and runs write; nothing here is typed by hand.
//   docs/models/runs.json            measured runs of each diagram type per CLI and model
//   docs/models/gates.json           gate result of each template (skills/ai-diagrams/templates/build-all.sh)
//   docs/models/install-checks.json  npm install checks (tests/npm-smoke.sh)
//   examples/import/manifest.json    import samples (examples/import/build-all.sh)
// Every cell becomes one of three states: pass (green), fail (red), none (gray, not measured).
import {readFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {join} from 'node:path';
import assert from 'node:assert/strict';

export const STATE = {pass: 'pass', gate_only: 'pass', defect: 'fail', fail: 'fail', not_measured: 'none'};

const readJson = async path => existsSync(path) ? JSON.parse(await readFile(path, 'utf8')) : null;

export async function compatibility(repo, importManifest) {
  const runs = await readJson(join(repo, 'docs/models/runs.json'));
  assert(runs, 'docs/models/runs.json is missing');
  const columns = runs.columns;
  const cells = runs.types.map(type => ({
    type,
    cells: columns.map(column => {
      const run = runs.runs.find(item => item.type === type && `${item.cli}:${item.model || 'default'}` === column.id);
      if (!run) return {state: 'none', result: 'not_measured'};
      assert(run.result in STATE, `Unknown result in runs.json: ${run.result}`);
      return {state: STATE[run.result], result: run.result, note: run.note, source: run.source};
    }),
  }));
  for (const row of cells) for (const [i, cell] of row.cells.entries()) {
    const n = runs.runs.filter(item => item.type === row.type && `${item.cli}:${item.model || 'default'}` === columns[i].id).length;
    assert(n <= 1, `Two runs for one cell: ${row.type} / ${columns[i].id}`);
  }

  const gates = await readJson(join(repo, 'docs/models/gates.json'));
  const gateRows = runs.types.map(type => ({type, state: gates?.types?.[type] === 'pass' ? 'pass' : gates?.types?.[type] === 'fail' ? 'fail' : 'none'}));

  const install = await readJson(join(repo, 'docs/models/install-checks.json'));
  const installRows = (install?.checks || []).map(check => ({...check, state: check.result === 'pass' ? 'pass' : check.result === 'fail' ? 'fail' : 'none'}));

  const importRows = importManifest.map(item => ({
    id: item.id, language: item.language, type: item.type,
    tested: item.tested === true ? 'pass' : 'fail',
    gate: item.gate === 'passed' ? 'pass' : item.gate === 'failed' ? 'fail' : 'none',
  }));

  return {
    results: runs.results, sources: runs.sources, columns, rows: cells,
    gates: {date: gates?.date ?? null, platform: gates?.platform ?? null, rows: gateRows},
    install: {date: install?.date ?? null, package: install?.package ?? null, node: install?.node ?? null, platform: install?.platform ?? null, rows: installRows},
    imports: importRows,
  };
}
