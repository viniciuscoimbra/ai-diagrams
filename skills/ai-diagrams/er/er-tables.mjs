// Conteúdo das caixas de tabela dos DERs, lido do modelo lógico (model.json, formato em references/er.md).
// O layout (posição de cada caixa e o caminho de cada seta) é decidido à mão no arquivo der-<schema>.layout.mjs;
// este módulo só calcula o que vai dentro da caixa e a altura dela, e gera o HTML da caixa.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { carregarIdioma, avisarAntigo } from './lang.mjs';
import { ler } from './spec.mjs';

// Tema: tira --theme X (ou --theme=X; --tema ainda vale, com aviso) do argv e pede ao scripts/theme.py, o único leitor do json do tema,
// o link das fontes e a meta que o fonte HTML grava. Tema inexistente ou incompleto encerra aqui.
export function tirarTema(argv) {
  const resto = []; let valor = null;
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i].split('=')[0];
    if (flag === '--theme' || flag === '--tema') {
      if (flag === '--tema') avisarAntigo('--tema', '--theme');
      valor = argv[i].includes('=') ? argv[i].slice(flag.length + 1) : argv[++i];
      continue;
    }
    resto.push(argv[i]);
  }
  return { valor, resto };
}
export function temaDoGerador(valor, saida) {
  const script = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'theme.py');
  const args = [script, ...(valor ? ['--theme', valor] : []), '--generator', saida];
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
  MODELO = ler('er_model', JSON.parse(fs.readFileSync(caminho, 'utf8')));
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
  forte: 'var(--er-strong)', dependente: 'var(--er-dependent)', associativa: 'var(--er-associative)', controle: 'var(--er-control)', fato: 'var(--er-fact)',
  versionada: 'var(--er-versioned)', projecao: 'var(--er-projection)', trilha: 'var(--er-trail)', dominio: 'var(--er-domain-bg)', configuracao: 'var(--er-config)', referencia: 'var(--er-reference)', visao: 'var(--er-view)'
};
export const TIPO = {}, SIGNIFICADO = {};

const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export const nome = (k) => k.split('.')[1];
export const tabela = (k) => {
  if (!completas[k]) throw new Error(`table ${k} not found in the model`);
  return completas[k];
};
export const chaves = (s) => Object.keys(completas).filter((k) => k.startsWith(`${s}.`));
// FK obrigatória: quinto campo da coluna no modelo (true quando a coluna é not null).
export function obrigatoria(k, coluna) {
  const c = tabela(k).colunas.find(([n]) => n === coluna);
  if (!c) throw new Error(`${k} has no column ${coluna}`);
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
  if (i < 0) throw new Error(`${k} has no column ${coluna}`);
  return HEAD + i * ROW + ROW / 2 + 4;
}

export function caixa(k, x, y, descricao, largura = LARG) {
  const t = tabela(k), ls = linhas(k, largura), h = altura(k);
  const cor = CANDY[t.tipo] || 'var(--er-trail)';
  const rows = ls.map((l) => `<div class="tr"><span class="tk">${esc(l.marca)}</span><span class="tn">${esc(l.n)}</span><span class="ti ${l.cls || ''}">${esc(l.info)}</span></div>`).join('');
  return `<div class="bchip tabela" style="left:${x}px;top:${y}px;width:${largura}px;height:${h}px">` +
    `<div class="th" style="background:${cor}"><div class="tt">${esc(nome(k))}<span class="tp">${esc(TIPO[t.tipo] || t.tipo)}</span></div>` +
    `<div class="td">${esc(descricao || t.rotulo)}</div></div>${rows}</div>`;
}

export const CSS_LOCAL = `
.bchip.tabela{padding:0;border:1.4px solid var(--support);border-left:1.4px solid var(--support);background:var(--paper);overflow:hidden}
.tabela .th{height:${HEAD}px;padding:6px 10px;border-bottom:1px solid var(--support)}
.tabela .tt{font-size:13px;font-weight:700;font-family:var(--font-mono);color:var(--ink);display:flex;justify-content:space-between;align-items:baseline}
.tabela .tp{font-family:var(--font-text);font-size:9px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--support)}
.tabela .td{font-size:10.5px;color:var(--ink);line-height:1.25;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tabela .tr{height:${ROW}px;display:flex;align-items:center;padding:0 10px;font-family:var(--font-mono);font-size:10.5px}
.tabela .tr:nth-child(odd){background:var(--er-row-even)}
.tabela .tk{width:24px;flex:none;font-size:9px;font-weight:700;color:var(--er-key)}
.tabela .tn{flex:1;min-width:0;font-size:10px;color:var(--ink);white-space:nowrap;overflow:hidden;padding-right:6px}
.tabela .ti{flex:none;max-width:165px;text-align:right;font-size:9px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tabela .ti.dom{color:var(--er-domain)}
.tabela .ti.fora{color:var(--er-external);font-weight:600}
.tabela .ti.cop{color:var(--er-copy)}
.tabela.externa{border-style:dashed}
.tabela.externa .th{border-bottom:none}
.tabela.leve .th{padding:4px 10px}
.tabela.leve .tt{font-size:11.5px}
.tabela .lu{font-size:9.5px;color:var(--er-domain);padding:2px 10px 0;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.front{position:absolute;font-size:10.5px;color:var(--ink);line-height:1.55}
.front h4{font-family:var(--font-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--support);margin:0 0 4px}
.front code{font-family:var(--font-mono);font-size:10px}
.front .fora{color:var(--er-external);font-weight:600}
.sub{min-height:66px}
.legfixa{display:flex;gap:28px;margin-top:22px;padding:14px 18px;border:1px solid var(--er-border);background:var(--er-legend);font-size:10.5px;color:var(--ink);line-height:1.35}
.legfixa h4{font-family:var(--font-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--support);margin:0 0 8px}
.legfixa .lc{flex:none;width:330px}
.legfixa .lc:nth-child(3){width:500px}
.legfixa .lc.dupla{flex:1;width:auto}
.legfixa .li{display:flex;gap:10px;align-items:center;margin-bottom:6px}
.legfixa .pe{flex:none;width:74px;font-weight:700}
.legfixa .rv,.legfixa .ra,.legfixa .rr,.legfixa .rk{flex:none;width:140px;font-family:var(--font-mono);font-size:9.5px;text-align:right}
.legfixa .rv{color:var(--er-domain)}.legfixa .ra{color:var(--er-external);font-weight:600}.legfixa .rr{color:var(--er-copy)}.legfixa .rk{color:var(--er-key);font-weight:700}
.legfixa .tps{columns:2;column-gap:22px}
.legfixa .tipo{break-inside:avoid;display:flex;gap:8px;align-items:flex-start;margin-bottom:5px}
.legfixa .sw{flex:none;width:14px;height:14px;border:1px solid var(--support)}
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
  const t = tabela(k), cor = CANDY[t.tipo] || 'var(--er-trail)';
  return `<div class="bchip tabela externa" style="left:${x}px;top:${y}px;width:${largura}px;height:${h}px">` +
    `<div class="th" style="background:${cor};height:${Math.min(h, HEAD) - 2}px"><div class="tt">${esc(k)}</div>` +
    `<div class="td">${esc(descricao || t.rotulo)}</div></div></div>`;
}
