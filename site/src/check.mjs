// Static audit of site/out, without a browser: every page and diagram exists, every local reference resolves,
// nothing is fetched from outside, the editor's theme CSS equals the engine's, and the compatibility data is complete.
import assert from 'node:assert/strict';
import {readFile, readdir, stat} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {dirname, resolve, join, relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {languages, importGateMessage} from './i18n.mjs';
import {themeTokens, validate, toV2, exportTheme, GROUPS} from './preview.mjs';
import {compatibility, STATE} from './compatibility.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../..');
const out = resolve(here, '../out');
const pages = ['01-home.html', '02-diagrams.html', '03-aws-architecture.html', '04-themes.html', '05-compatibility.html', '06-brand.html', '07-import.html', 'index.html'];
const failures = [];
let passed = 0;
async function check(label, run) {
  try { await run(); passed++; console.log(`OK ${label}`); }
  catch (error) { failures.push(`${label}: ${error.message}`); console.error(`FAIL ${label}: ${error.message}`); }
}
async function walk(dir) {
  const list = [];
  for (const entry of await readdir(dir, {withFileTypes: true})) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) list.push(...await walk(path)); else list.push(path);
  }
  return list;
}
const files = await walk(out);
const htmls = files.filter(file => file.endsWith('.html'));
const declarations = css => [...css.matchAll(/--([\w-]+):([^;]+);/g)].map(m => `${m[1]}=${m[2].trim()}`).filter(d => !d.startsWith('frame-visibility'));
const python = (...args) => execFileSync('python3', [join(repo, 'skills/ai-diagrams/scripts/theme.py'), ...args], {encoding: 'utf8'});

await check('every page exists in every language', async () => {
  for (const language of languages) for (const page of pages) assert(existsSync(join(out, language === 'en' ? '' : language, page)), `${language}/${page}`);
});

await check('11 example diagrams, 5 more C4 views and 9 imports per language', async () => {
  for (const language of languages) {
    const list = (await readdir(join(out, 'diagrams', language))).filter(f => f.endsWith('.html'));
    assert.equal(list.filter(f => !f.startsWith('import-') && !f.startsWith('c4-')).length, 11, language);
    // landscape, context, components, dynamic and deployment; the container view is c4.html
    assert.equal(list.filter(f => f.startsWith('c4-')).length, 5, language);
    assert.equal(list.filter(f => f.startsWith('import-')).length, 9, language);
  }
});

