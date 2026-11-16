#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const skill = path.join(root, 'skills/ai-diagrams');
const help = `ai-diagrams install --claude|--codex|--kiro [--project <dir>]
ai-diagrams doctor
ai-diagrams import <file> [--type X] [--out dir] [--lang pt-BR|en|es] [--theme name|path.json]

Claude/Codex: global links; --project installs into a project.
Kiro: a copy in the project, the current folder by default.
Run import --help for the conversion options.`;
const deprecated = (old, current) => console.error(`ai-diagrams: ${old} is deprecated; use ${current}`);

function exists(file) {
  try { return fs.lstatSync(file); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

async function install(args) {
  let cli, project;
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (['--claude', '--codex', '--kiro'].includes(arg) && !cli) cli = arg.slice(2);
    else if (['--project', '--projeto'].includes(arg) && !project && args[i + 1] && !args[i + 1].startsWith('--')) {
      if (arg === '--projeto') deprecated('--projeto', '--project');
      project = path.resolve(args[++i]);
    } else throw new Error(`Invalid argument: ${arg}\n${help}`);
  }
  if (!cli) throw new Error(`Choose --claude, --codex or --kiro.\n${help}`);
  const base = project || (cli === 'kiro' ? process.cwd() : os.homedir());
  const dest = path.join(base, `.${cli}`, 'skills/ai-diagrams');
  const targets = cli === 'kiro'
    ? [dest, path.join(base, '.kiro/steering/ai-diagrams.md'), path.join(base, '.kiro/agents/ai-diagrams.json')]
    : [dest];
  if (cli !== 'kiro' && exists(dest)?.isSymbolicLink() && path.resolve(path.dirname(dest), fs.readlinkSync(dest)) === skill) {
    console.log(`Already installed: ${dest}`);
    return;
  }
  const conflicts = targets.filter(exists);
  if (conflicts.length) {
    if (!process.stdin.isTTY || !process.stdout.isTTY) throw new Error(`Existing installation kept: ${conflicts.join(', ')}. Run in an interactive terminal to confirm the replacement.`);
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    let answer;
    try { answer = await rl.question(`Replace ${conflicts.join(', ')}? [y/N] `); }
    finally { rl.close(); }
    if (!/^(y|yes|s|sim)$/i.test(answer.trim())) throw new Error('Installation cancelled; files kept.');
  }
  const changed = [];
  try {
    for (const target of targets) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      let backup;
      if (exists(target)) {
        backup = fs.mkdtempSync(path.join(path.dirname(target), '.ai-diagrams-backup-'));
        fs.renameSync(target, path.join(backup, 'original'));
      }
      changed.push({ target, backup });
    }
    if (cli === 'kiro') {
      const result = spawnSync('bash', [path.join(root, 'tools/install-kiro.sh'), base], { stdio: 'inherit' });
      if (result.error) throw result.error;
      if (result.status !== 0) throw new Error(`Kiro installer failed (${result.status ?? result.signal}).`);
    } else {
      // shortcut: npx links to its cache; rerun install after clearing the npm cache.
      fs.symlinkSync(skill, dest, 'dir');
      console.log(`skill: ${dest} -> ${skill}`);
    }
    for (const { backup } of changed) if (backup) console.log(`Backup kept: ${path.join(backup, 'original')}`);
  } catch (error) {
    for (const { target, backup } of changed.reverse()) {
      fs.rmSync(target, { recursive: true, force: true });
      if (backup) fs.renameSync(path.join(backup, 'original'), target);
    }
    throw error;
  } finally {
    for (const { backup } of changed) if (backup && !exists(path.join(backup, 'original'))) fs.rmSync(backup, { recursive: true, force: true });
  }
}

function doctor() {
  const nodeOK = Number(process.versions.node.split('.')[0]) >= 18;
  console.log(`${nodeOK ? 'OK' : 'FAIL'} Node: ${process.versions.node} (minimum 18)`);
  let failed = !nodeOK;
  const checks = [
    ['Python', "import sys; print(sys.version.split()[0]); sys.exit(0 if sys.version_info >= (3, 9) else 1)"],
    ['Chrome', 'from build import find_chrome; print(find_chrome())'],
    ['AWS icons', 'from build import find_iconbase; print(find_iconbase())'],
  ];
  for (const [label, code] of checks) {
    const result = spawnSync('python3', ['-c', `import sys; sys.path.insert(0, sys.argv[1]); ${code}`, path.join(skill, 'scripts')], { encoding: 'utf8', env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
    const ok = result.status === 0;
    console.log(`${ok ? 'OK' : 'FAIL'} ${label}: ${(result.stdout || result.stderr || result.error?.message || result.signal || '').trim()}`);
    failed ||= !ok;
  }
  console.log('doctor does not run Chrome or the gates, and writes no PNG.');
  process.exitCode = failed ? 1 : 0;
}

const [command, ...args] = process.argv.slice(2);
try {
  if (!command || command === '--help' || command === '-h') console.log(help);
  else if (command === 'install') await install(args);
  else if (command === 'doctor' && args.length === 0) doctor();
  else if (command === 'import' || command === 'importar') {
    if (command === 'importar') deprecated('importar', 'import');
    const result = spawnSync('python3', [path.join(skill, 'scripts/import_cli.py'), ...args], { stdio: 'inherit', env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
    if (result.error) throw result.error;
    process.exitCode = result.status ?? 1;
  } else throw new Error(`Invalid command: ${command}\n${help}`);
} catch (error) {
  console.error(`ai-diagrams: ${error.message}`);
  process.exitCode = 1;
}
