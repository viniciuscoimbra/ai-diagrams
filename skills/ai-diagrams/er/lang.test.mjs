import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { carregarIdioma, tirarIdioma, validarCatalogo } from './lang.mjs';

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-diagrams-der-test-'));
const ambiente = { ...process.env };
const VARIAVEIS = ['AI_DIAGRAMS_LANG', 'AI_DIAGRAMS_IDIOMA', 'AI_DIAGRAMS_THEME', 'AI_DIAGRAMS_TEMA'];
for (const chave of VARIAVEIS) delete process.env[chave];
const rodar = (script, args) => execFileSync(process.execPath, [new URL(script, import.meta.url).pathname, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
const hash = (texto) => createHash('sha256').update(texto).digest('hex');
try {
  assert.equal(carregarIdioma().codigo, 'pt-BR');
  assert.equal(carregarIdioma().meta, '');
  process.env.AI_DIAGRAMS_LANG = 'es';
  assert.equal(carregarIdioma().codigo, 'es');
  delete process.env.AI_DIAGRAMS_LANG;
  process.env.AI_DIAGRAMS_IDIOMA = 'es';
  assert.equal(carregarIdioma().codigo, 'es');
  assert.equal(carregarIdioma(undefined, { idioma: 'en' }).codigo, 'en');
  assert.equal(carregarIdioma(undefined, { lang: 'en' }).codigo, 'en');
  assert.equal(carregarIdioma('pt-BR', { idioma: 'en' }).codigo, 'pt-BR');
  assert.match(carregarIdioma('pt-BR').meta, /content="pt-BR"/);
  assert.deepEqual(tirarIdioma(['model.json', '--lang=en', '--theme', 'papel']), { valor: 'en', resto: ['model.json', '--theme', 'papel'] });
  assert.deepEqual(tirarIdioma(['--lang', 'es', 'model.json']), { valor: 'es', resto: ['model.json'] });
  assert.deepEqual(tirarIdioma(['--idioma', 'es', 'model.json']), { valor: 'es', resto: ['model.json'] });
  assert.deepEqual(tirarIdioma(['--idioma=en']), { valor: 'en', resto: [] });
  assert.throws(() => tirarIdioma(['--lang']), /LANG-NOT-FOUND/);
  assert.throws(() => carregarIdioma('fr'), /LANG-NOT-FOUND/);
  assert.throws(() => validarCatalogo({}, { 'der.linhas': 'Linhas' }), /LANG-INCOMPLETE: missing der.linhas/);
  assert.equal(carregarIdioma('en').t('der.faixa', { n: 5 }), 'Domain and configuration · 5 tables · green columns store an id from one of these, without an arrow');
  delete process.env.AI_DIAGRAMS_IDIOMA;

  for (const [tipo, pasta, script, entrada, saida, baseline, en, es] of [
    ['schema', 'er-schema', 'er-build.mjs', 'er-billing.layout.mjs', 'er-billing.html', '9d991153caa89ca3be5fe8712738fead94041288c8ba7346d73db563fba3e3f0', 'Relationships', 'Relaciones'],
    ['matriz', 'dependency-matrix', 'er-overview.mjs', 'model.json', 'er-overview.html', 'b31f760648f411a5854388ec82c8d48dd120923c317ef2b314d9ce1df7af3603', 'Dependencies between schemas', 'Dependencias entre los schemas'],
  ]) {
    const dir = path.join(tmp, tipo);
    fs.cpSync(path.join(repo, 'examples', pasta, 'output', '_src'), dir, { recursive: true });
    const fonte = path.join(dir, entrada), destino = path.join(dir, saida);
    rodar(script, [fonte]);
    const pt = fs.readFileSync(destino, 'utf8');
    assert.equal(hash(pt), baseline, `${tipo}: default output must keep the pre-i18n bytes`);
    const geometria = (html) => [...html.matchAll(/(?:style|d|viewBox)="[^"]*"/g)].map((m) => m[0]);
    for (const [idioma, rotulo] of [['en', en], ['es', es]]) {
      rodar(script, [fonte, '--lang', idioma]);
      const html = fs.readFileSync(destino, 'utf8');
      assert.ok(html.includes(rotulo), `${tipo}: ${idioma} label`);
      assert.ok(html.includes(`<meta name="lang" content="${idioma}">`));
      assert.deepEqual(geometria(html), geometria(pt), `${tipo}: translation keeps the geometry`);
    }
    const modelo = path.join(dir, 'model.json');
    const dados = JSON.parse(fs.readFileSync(modelo, 'utf8'));
    dados.lang = 'es';
    fs.writeFileSync(modelo, JSON.stringify(dados));
    process.env.AI_DIAGRAMS_LANG = 'en';
    rodar(script, [fonte]);
    assert.ok(fs.readFileSync(destino, 'utf8').includes(es), `${tipo}: source wins over environment`);
    rodar(script, [fonte, '--lang', 'en']);
    assert.ok(fs.readFileSync(destino, 'utf8').includes(en), `${tipo}: flag wins over source`);
    const antigo = spawnSync(process.execPath, [new URL(script, import.meta.url).pathname, fonte, '--idioma', 'es'], { encoding: 'utf8' });
    assert.equal(antigo.status, 0, antigo.stderr);
    assert.match(antigo.stderr, /ai-diagrams: --idioma is deprecated; use --lang/);
    assert.ok(fs.readFileSync(destino, 'utf8').includes(es), `${tipo}: --idioma still works`);
    delete process.env.AI_DIAGRAMS_LANG;
  }
  console.log('ER i18n: precedence, errors, labels, geometry and byte-for-byte compatibility passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
  for (const chave of VARIAVEIS) {
    if (ambiente[chave] === undefined) delete process.env[chave];
    else process.env[chave] = ambiente[chave];
  }
}