await check('local references resolve and nothing is fetched from another host', async () => {
  const problems = [];
  for (const file of [...htmls, ...files.filter(f => f.endsWith('.css'))]) {
    const source = await readFile(file, 'utf8');
    const refs = [...source.matchAll(/<(?:link|script|img|iframe)\b[^>]*?\s(?:href|src)="([^"]+)"/gi)].map(m => m[1])
      .concat([...source.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)].map(m => m[1]));
    for (const ref of refs) {
      if (ref.startsWith('data:') || ref.startsWith('#') || ref.startsWith('blob:')) continue;
      if (/^https?:\/\//.test(ref)) { problems.push(`${relative(out, file)} loads ${ref}`); continue; }
      const target = resolve(dirname(file), ref.split(/[?#]/)[0]);
      if (!existsSync(target)) problems.push(`${relative(out, file)} -> ${ref}`);
    }
    const markup = source.replace(/<script\b[^>]*>[^]*?<\/script>/gi, '');
    for (const m of markup.matchAll(/<a\b[^>]*\shref="([^"]+)"/gi)) {
      const ref = m[1];
      if (/^(?:https?:|mailto:|#|data:|blob:)/.test(ref)) continue;
      if (!existsSync(resolve(dirname(file), ref.split(/[?#]/)[0]))) problems.push(`${relative(out, file)} links ${ref}`);
    }
  }
  assert.deepEqual(problems.slice(0, 10), []);
});

await check('no em dash in pages or diagrams', async () => {
  for (const file of htmls) assert(!(await readFile(file, 'utf8')).includes('—'), relative(out, file));
});

// the names are assembled here so this file does not carry them either
const privateNames = new RegExp([['refy', 'ui'], ['dommus', 'platform'], ['ply', 'ngo']].map(parts => parts.join(parts[0] === 'ply' ? '' : '-')).join('|'));
await check('no private repository is named', async () => {
  for (const file of files.filter(f => /\.(html|css|js|json|txt|svg)$/.test(f))) {
    assert(!privateNames.test(await readFile(file, 'utf8')), relative(out, file));
  }
});

await check('every diagram carries the theme root, the runtime and the shared fonts', async () => {
  for (const file of htmls.filter(f => f.includes('/diagrams/'))) {
    const source = await readFile(file, 'utf8');
    assert(source.includes('<style id="ai-diagrams-theme">:root{'), relative(out, file));
    assert(source.includes("type: 'ai-diagrams:pick'"), `${relative(out, file)}: runtime`);
    assert(source.includes('href="../../assets/diagram-fonts.css"'), `${relative(out, file)}: fonts`);
  }
});

await check('the editor writes the same theme CSS as skills/ai-diagrams/scripts/theme.py', async () => {
  for (const name of ['ai-diagrams', 'paper']) {
    const theme = JSON.parse(await readFile(join(repo, `skills/ai-diagrams/themes/${name}.json`), 'utf8'));
    assert.deepEqual(declarations(themeTokens(theme)), declarations(python('--theme', name, '--css')), name);
  }
  // a random theme, written to a temp file the engine reads
  const {mkdtemp, writeFile} = await import('node:fs/promises');
  const {tmpdir} = await import('node:os');
  const theme = structuredClone(validate(JSON.parse(await readFile(join(repo, 'skills/ai-diagrams/themes/ai-diagrams.json'), 'utf8'))));
  let seed = 7;
  const random = () => (seed = (seed * 48271) % 2147483647) / 2147483647;
  for (const group of Object.keys(GROUPS)) for (const key of GROUPS[group]) theme[group][key] = '#' + Math.floor(random() * 0xffffff).toString(16).padStart(6, '0').toUpperCase();
  theme.fonts = {text: 'Inter', mono: 'JetBrains Mono'};
  const path = join(await mkdtemp(join(tmpdir(), 'ai-diagrams-theme-')), 'random.json');
  await writeFile(path, JSON.stringify(exportTheme(theme)));
  assert.deepEqual(declarations(themeTokens(theme)), declarations(python('--theme', path, '--css')));
});

await check('a schema_version 1 theme converts to the same v2 theme as theme.py', async () => {
  const v2 = JSON.parse(await readFile(join(repo, 'skills/ai-diagrams/themes/paper.json'), 'utf8'));
  const back = {versao_schema: 1, nome: v2.name, empresa: v2.company, logo: v2.logo,
    cores: {tinta: v2.colors.ink, apoio: v2.colors.support, cinza: v2.colors.muted, zona: v2.colors.zone, papel: v2.colors.paper, acento: v2.colors.accent, risco: v2.colors.risk, risco_fundo: v2.colors.risk_bg}};
  const converted = toV2(back);
  assert.deepEqual(converted.colors, v2.colors);
  assert.throws(() => validate({schema_version: 2, colors: {}}), /THEME-INCOMPLETE/);
  assert.throws(() => validate({...v2, colors: {...v2.colors, ink: 'black'}}), /THEME-INVALID: colors.ink/);
});

await check('compatibility data: 11 types × every column, three states only, sources exist', async () => {
  const manifest = JSON.parse(await readFile(join(repo, 'examples/import/manifest.json'), 'utf8'));
  const data = await compatibility(repo, manifest);
  assert.equal(data.rows.length, 11);
  for (const row of data.rows) {
    assert.equal(row.cells.length, data.columns.length);
    for (const cell of row.cells) {
      assert(['pass', 'fail', 'none'].includes(cell.state));
      if (cell.source) assert(data.sources[String(cell.source)], `source ${cell.source}`);
    }
  }
  assert.deepEqual(new Set(Object.values(STATE)), new Set(['pass', 'fail', 'none']));
  for (const item of manifest) importGateMessage(item.gate);
});

await check('docs/models.md carries the same table as docs/models/runs.json', async () => {
  const runs = JSON.parse(await readFile(join(repo, 'docs/models/runs.json'), 'utf8'));
  const md = await readFile(join(repo, 'docs/models.md'), 'utf8');
  const {modelsTable} = await import('./models-table.mjs');
  assert(md.includes(modelsTable(runs)), 'run `node site/src/models-table.mjs --write` and commit docs/models.md');
});

await check('total size stays small', async () => {
  let total = 0;
  for (const file of files) total += (await stat(file)).size;
  assert(total < 60 * 1048576, `${(total / 1048576).toFixed(1)} MB`);
  console.log(`   ${files.length} files, ${(total / 1048576).toFixed(1)} MB`);
});

console.log(`${passed} checks passed, ${failures.length} failed`);
if (failures.length) process.exit(1);
