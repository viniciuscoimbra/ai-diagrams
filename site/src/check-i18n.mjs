import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
import { content } from './content.mjs';
import { translator, localizeContent, languageHref, languages, importGateMessage } from './i18n.mjs';
import { contrastPairs } from './editor.mjs';

const catalogs = { 'pt-BR': {}, es: {} };
for (const file of ['ui.tsv', 'content.tsv']) {
  for (const [index, line] of fs.readFileSync(new URL(`locales/${file}`, import.meta.url), 'utf8').trim().split('\n').entries()) {
    const fields = line.split('\t');
    assert.equal(fields.length, 3, `${file}:${index + 1}: three fields`);
    const [key, pt, es] = fields;
    assert.ok(key && pt && es, `${file}:${index + 1}: empty translation`);
    assert.ok(!key.includes('\u2014') && !pt.includes('\u2014') && !es.includes('\u2014'), `${file}:${index + 1}: em dash`);
    for (const [language, value] of [['pt-BR', pt], ['es', es]]) {
      assert.ok(!Object.hasOwn(catalogs[language], key), `duplicate key: ${key}`);
      catalogs[language][key] = value;
    }
  }
}
const missing = new Set();
const translated = value => {
  for (const catalog of Object.values(catalogs)) if (!Object.hasOwn(catalog, value)) missing.add(value);
};
const app = fs.readFileSync(new URL('app.jsx', import.meta.url), 'utf8');
const ast = ts.createSourceFile('app.jsx', app, ts.ScriptTarget.Latest, true, ts.ScriptKind.JSX);
const rawText = new Set(['GitHub ↗', 'en', 'es', 'pt-BR', 'ai-diagrams', 'paper', 'Aa', 'px', 'INSTALL.md', 'Inter / 400 · 500 · 600 · 700', 'JetBrains Mono / 400 · 600', '−', '+', '%', ':', '·']);
const literalAttributes = new Set(['ai-diagrams', 'prompt.md', 'antifraud-decision.md']);
let calls = 0;
function walk(node) {
  if (ts.isCallExpression(node) && node.expression.getText(ast) === 't' && ts.isStringLiteral(node.arguments[0])) {
    translated(node.arguments[0].text); calls++;
  }
  if (ts.isJsxText(node) && /[\p{L}]/u.test(node.text)) assert.ok(rawText.has(node.text.trim()), `JSX text without translation: ${node.text.trim()}`);
  if (ts.isJsxAttribute(node) && ['alt', 'title', 'label', 'sub', 'placeholder', 'aria-label'].includes(node.name.text) && node.initializer && ts.isStringLiteral(node.initializer)) {
    assert.ok(literalAttributes.has(node.initializer.text), `JSX attribute without translation: ${node.initializer.text}`);
  }
  if (ts.isVariableDeclaration(node) && ['TOKEN_LABELS', 'GROUP_LABELS', 'ROLE_LABELS', 'STATE_LABEL', 'RESULT_LABEL'].includes(node.name.getText(ast))) {
    for (const property of node.initializer.properties) translated(property.initializer.text);
  }
  ts.forEachChild(node, walk);
}
walk(ast);
for (const gate of ['pending', 'passed']) translated(importGateMessage(gate));
const buildSource = fs.readFileSync(new URL('build.mjs', import.meta.url), 'utf8');
const importFormats = buildSource.match(/const importFormats = \[([^]*?)\n\];/)[1];
for (const match of importFormats.matchAll(/\['[^']+', '([^']+)', '[^']+'\]/g)) translated(match[1]);
const theme = JSON.parse(fs.readFileSync(new URL('../../skills/ai-diagrams/themes/ai-diagrams.json', import.meta.url), 'utf8'));
// texts the compatibility page reads from the measurement files
const runs = JSON.parse(fs.readFileSync(new URL('../../docs/models/runs.json', import.meta.url), 'utf8'));
for (const text of [...Object.values(runs.results), ...Object.values(runs.sources).map(s => s.text), ...runs.runs.map(r => r.note).filter(Boolean)]) translated(text);
const installChecks = new URL('../../docs/models/install-checks.json', import.meta.url);
if (fs.existsSync(installChecks)) for (const check of JSON.parse(fs.readFileSync(installChecks, 'utf8')).checks) translated(check.label);
for (const { label } of contrastPairs(theme)) translated(label);

const metadata = new Set(['id', 'family', 'sourcePath']);
const authorSources = new Set(['prompt', 'exampleData']);
function checkContent(original, localized, translate, key = '') {
  if (typeof original === 'string') {
    if (metadata.has(key)) assert.equal(localized, original, `identifier changed: ${original}`);
    else if (key === 'command') {
      const before = original.split('\n'), after = localized.split('\n');
      assert.equal(after.length, before.length, 'command lines');
      before.forEach((line, i) => {
        if (line.startsWith('#')) { translated(line); assert.equal(after[i], translate(line)); }
        else assert.equal(after[i], line, `command changed: ${line}`);
      });
    } else if (!authorSources.has(key)) {
      translated(original);
      assert.equal(localized, translate(original));
      assert.deepEqual(localized.match(/\d+(?:\.\d+)*|[¹²³⁴⁵⁶⁷]/g), original.match(/\d+(?:\.\d+)*|[¹²³⁴⁵⁶⁷]/g), `measurement changed: ${original}`);
      for (const code of original.match(/`[^`]+`|<AI_DIAGRAMS>|<PROJECT>|No such file or directory|Already up to date\.|Cloning into|templates: 11 of 11/g) || []) assert.ok(localized.includes(code), `code or output changed: ${code}`);
    }
  } else if (Array.isArray(original)) original.forEach((item, index) => checkContent(item, localized[index], translate, key));
  else if (original && typeof original === 'object') for (const [name, item] of Object.entries(original)) checkContent(item, localized[name], translate, name);
  else assert.equal(localized, original);
}
for (const language of ['pt-BR', 'es']) {
  const translate = translator(language, catalogs[language]);
  checkContent(content, localizeContent(content, translate), translate);
}
for (const from of languages) for (const to of languages) {
  const base = `https://example.test/out/${from === 'en' ? '' : from + '/'}01-home.html`;
  const destination = new URL(languageHref(from, to, '02-diagrams.html'), base);
  assert.equal(destination.pathname, `/out/${to === 'en' ? '' : to + '/'}02-diagrams.html`);
}
if (missing.size) { console.error(`${missing.size} strings without pt-BR or es:`); for (const value of missing) console.error(JSON.stringify(value)); process.exit(1); }
console.log(`i18n: ${calls} literal calls, JSX, attributes, labels, content, measurements, metadata, commands and 9 language routes passed`);
