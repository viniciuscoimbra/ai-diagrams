// Conteúdo das caixas de tabela dos DERs, lido do modelo lógico (modelo.json, formato em references/der.md).
// O layout (posição de cada caixa e o caminho de cada seta) é decidido à mão no arquivo der-<schema>.layout.mjs;
// este módulo só calcula o que vai dentro da caixa e a altura dela, e gera o HTML da caixa.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { carregarIdioma } from './idioma.mjs';

// Tema: tira --tema X (ou --tema=X) do argv e pede ao scripts/tema.py, o único leitor do json do tema,
// o link das fontes e a meta que o fonte HTML grava. Tema inexistente ou incompleto encerra aqui.
export function tirarTema(argv) {
  const resto = []; let valor = null;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--tema') { valor = argv[++i]; continue; }
    if (argv[i].startsWith('--tema=')) { valor = argv[i].slice(7); continue; }
    resto.push(argv[i]);
  }
  return { valor, resto };
}
export function temaDoGerador(valor, saida) {
  const script = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'tema.py');
  const args = [script, ...(valor ? ['--tema', valor] : []), '--gerador', saida];
  try {
    return JSON.parse(execFileSync('python3', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));
  } catch (e) {
    console.error(((e.stderr || '') + '').trim() || e.message);
    process.exit(1);
  }
}

// Modelo carregado: { tabelas: { 'schema.tabela': { tipo, rotulo, colunas: [[nome, tipo, chave, alvo, obrigatoria]] } } }
export let MODELO = null;
let completas = {};
export let IDIOMA;
export const texto = (chave, valores) => IDIOMA.t(`der.${chave}`, valores);
export function carregar(caminho, idioma, fonte = {}) {
  MODELO = JSON.parse(fs.readFileSync(caminho, 'utf8'));
  IDIOMA = carregarIdioma(idioma, { ...MODELO, ...fonte });
  for (const tipo of Object.keys(CANDY)) {
    TIPO[tipo] = texto(`tipo.${tipo}`);
    SIGNIFICADO[tipo] = texto(`significado.${tipo}`);
  }
  completas = MODELO.tabelas;
  for (const c of MODELO.colunasControle || []) CONTROLE.add(c);
  return MODELO;
}

// Colunas de controle não aparecem na caixa.
export const CONTROLE = new Set(['criado_em', 'atualizado_em', 'versao_registro', 'deletado_em']);
const LEVE = new Set(['dominio', 'referencia', 'configuracao']);
export const HEAD = 52, ROW = 17, LARG = 330;

// Paleta candy: um tom pastel por tipo de tabela, texto escuro.
export const CANDY = {
  forte: 'var(--der-forte)', dependente: 'var(--der-dependente)', associativa: 'var(--der-associativa)', controle: 'var(--der-controle)', fato: 'var(--der-fato)',
  versionada: 'var(--der-versionada)', projecao: 'var(--der-projecao)', trilha: 'var(--der-trilha)', dominio: 'var(--der-dominio-fundo)', configuracao: 'var(--der-configuracao)', referencia: 'var(--der-referencia)', visao: 'var(--der-visao)'
};
export const TIPO = {}, SIGNIFICADO = {};

const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export const nome = (k) => k.split('.')[1];
export const tabela = (k) => {
  if (!completas[k]) throw new Error(`tabela ${k} não existe no modelo`);
  return completas[k];
};
export const chaves = (s) => Object.keys(completas).filter((k) => k.startsWith(`${s}.`));
// FK obrigatória: quinto campo da coluna no modelo (true quando a coluna é not null).
export function obrigatoria(k, coluna) {
  const c = tabela(k).colunas.find(([n]) => n === coluna);
  if (!c) throw new Error(`${k} não tem a coluna ${coluna}`);
  return c[4] === true;
}

// Coluna de FK desenhada sem seta (cópia deliberada; o layout escreve o motivo).
export const SEM_SETA = new Map();
// Tabelas desenhadas no DER corrente: FK para uma delas vira seta, mesmo que o alvo seja referência ou domínio.
export const DESENHADAS = new Set();

