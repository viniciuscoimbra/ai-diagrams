// Monta o fonte HTML de um DER no formato dos posters (template e estilo da skill posters-aws).
// A posição de cada tabela, a raia de cada seta e o ponto de chegada são escritos à mão no arquivo de layout
// (der-<schema>.layout.mjs); aqui só se traduz isso em caixas e caminhos ortogonais.
// Notação pé de galinha: na ponta da FK, "zero ou muitos"; na ponta da chave, "um" (FK obrigatória) ou "zero ou um" (FK opcional).
// Uso: node der-montar.mjs caminho/der-<schema>.layout.mjs
// O layout aponta o modelo lógico (campo modelo, relativo ao layout). A saída der-<schema>.html é gravada ao
// lado do layout; o build.py da skill gera o PNG a partir dela.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { carregar, obrigatoria, caixa, yColuna, altura, LARG, CSS_LOCAL, CANDY, TIPO, nome, SEM_SETA, SIGNIFICADO, chaves, tabela, LEVES, caixaLeve, HLEVE, fronteira, textoLeve, DESENHADAS, caixaExterna } from './der-tabelas.mjs';

if (!process.argv[2]) { console.error('uso: node der-montar.mjs caminho/der-<schema>.layout.mjs'); process.exit(1); }
const layoutPath = path.resolve(process.argv[2]);
const aqui = path.dirname(layoutPath);
const L = (await import(pathToFileURL(layoutPath).href)).default;
const M = carregar(path.resolve(aqui, L.modelo || 'modelo.json'));

for (const [c, motivo] of Object.entries(L.semSeta || {})) SEM_SETA.set(c, motivo);
const pos = L.tabelas;
const ext = L.externas || {};
for (const k of [...Object.keys(pos), ...Object.keys(ext)]) DESENHADAS.add(k);
const box = (k) => (ext[k] ? { x: ext[k].x, y: ext[k].y, w: ext[k].w, h: ext[k].h } : { x: pos[k].x, y: pos[k].y, w: pos[k].w || LARG, h: altura(k) });

// Seta: sai da linha da coluna de FK (lado 'L' ou 'R' da caixa de origem), corre por raias verticais (x) e chega
// ao lado da caixa da chave na altura dy (relativa ao topo dela). 'pontos' substitui o roteamento padrão quando preciso.
function caminho(a) {
  const o = box(a.de), d = box(a.para);
  const y0 = o.y + yColuna(a.de, a.coluna);
  const x0 = a.sai === 'L' ? o.x : o.x + o.w;
  const x1 = a.chega === 'L' ? d.x : a.chega === 'R' ? d.x + d.w : null;
  let pts;
  if (a.pontos) pts = a.pontos.map(([x, y]) => [x === 'x0' ? x0 : x, y === 'y0' ? y0 : y]);
  else if (a.chega === 'T' || a.chega === 'B') {
    const yd = a.chega === 'T' ? d.y : d.y + d.h, xd = d.x + a.dx;
    pts = [[x0, y0], [a.raia, y0], [a.raia, a.yRaia], [xd, a.yRaia], [xd, yd]];
    if (a.raia === undefined) pts = [[x0, y0], [xd, y0], [xd, yd]];
  } else {
    // dy 'reto': chega na mesma altura da coluna de origem (seta reta).
    const yd = a.dy === 'reto' ? y0 : d.y + a.dy;
    pts = a.raia === undefined ? [[x0, y0], [x1, y0]] : [[x0, y0], [a.raia, y0], [a.raia, yd], [x1, yd]];
  }
  const dedup = pts.filter((p, i) => i === 0 || p[0] !== pts[i - 1][0] || p[1] !== pts[i - 1][1]);
  let dstr = `M${dedup[0][0]},${dedup[0][1]}`;
  for (let i = 1; i < dedup.length; i++) dstr += dedup[i][0] !== dedup[i - 1][0] ? ` H${dedup[i][0]}` : ` V${dedup[i][1]}`;
  return { d: dstr, pts: dedup };
}

