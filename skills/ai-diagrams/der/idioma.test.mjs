import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { carregarIdioma, tirarIdioma, validarCatalogo } from './idioma.mjs';

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-diagrams-der-test-'));
const ambiente = { ...process.env };
delete process.env.AI_DIAGRAMS_IDIOMA;
delete process.env.AI_DIAGRAMS_TEMA;
const rodar = (script, args) => execFileSync(process.execPath, [new URL(script, import.meta.url).pathname, ...args], { encoding: 'utf8' });
const hash = (texto) => createHash('sha256').update(texto).digest('hex');
try {
  assert.equal(carregarIdioma().codigo, 'pt-BR');
  assert.equal(carregarIdioma().meta, '');
  process.env.AI_DIAGRAMS_IDIOMA = 'es';
  assert.equal(carregarIdioma().codigo, 'es');
  assert.equal(carregarIdioma(undefined, { idioma: 'en' }).codigo, 'en');
  assert.equal(carregarIdioma('pt-BR', { idioma: 'en' }).codigo, 'pt-BR');
  assert.match(carregarIdioma('pt-BR').meta, /content="pt-BR"/);
  assert.deepEqual(tirarIdioma(['modelo.json', '--idioma=en', '--tema', 'papel']), { valor: 'en', resto: ['modelo.json', '--tema', 'papel'] });
  assert.deepEqual(tirarIdioma(['--idioma', 'es', 'modelo.json']), { valor: 'es', resto: ['modelo.json'] });
  assert.throws(() => tirarIdioma(['--idioma']), /IDIOMA-INEXISTENTE/);
  assert.throws(() => carregarIdioma('fr'), /IDIOMA-INEXISTENTE/);
  assert.throws(() => validarCatalogo({}, { 'der.linhas': 'Linhas' }), /IDIOMA-INCOMPLETO: falta der.linhas/);
  assert.equal(carregarIdioma('en').t('der.faixa', { n: 5 }), 'Domain and configuration · 5 tables · green columns store an id from one of these, without an arrow');
  delete process.env.AI_DIAGRAMS_IDIOMA;

  for (const [tipo, pasta, script, entrada, saida, baseline, en, es] of [
    ['schema', 'der-schema', 'der-montar.mjs', 'der-cobranca.layout.mjs', 'der-cobranca.html', '8b9f60ef2943b102fa576cd944d8f49ed95e495a9447fbc37879d83323ef1ede', 'Relationships', 'Relaciones'],
    ['matriz', 'matriz-dependencia', 'der-visao-geral.mjs', 'modelo.json', 'der-visao-geral.html', '09fa408d18260f110ccd6ee9af54afe626bec4b76d8b7c8fdcff0ccd6693cd1a', 'Dependencies between schemas', 'Dependencias entre los schemas'],
  ]) {
    const dir = path.join(tmp, tipo);
    fs.cpSync(path.join(repo, 'exemplos', pasta, 'resultado', '_src'), dir, { recursive: true });
    const fonte = path.join(dir, entrada), destino = path.join(dir, saida);
    rodar(script, [fonte]);
    const pt = fs.readFileSync(destino, 'utf8');
    assert.equal(hash(pt), baseline, `${tipo}: saída padrão deve manter bytes anteriores ao i18n`);
    const geometria = (html) => [...html.matchAll(/(?:style|d|viewBox)="[^"]*"/g)].map((m) => m[0]);
    for (const [idioma, rotulo] of [['en', en], ['es', es]]) {
      rodar(script, [fonte, '--idioma', idioma]);
      const html = fs.readFileSync(destino, 'utf8');
      assert.ok(html.includes(rotulo), `${tipo}: rótulo ${idioma}`);
      assert.ok(html.includes(`<meta name="idioma" content="${idioma}">`));
      assert.deepEqual(geometria(html), geometria(pt), `${tipo}: tradução preserva geometria`);
    }
    const modelo = path.join(dir, 'modelo.json');
    const dados = JSON.parse(fs.readFileSync(modelo, 'utf8'));
    dados.idioma = 'es';
    fs.writeFileSync(modelo, JSON.stringify(dados));
    process.env.AI_DIAGRAMS_IDIOMA = 'en';
    rodar(script, [fonte]);
    assert.ok(fs.readFileSync(destino, 'utf8').includes(es), `${tipo}: fonte prevalece sobre ambiente`);
    rodar(script, [fonte, '--idioma', 'en']);
    assert.ok(fs.readFileSync(destino, 'utf8').includes(en), `${tipo}: flag prevalece sobre fonte`);
    delete process.env.AI_DIAGRAMS_IDIOMA;
  }
  console.log('DER i18n: prioridade, erros, rótulos, geometria e compatibilidade byte a byte aprovados');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
  for (const chave of ['AI_DIAGRAMS_IDIOMA', 'AI_DIAGRAMS_TEMA']) {
    if (ambiente[chave] === undefined) delete process.env[chave];
    else process.env[chave] = ambiente[chave];
  }
}