// Coluna (mono 10px) e rótulo (mono 9px) cabem lado a lado na largura da caixa?
const cabe = (n, info, largura) => n.length * 6.2 + info.length * 5.6 + 80 <= largura;
export function linhas(k, largura = LARG) {
  const t = tabela(k), s = k.split('.')[0];
  return t.colunas.filter(([n]) => !CONTROLE.has(n)).map(([n, tipo, chave, alvo]) => {
    if (chave === 'PK') return { n, marca: 'PK', info: '' };
    if (chave === 'FK') {
      const leve = LEVES(alvo) && !DESENHADAS.has(alvo);
      // Quando a tabela de domínio é do mesmo schema, basta o nome dela; de outro schema, com o prefixo.
      if (leve) {
        // Nome da coluna e da tabela de domínio não cabem juntos: a coluna fica inteira e o rótulo manda para a faixa.
        const info = `${alvo.split('.')[0] === s ? '' : alvo.split('.')[0] + '.'}${nome(alvo)}`;
        const alt = alvo.split('.')[0] === s ? texto('faixa_curta') : alvo.split('.')[0];
        return { n, marca: '', info: cabe(n, info, largura) ? info : cabe(n, alt, largura) ? alt : '', cls: 'dom' };
      }
      if (alvo.split('.')[0] !== s && !DESENHADAS.has(alvo)) return { n, marca: 'FK', info: `${alvo.split('.')[0]}.${nome(alvo)}`, cls: 'fora' };
      if (SEM_SETA.has(`${k}.${n}`)) return { n, marca: 'FK', info: SEM_SETA.get(`${k}.${n}`), cls: 'cop' };
      return { n, marca: t.tipo === 'visao' ? 'id' : 'FK', info: '', alvo };
    }
    return { n, marca: chave === 'UQ' ? 'UQ' : '', info: tipo.replace('timestamptz', texto('data_hora')).replace('numeric(18,2)', texto('valor')) };
  });
}

export function altura(k) { return HEAD + linhas(k).length * ROW + 8; }

// y (relativo ao topo da caixa) do centro da linha da coluna.
export function yColuna(k, coluna) {
  const i = linhas(k).findIndex((l) => l.n === coluna);
  if (i < 0) throw new Error(`${k} não tem a coluna ${coluna}`);
  return HEAD + i * ROW + ROW / 2 + 4;
}

export function caixa(k, x, y, descricao, largura = LARG) {
  const t = tabela(k), ls = linhas(k, largura), h = altura(k);
  const cor = CANDY[t.tipo] || 'var(--der-trilha)';
  const rows = ls.map((l) => `<div class="tr"><span class="tk">${esc(l.marca)}</span><span class="tn">${esc(l.n)}</span><span class="ti ${l.cls || ''}">${esc(l.info)}</span></div>`).join('');
  return `<div class="bchip tabela" style="left:${x}px;top:${y}px;width:${largura}px;height:${h}px">` +
    `<div class="th" style="background:${cor}"><div class="tt">${esc(nome(k))}<span class="tp">${esc(TIPO[t.tipo] || t.tipo)}</span></div>` +
    `<div class="td">${esc(descricao || t.rotulo)}</div></div>${rows}</div>`;
}

export const CSS_LOCAL = `
.bchip.tabela{padding:0;border:1.4px solid var(--apoio);border-left:1.4px solid var(--apoio);background:var(--papel);overflow:hidden}
.tabela .th{height:${HEAD}px;padding:6px 10px;border-bottom:1px solid var(--apoio)}
.tabela .tt{font-size:13px;font-weight:700;font-family:var(--fonte-mono);color:var(--tinta);display:flex;justify-content:space-between;align-items:baseline}
.tabela .tp{font-family:var(--fonte-texto);font-size:9px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--apoio)}
.tabela .td{font-size:10.5px;color:var(--tinta);line-height:1.25;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tabela .tr{height:${ROW}px;display:flex;align-items:center;padding:0 10px;font-family:var(--fonte-mono);font-size:10.5px}
.tabela .tr:nth-child(odd){background:var(--der-linha-par)}
.tabela .tk{width:24px;flex:none;font-size:9px;font-weight:700;color:var(--der-chave)}
.tabela .tn{flex:1;min-width:0;font-size:10px;color:var(--tinta);white-space:nowrap;overflow:hidden;padding-right:6px}
.tabela .ti{flex:none;max-width:165px;text-align:right;font-size:9px;color:var(--cinza);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tabela .ti.dom{color:var(--der-dominio)}
.tabela .ti.fora{color:var(--der-fora);font-weight:600}
.tabela .ti.cop{color:var(--der-copia)}
.tabela.externa{border-style:dashed}
.tabela.externa .th{border-bottom:none}
.tabela.leve .th{padding:4px 10px}
.tabela.leve .tt{font-size:11.5px}
.tabela .lu{font-size:9.5px;color:var(--der-dominio);padding:2px 10px 0;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.front{position:absolute;font-size:10.5px;color:var(--tinta);line-height:1.55}
.front h4{font-family:var(--fonte-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--apoio);margin:0 0 4px}
.front code{font-family:var(--fonte-mono);font-size:10px}
.front .fora{color:var(--der-fora);font-weight:600}
.sub{min-height:66px}
.legfixa{display:flex;gap:28px;margin-top:22px;padding:14px 18px;border:1px solid var(--der-borda);background:var(--der-legenda);font-size:10.5px;color:var(--tinta);line-height:1.35}
.legfixa h4{font-family:var(--fonte-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--apoio);margin:0 0 8px}
.legfixa .lc{flex:none;width:330px}
.legfixa .lc:nth-child(3){width:500px}
.legfixa .lc.dupla{flex:1;width:auto}
.legfixa .li{display:flex;gap:10px;align-items:center;margin-bottom:6px}
.legfixa .pe{flex:none;width:74px;font-weight:700}
.legfixa .rv,.legfixa .ra,.legfixa .rr,.legfixa .rk{flex:none;width:140px;font-family:var(--fonte-mono);font-size:9.5px;text-align:right}
.legfixa .rv{color:var(--der-dominio)}.legfixa .ra{color:var(--der-fora);font-weight:600}.legfixa .rr{color:var(--der-copia)}.legfixa .rk{color:var(--der-chave);font-weight:700}
.legfixa .tps{columns:2;column-gap:22px}
.legfixa .tipo{break-inside:avoid;display:flex;gap:8px;align-items:flex-start;margin-bottom:5px}
.legfixa .sw{flex:none;width:14px;height:14px;border:1px solid var(--apoio)}
`;