function badgeEm(pts, seg, frac = 0.5) {
  const i = seg ?? pts.reduce((m, p, j) => (j > 0 && Math.hypot(p[0] - pts[j - 1][0], p[1] - pts[j - 1][1]) > Math.hypot(pts[m][0] - pts[m - 1][0], pts[m][1] - pts[m - 1][1]) ? j : m), 1);
  const a = pts[i - 1], b = pts[i];
  return [Math.round(a[0] + (b[0] - a[0]) * frac), Math.round(a[1] + (b[1] - a[1]) * frac)];
}

// Cobertura: toda tabela do schema aparece uma vez. As do desenho principal estão no layout; o resto vai para a
// faixa de domínio e configuração, e só pode ser domínio ou configuração.
const todas = chaves(L.schema), faixa = todas.filter((k) => !pos[k]);
const foraDoDesenho = faixa.filter((k) => !LEVES(k));
if (foraDoDesenho.length) throw new Error(`tabelas fora do DER de ${L.schema}: ${foraDoDesenho.join(', ')}`);
const tipoDe = (k) => tabela(k).tipo;
const tiposPresentes = Object.keys(CANDY).filter((t) => todas.some((k) => tipoDe(k) === t));

const W = L.canvas.w;
const NC = 4, LF = 397, GF = 24, X0 = 20;
// Altura do desenho principal: a caixa ou a seta mais baixa, mais uma margem. A legenda fica fora do desenho.
const caminhos = L.arestas.map((a) => caminho(a));
const hDesenho = Math.ceil(Math.max(...[...Object.keys(pos), ...Object.keys(ext)].map((k) => box(k).y + box(k).h),
  ...caminhos.flatMap((c) => c.pts.map((p) => p[1]))) + 30);
const yFaixa = hDesenho + 10, linhasFaixa = Math.ceil(faixa.length / NC);
// Altura da caixa compacta: cabe a linha mais longa da faixa (uma linha por uso).
const hLeve = 34 + 14 * Math.max(1, ...faixa.map((k) => textoLeve(k).length));
const hFaixa = faixa.length ? 40 + linhasFaixa * (hLeve + 14) : 0;
const faixaHtml = faixa.length ? `<div class="frame zone" style="left:10px;top:${yFaixa}px;width:${W - 20}px;height:${hFaixa}px"><div class="flabel">Domínio e configuração · ${faixa.length} tabelas · a coluna em verde guarda o id de uma destas, sem seta</div></div>\n  ` +
  faixa.map((k, i) => caixaLeve(k, X0 + (i % NC) * (LF + GF), yFaixa + 32 + Math.floor(i / NC) * (hLeve + 14), LF, hLeve)).join('\n  ') : '';
const fr = fronteira(L.schema);
const lista = (xs) => xs.length ? xs.map((x) => `<div><code>${x}</code></div>`).join('') : '<div>nenhuma</div>';
const yFront = yFaixa + hFaixa + 20;
const nLinhas = Math.max(fr.sai.length, fr.chega.length + (fr.cache.length ? fr.cache.length + 2 : 0), Math.ceil(fr.aux.length / 2) + 1);
const hFront = 52 + nLinhas * 16.5;
const frontHtml = `<div class="frame zone" style="left:10px;top:${yFront}px;width:${W - 20}px;height:${hFront}px"><div class="flabel">${L.leitura ? 'Fronteira com outros schemas · referência lógica: o id aponta uma linha de lá, sem FK' : 'Fronteira com outros schemas · FK sem leitura: o banco garante que a linha existe, o serviço não lê a tabela do outro'}</div></div>
  <div class="front" style="left:30px;top:${yFront + 30}px;width:560px"><h4>${L.leitura ? 'cada id da view aponta para' : 'este schema aponta para'}</h4>${lista(fr.sai)}</div>
  <div class="front" style="left:610px;top:${yFront + 30}px;width:560px"><h4>outros schemas apontam para cá</h4>${lista(fr.chega)}${fr.cache.length ? `<h4 style="margin-top:8px">views de leitura</h4>${lista(fr.cache)}` : ''}</div>
  <div class="front" style="left:1190px;top:${yFront + 30}px;width:490px"><h4>usa de ${M.schemaComum || 'comum'} (domínio geral e referência)</h4><div>${fr.aux.map((a) => `<code>${a}</code>`).join(' · ') || 'nada'}</div></div>`;
