// Visão geral dos schemas: matriz de dependência gerada do modelo lógico (modelo.json).
// Linha: o schema que tem a coluna. Coluna: o schema da tabela apontada. Célula: quantas colunas apontam.
// Matriz em vez de grafo: com muitos pares de schemas, setas para todos eles se cruzariam.
// Uso: node der-visao-geral.mjs caminho/modelo.json [saida.html] [--tema NOME|caminho.json] [--idioma pt-BR|en|es]
// Sem saída explícita, grava der-visao-geral.html ao lado do modelo; o build.py da skill gera o PNG.
import fs from 'node:fs';
import path from 'node:path';
import { tirarIdioma } from './idioma.mjs';
import { texto, IDIOMA, tirarTema, temaDoGerador, carregar, chaves, tabela, nome } from './der-tabelas.mjs';

const IDIOMA_ARGS = tirarIdioma(process.argv.slice(2));
const ARGS = tirarTema(IDIOMA_ARGS.resto);
if (!ARGS.resto[0]) { console.error('uso: node der-visao-geral.mjs caminho/modelo.json [saida.html] [--tema NOME|caminho.json] [--idioma pt-BR|en|es]'); process.exit(1); }
const modeloPath = path.resolve(ARGS.resto[0]);
const M = carregar(modeloPath, IDIOMA_ARGS.valor);
const saida = ARGS.resto[1] ? path.resolve(ARGS.resto[1]) : path.join(path.dirname(modeloPath), 'der-visao-geral.html');
const TEMA = temaDoGerador(ARGS.valor, saida);
// Ordem de construção (a do modelo): quem é apontado por mais schemas vem antes.
const ORDEM = Object.keys(M.schemas);
const NOME = M.schemas;

const par = {};
for (const s of ORDEM) for (const k of chaves(s)) for (const [n, , chave, alvo] of tabela(k).colunas) {
  if (chave !== 'FK') continue;
  const d = alvo.split('.')[0];
  if (d === s) continue;
  (par[`${s}>${d}`] ||= []).push(`${nome(k)}.${n} → ${nome(alvo)}`);
}
const n = (o, d) => (par[`${o}>${d}`] || []).length;
const max = Math.max(...Object.values(par).map((v) => v.length));
const tom = (v) => (v ? `rgba(var(--der-calor-rgb), ${0.18 + 0.62 * (v / max)})` : 'transparent');

const cab = ORDEM.map((d) => `<th class="cv"><span>${d}</span></th>`).join('');
const linhas = ORDEM.map((o) => {
  const cel = ORDEM.map((d) => o === d
    ? `<td class="diag">${chaves(o).length}</td>`
    : `<td style="background:${tom(n(o, d))}">${n(o, d) || ''}</td>`).join('');
  const sai = ORDEM.filter((d) => d !== o && n(o, d)).length;
  return `<tr><th class="rh"><b>${o}</b><span>${NOME[o]}</span></th>${cel}<td class="tot">${sai}</td></tr>`;
}).join('\n');
const usados = (d) => ORDEM.filter((o) => o !== d && n(o, d)).length;
const aponta = (o) => ORDEM.filter((d) => d !== o && n(o, d)).length;
const maisUsado = ORDEM.reduce((a, b) => (usados(b) > usados(a) ? b : a));
const maisDepende = ORDEM.reduce((a, b) => (aponta(b) > aponta(a) ? b : a));
const usadoPor = ORDEM.map((d) => `<td class="tot">${ORDEM.filter((o) => o !== d && n(o, d)).length}</td>`).join('');

const detalhe = ORDEM.flatMap((o) => ORDEM.filter((d) => d !== o && n(o, d)).map((d) =>
  `<div class="par"><div class="pt">${o} → ${d} <span>${n(o, d)}</span></div>${par[`${o}>${d}`].map((x) => `<div class="pc">${x}</div>`).join('')}</div>`)).join('\n');

const html = `<!DOCTYPE html>
<html lang="${IDIOMA.codigo}">
<head>
<meta charset="utf-8">
<title>${texto('matriz.titulo')}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
${TEMA.link}${IDIOMA.meta ? '\n' + IDIOMA.meta : ''}${TEMA.meta ? '\n' + TEMA.meta : ''}
<style>
/*ESTILO*/
.mx{border-collapse:collapse;margin-top:34px;font-family:var(--fonte-mono)}
.mx td,.mx th{border:1px solid var(--der-borda);width:74px;height:46px;text-align:center;font-size:15px;font-weight:600;color:var(--tinta)}
.mx th.cv{height:120px;vertical-align:bottom;padding-bottom:8px;border-top:none}
.mx th.cv span{display:inline-block;writing-mode:vertical-rl;transform:rotate(180deg);font-size:12px;font-weight:700}
.mx th.rh{width:260px;text-align:left;padding:0 12px;font-weight:400}
.mx th.rh b{font-size:13px;display:block}
.mx th.rh span{font-family:var(--fonte-texto);font-size:11px;color:var(--cinza)}
.mx td.diag{background:var(--apoio);color:var(--papel);font-size:12px}
.mx td.tot{background:var(--zona);font-size:13px;color:var(--apoio)}
.mx th.canto{border:none}
.leitura{display:flex;gap:40px;margin-top:26px;font-size:12.5px;line-height:1.55;color:var(--tinta)}
.leitura div{flex:1}
.det{columns:3;column-gap:32px;margin-top:20px}
.par{break-inside:avoid;margin-bottom:12px}
.pt{font-family:var(--fonte-mono);font-size:11.5px;font-weight:700;border-bottom:1px solid var(--apoio);padding-bottom:2px;margin-bottom:3px}
.pt span{float:right;color:var(--cinza)}
.pc{font-family:var(--fonte-mono);font-size:10px;color:var(--apoio);line-height:1.5}
.sec{font-family:var(--fonte-mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;font-weight:600;margin-top:34px;border-bottom:1.5px solid var(--tinta);padding-bottom:6px}
</style>
</head>
<body>
<div class="page">
<div class="hdr"><span>${M.cabecalho || ''}</span><span>${texto('matriz.cabecalho')}</span></div>
<div class="kicker"><span class="sq">■</span>&nbsp; ${texto('matriz.kicker', { n: ORDEM.length })}</div>
<h1>${texto('matriz.h1')}</h1>
<div class="sub">${texto('matriz.sub')}</div>

<table class="mx">
<tr><th class="canto"></th>${cab}<th class="cv"><span>${texto('matriz.aponta')}</span></th></tr>
${linhas}
<tr><th class="rh"><b>${texto('matriz.usado_por')}</b><span>${texto('matriz.quantos')}</span></th>${usadoPor}<td class="tot"></td></tr>
</table>

<div class="leitura">
<div>${texto('matriz.diagonal', { n: ORDEM.reduce((n, o) => n + chaves(o).length, 0) })}</div>
<div>${texto('matriz.cor', { n: max })}</div>
<div>${texto('matriz.dependencias', { usado: maisUsado, nUsado: usados(maisUsado), depende: maisDepende, nDepende: aponta(maisDepende) })}</div>
</div>

<div class="sec">${texto('matriz.colunas')}</div>
<div class="det">
${detalhe}
</div>

<div class="foot">${M.rodape || ''}</div>
</div>
</body>
</html>
`;
fs.writeFileSync(saida, html);
console.log(saida);
console.log(`${Object.keys(par).length} pares, máximo ${max}`);
