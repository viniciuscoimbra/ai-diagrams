import fs from 'node:fs';

const avisado = new Set();
export function avisarAntigo(antigo, novo) {
  if (avisado.has(antigo)) return;
  avisado.add(antigo);
  console.error(`ai-diagrams: ${antigo} is deprecated; use ${novo}`);
}

// Tira --lang X (ou --lang=X) do argv; --idioma ainda vale até 0.3.0, com aviso.
export function tirarIdioma(argv) {
  const resto = []; let valor;
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i].split('=')[0];
    if (flag === '--lang' || flag === '--idioma') {
      if (flag === '--idioma') avisarAntigo('--idioma', '--lang');
      if (argv[i].includes('=')) valor = argv[i].slice(flag.length + 1);
      else {
        valor = argv[++i];
        if (!valor || valor.startsWith('--')) throw new Error('LANG-NOT-FOUND: use pt-BR, en or es');
      }
    } else resto.push(argv[i]);
  }
  return { valor, resto };
}

export function validarCatalogo(catalogo, padrao) {
  for (const chave of Object.keys(padrao)) {
    if (typeof catalogo[chave] !== 'string') throw new Error(`LANG-INCOMPLETE: missing ${chave}`);
  }
}

function idiomaDoAmbiente() {
  if (process.env.AI_DIAGRAMS_LANG !== undefined) return process.env.AI_DIAGRAMS_LANG;
  if (process.env.AI_DIAGRAMS_IDIOMA !== undefined) {
    avisarAntigo('AI_DIAGRAMS_IDIOMA', 'AI_DIAGRAMS_LANG');
    return process.env.AI_DIAGRAMS_IDIOMA;
  }
  return undefined;
}

export function carregarIdioma(flag, fonte = {}) {
  const escolhido = flag ?? fonte.idioma ?? fonte.lang ?? idiomaDoAmbiente();
  const codigo = escolhido ?? 'pt-BR';
  if (!['pt-BR', 'en', 'es'].includes(codigo)) throw new Error(`LANG-NOT-FOUND: ${codigo}`);
  const ler = (nome) => {
    try { return JSON.parse(fs.readFileSync(new URL(`../i18n/${nome}.json`, import.meta.url), 'utf8')); }
    catch (erro) { throw new Error(`LANG-NOT-FOUND: ${nome}: ${erro.message}`); }
  };
  const catalogos = Object.fromEntries(['pt-BR', 'en', 'es'].map((nome) => [nome, ler(nome)]));
  const chaves = Object.assign({}, ...Object.values(catalogos));
  for (const catalogo of Object.values(catalogos)) validarCatalogo(catalogo, chaves);
  const catalogo = catalogos[codigo];
  const t = (chave, valores = {}) => {
    if (typeof catalogo[chave] !== 'string') throw new Error(`LANG-INCOMPLETE: missing ${chave}`);
    return catalogo[chave].replace(/\{(\w+)\}/g, (original, nome) => Object.hasOwn(valores, nome) ? String(valores[nome]) : original);
  };
  return { codigo, t, meta: escolhido === undefined ? '' : `<meta name="lang" content="${codigo}">` };
}