const H = yFront + hFront + 10;
const caixas = [...Object.entries(pos).map(([k, p]) => caixa(k, p.x, p.y, p.desc, p.w)),
  ...Object.entries(ext).map(([k, p]) => caixaExterna(k, p.x, p.y, p.w, p.h, p.desc))].join('\n  ');
const setas = [], badges = [], passos = [];
L.arestas.forEach((a, i) => {
  const n = i + 1, c = caminhos[i];
  // Seta de leitura (DER de views): a view lê a tabela; não existe FK, então não há cardinalidade.
  if (L.leitura) setas.push(`<path d="${c.d}" fill="none" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#le)" style="stroke:var(--apoio)"/>`);
  else {
    const opc = !obrigatoria(a.de, a.coluna);
    setas.push(`<path d="${c.d}" fill="none" stroke-width="1.6" marker-start="url(#muitos)" marker-end="url(#${opc ? 'zeroum' : 'um'})" style="stroke:var(--apoio)"/>`);
  }
  const [bx, by] = a.badge || badgeEm(c.pts, a.seg, a.frac);
  badges.push(`<div class="badge" style="left:${bx - 10}px;top:${by - 10}px">${n}</div>`);
  passos.push(`<div class="pitem"><div class="pb">${n}</div><div>${a.texto}</div></div>`);
});
for (const e of L.extras || []) setas.push(e);

// Legenda fixa: o mesmo bloco, no mesmo lugar (entre o subtítulo e o desenho), em todo DER.
const amostra = (fim, tracejada) => `<svg width="74" height="16" viewBox="0 0 74 16" style="flex:none"><path ${tracejada ? '' : 'marker-start="url(#lmuitos)" '}marker-end="url(#${fim})" d="M3,8 H70" fill="none" stroke-width="1.6"${tracejada ? ' stroke-dasharray="6 4"' : ''} style="stroke:var(--apoio)"/></svg>`;
const legendaFixa = `<div class="legfixa">
  <svg width="0" height="0" style="position:absolute"><defs><marker id="lum" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M5,0 V12 M9,0 V12" stroke-width="1.6" style="stroke:var(--apoio)"/></marker><marker id="lzeroum" markerWidth="18" markerHeight="12" refX="17" refY="6" orient="auto" markerUnits="userSpaceOnUse"><circle cx="5" cy="6" r="3.6" stroke-width="1.4" style="fill:var(--papel);stroke:var(--apoio)"/><path d="M14,0 V12" stroke-width="1.6" style="stroke:var(--apoio)"/></marker><marker id="lmuitos" markerWidth="22" markerHeight="14" refX="21" refY="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><circle cx="5" cy="7" r="3.6" stroke-width="1.4" style="fill:var(--papel);stroke:var(--apoio)"/><path d="M11,7 L21,0 M11,7 L21,7 M11,7 L21,14" stroke-width="1.5" fill="none" style="stroke:var(--apoio)"/></marker><marker id="lle" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 z" style="fill:var(--apoio)"/></marker></defs></svg>
  <div class="lc"><h4>Linhas</h4>
    <div class="li">${amostra('lum')}<span><b>FK obrigatória</b>: aponta exatamente uma linha</span></div>
    <div class="li">${amostra('lzeroum')}<span><b>FK opcional</b>: aponta zero ou uma linha</span></div>
    <div class="li"><span class="pe">pé de galinha</span><span>o lado N: zero ou muitas linhas por chave</span></div>
    <div class="li">${amostra('lle', true)}<span><b>só em view</b>: o id aponta a tabela, sem FK</span></div></div>
  <div class="lc"><h4>Rótulo à direita da coluna</h4>
    <div class="li"><span class="rv">situacoes_conta</span><span>id de tabela de domínio ou de referência, sem seta</span></div>
    <div class="li"><span class="rv">↓ na faixa</span><span>o nome não coube: a tabela está na faixa de domínio</span></div>
    <div class="li"><span class="ra">cadastro.clientes</span><span>FK para tabela de outro schema, sem seta</span></div>
    <div class="li"><span class="rr">motivo</span><span>FK desenhada sem seta: cópia deliberada, motivo no rótulo</span></div>
    <div class="li"><span class="rk">PK FK UQ</span><span>chave primária, estrangeira, única; <b>id</b>: id numa view de leitura</span></div>
    <div class="li"><span class="rk">- - -</span><span>contorno tracejado: tabela de outro schema</span></div></div>
  <div class="lc dupla"><h4>Cor do cabeçalho: o tipo da tabela</h4><div class="tps">${Object.keys(SIGNIFICADO)
    .map((t) => `<div class="tipo"><span class="sw" style="background:${CANDY[t]}"></span><span><b>${TIPO[t]}</b>: ${SIGNIFICADO[t]}</span></div>`).join('')}</div></div>
</div>`;

