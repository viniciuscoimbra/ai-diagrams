import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const [cli, tmp] = process.argv.slice(2);
const home = process.env.HOME;
assert.equal(path.resolve(home), path.resolve(tmp, 'home'), 'Tests require an isolated HOME');
const pkg = path.dirname(path.dirname(fs.realpathSync(cli)));
const skill = path.join(pkg, 'skills/ai-diagrams');
const run = (...args) => spawnSync(cli, args, { encoding: 'utf8' });
const succeeds = (...args) => {
  const result = run(...args);
  assert.equal(result.status, 0, result.stderr);
  return result;
};
const fails = (...args) => {
  const result = run(...args);
  assert.equal(result.status, 1, result.stdout);
  return result;
};
const manifest = JSON.parse(fs.readFileSync(path.join(pkg, 'package.json'), 'utf8'));
assert.equal(manifest.name, 'ai-diagrams');
assert.equal(manifest.license, 'MIT');
assert.equal(manifest.author, 'Vinícius Coimbra <viniciuscoimbra@gmail.com>');
assert.equal(Object.keys(manifest.dependencies || {}).length, 0);
for (const relative of ['SKILL.md', 'scripts/importar.py', 'scripts/build.py', 'bpmn/vendor/LICENSE', 'estados/vendor/LICENSE.md', 'i18n/en.json', 'i18n/es.json', 'i18n/pt-BR.json']) assert.ok(fs.existsSync(path.join(skill, relative)), relative);
assert.equal(fs.readdirSync(path.join(skill, 'modelos'), { withFileTypes: true }).filter(file => file.isDirectory()).length, 11);
function checkPackage(dir) {
  for (const file of fs.readdirSync(dir, { withFileTypes: true })) {
    assert.ok(!['node_modules', '__pycache__', 'site-pranchas', 'brand', '.git', 'testes', 'evals'].includes(file.name), file.name);
    assert.ok(!/\.(?:png|tgz|pyc)$|\.test\.mjs$/.test(file.name), file.name);
    if (file.isDirectory()) checkPackage(path.join(dir, file.name));
  }
}
checkPackage(pkg);

for (const tool of ['claude', 'codex']) {
  succeeds('install', `--${tool}`);
  const link = path.join(home, `.${tool}/skills/ai-diagrams`);
  assert.equal(fs.realpathSync(link), skill);
  assert.match(succeeds('install', `--${tool}`).stdout, /Já instalado/);
  const project = path.join(tmp, `project ${tool}`);
  succeeds('install', `--${tool}`, '--projeto', project);
  assert.equal(fs.realpathSync(path.join(project, `.${tool}/skills/ai-diagrams`)), skill);
}
const occupied = path.join(tmp, 'existing');
const existingSkill = path.join(occupied, '.claude/skills/ai-diagrams');
fs.mkdirSync(existingSkill, { recursive: true });
fs.writeFileSync(path.join(existingSkill, 'keep.txt'), 'do not replace');
assert.match(fails('install', '--claude', '--projeto', occupied).stderr, /preservada/);
assert.equal(fs.readFileSync(path.join(existingSkill, 'keep.txt'), 'utf8'), 'do not replace');
fs.rmSync(existingSkill, { recursive: true });
fs.symlinkSync(path.join(tmp, 'missing'), existingSkill);
assert.match(fails('install', '--claude', '--projeto', occupied).stderr, /preservada/);
assert.equal(fs.readlinkSync(existingSkill), path.join(tmp, 'missing'));

const kiro = path.join(tmp, 'project kiro');
succeeds('install', '--kiro', '--projeto', kiro);
assert.ok(!fs.lstatSync(path.join(kiro, '.kiro/skills/ai-diagrams')).isSymbolicLink());
assert.ok(fs.existsSync(path.join(kiro, '.kiro/skills/ai-diagrams/SKILL.md')));
for (const file of ['agents/ai-diagrams.json', 'steering/ai-diagrams.md']) assert.equal(fs.readFileSync(path.join(kiro, '.kiro', file), 'utf8'), fs.readFileSync(path.join(pkg, 'kiro', file), 'utf8'));
fs.writeFileSync(path.join(kiro, '.kiro/skills/ai-diagrams/keep.txt'), 'preserve');
assert.match(fails('install', '--kiro', '--projeto', kiro).stderr, /preservada/);
assert.equal(fs.readFileSync(path.join(kiro, '.kiro/skills/ai-diagrams/keep.txt'), 'utf8'), 'preserve');
for (const args of [['install'], ['install', '--claude', '--codex'], ['install', '--claude', '--projeto'], ['doctor', '--unknown'], ['unknown']]) fails(...args);
assert.match(succeeds('importar', '--help').stdout, /--saida/);
const input = path.join(tmp, 'sequence with spaces.mmd');
const output = path.join(tmp, 'import result');
fs.writeFileSync(input, 'sequenceDiagram\nparticipant A as Caller\nparticipant B as API\nA->>B: request\nB-->>A: response\n');
succeeds('importar', input, '--saida', output, '--idioma', 'en', '--somente-fonte');
const report = JSON.parse(fs.readFileSync(path.join(output, 'sequence with spaces.importacao.json'), 'utf8'));
assert.equal(report.type, 'sequencia');
assert.equal(report.language, 'en');
assert.equal(report.gate, 'pending');
assert.ok(report.sources.every(file => fs.existsSync(file)));
assert.ok(fs.readFileSync(report.sources[0], 'utf8').includes('request'));
const doctor = run('doctor');
assert.ok([0, 1].includes(doctor.status));
for (const label of ['Node:', 'Python:', 'Chrome:']) assert.ok(doctor.stdout.includes(label), doctor.stdout);
console.log(doctor.stdout.trim());
console.log('OK npm smoke: archive, isolated install, Claude/Codex links, Kiro copies, conflict preservation and importer dispatch.');