// Faixa de domínio e configuração: caixa compacta, sem colunas, com quem usa a tabela.
export const LEVES = (k) => LEVE.has(tabela(k).tipo);
const curto = (alvo, s) => `${alvo.split('.')[0] === s ? '' : alvo.split('.')[0] + '.'}${nome(alvo)}`;
export function usos(k) {
  const s = k.split('.')[0], r = [];
  for (const [kk, t] of Object.entries(completas)) {
    if (kk === k || kk.split('.')[0] === MODELO.schemaLeitura || t.tipo === 'configuracao') continue;
    for (const [n, , chave, alvo] of t.colunas) if (chave === 'FK' && alvo === k) r.push(`${curto(kk, s)}.${n}`);
  }
  return r;
}
export function textoLeve(k) {
  const t = tabela(k), s = k.split('.')[0];
  const fks = t.colunas.filter(([, , c]) => c === 'FK').map(([, , , alvo]) => alvo);
  if (t.tipo === 'configuracao' && fks.length)
    return [texto('pares_permitidos', { tabela: curto(fks[0], s) }), texto('recusa_troca')];
  const u = usos(k);
  const linhas = u.length ? u.map((x, i) => (i ? `· ${x}` : texto('usada_por', { coluna: x }))) : [texto('sem_uso')];
  if (fks.length) linhas.push(texto('linha_leva', { tabela: curto(fks[0], s) }));
  return linhas;
}
export const HLEVE = 84;
export function caixaLeve(k, x, y, largura, h = HLEVE) {
  const tipo = tabela(k).tipo;
  return `<div class="bchip tabela leve" style="left:${x}px;top:${y}px;width:${largura}px;height:${h}px">` +
    `<div class="th" style="background:${CANDY[tipo] || CANDY.configuracao};height:24px"><div class="tt">${esc(nome(k))}${nome(k).length > 30 ? '' : `<span class="tp">${esc(TIPO[tipo])}</span>`}</div></div>` +
    textoLeve(k).map((l) => `<div class="lu">${esc(l)}</div>`).join('') + `</div>`;
}
// Fronteira: FKs que saem deste schema para outro e as que chegam de outro schema.
export function fronteira(s) {
  const comum = MODELO.schemaComum, leitura = MODELO.schemaLeitura;
  const sai = [], chega = [], cache = [], aux = new Set();
  for (const [k, t] of Object.entries(completas)) {
    const de = k.split('.')[0];
    for (const [n, , chave, alvo] of t.colunas) {
      if (chave !== 'FK') continue;
      const para = alvo.split('.')[0];
      if (de === s && para === s) continue;
      if (de === s && para === comum) aux.add(nome(alvo));
      else if (de === s && para !== s) sai.push(`${nome(k)}.${n} → ${para}.${nome(alvo)}`);
      else if (de !== s && para === s && de === leitura) cache.push(`${nome(k)}.${n} → ${nome(alvo)}`);
      else if (de !== s && para === s) chega.push(`${de}.${nome(k)}.${n} → ${nome(alvo)}`);
    }
  }
  return { sai, chega, cache, aux: [...aux].sort() };
}

// Tabela de outro schema desenhada só como alvo de seta (DER de views de leitura): contorno tracejado, nome com o schema.
export function caixaExterna(k, x, y, largura, h, descricao) {
  const t = tabela(k), cor = CANDY[t.tipo] || 'var(--der-trilha)';
  return `<div class="bchip tabela externa" style="left:${x}px;top:${y}px;width:${largura}px;height:${h}px">` +
    `<div class="th" style="background:${cor};height:${Math.min(h, HEAD) - 2}px"><div class="tt">${esc(k)}</div>` +
    `<div class="td">${esc(descricao || t.rotulo)}</div></div></div>`;
}