const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="largura" content="${W + 96}">
<title>DER · ${L.schema}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/*ESTILO*/
${CSS_LOCAL}
/* a página acompanha o canvas do layout: legenda, faixas e desenho com a mesma largura */
body{width:${W + 96}px}
.wrap.stack .canvas{width:${W}px}
</style>
</head>
<body>
<div class="page">
<div class="hdr"><span>${M.cabecalho || ''}</span><span>DER · ${L.schema} · V1</span></div>
<div class="kicker"><span class="sq">■</span>&nbsp; Modelo lógico · schema ${L.schema}</div>
<h1>${L.titulo}</h1>
<div class="sub">${L.sub}</div>
${legendaFixa}

<div class="wrap stack">
<div class="canvas" style="height:${H}px">
  ${caixas}
  ${faixaHtml}
  ${frontHtml}
  <svg class="edges" viewBox="0 0 ${W} ${H}">
    <defs>
      <marker id="le" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 z" style="fill:var(--apoio)"/></marker>
      <marker id="um" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M5,0 V12 M9,0 V12" stroke-width="1.6" style="stroke:var(--apoio)"/></marker>
      <marker id="zeroum" markerWidth="18" markerHeight="12" refX="17" refY="6" orient="auto" markerUnits="userSpaceOnUse"><circle cx="5" cy="6" r="3.6" stroke-width="1.4" style="fill:var(--papel);stroke:var(--apoio)"/><path d="M14,0 V12" stroke-width="1.6" style="stroke:var(--apoio)"/></marker>
      <marker id="muitos" markerWidth="22" markerHeight="14" refX="21" refY="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><circle cx="5" cy="7" r="3.6" stroke-width="1.4" style="fill:var(--papel);stroke:var(--apoio)"/><path d="M11,7 L21,0 M11,7 L21,7 M11,7 L21,14" stroke-width="1.5" fill="none" style="stroke:var(--apoio)"/></marker>
    </defs>
    ${setas.join('\n    ')}
  </svg>
  ${badges.join('\n  ')}
</div>

<div class="passos">
  <div class="ptitle">Relações</div>
  ${passos.join('\n  ')}
</div>
</div>

<div class="foot">${M.rodape || ''}</div>
</div>
</body>
</html>
`;
const saida = path.join(aqui, `der-${L.schema}.html`);
fs.writeFileSync(saida, html);
console.log(saida);
