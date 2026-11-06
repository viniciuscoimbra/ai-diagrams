import fs from 'node:fs';

export function tirarIdioma(argv) {
  const resto = []; let valor;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--idioma') {
      valor = argv[++i];
      if (!valor || valor.startsWith('--')) throw new Error('IDIOMA-INEXISTENTE: informe pt-BR, en ou es');
    } else if (argv[i].startsWith('--idioma=')) valor = argv[i].slice(9);
    else resto.push(argv[i]);
  }
  return { valor, resto };
}

export function validarCatalogo(catalogo, padrao) {
  for (const chave of Object.keys(padrao)) {
    if (typeof catalogo[chave] !== 'string') throw new Error(`IDIOMA-INCOMPLETO: falta ${chave}`);
  }
}

export function carregarIdioma(flag, fonte = {}) {
  const escolhido = flag ?? fonte.idioma ?? process.env.AI_DIAGRAMS_IDIOMA;
  const codigo = escolhido ?? 'pt-BR';
  if (!['pt-BR', 'en', 'es'].includes(codigo)) throw new Error(`IDIOMA-INEXISTENTE: ${codigo}`);
  const ler = (nome) => {
    try { return JSON.parse(fs.readFileSync(new URL(`../i18n/${nome}.json`, import.meta.url), 'utf8')); }
    catch (erro) { throw new Error(`IDIOMA-INEXISTENTE: ${nome}: ${erro.message}`); }
  };
  const catalogos = Object.fromEntries(['pt-BR', 'en', 'es'].map((nome) => [nome, ler(nome)]));
  const chaves = Object.assign({}, ...Object.values(catalogos));
  for (const catalogo of Object.values(catalogos)) validarCatalogo(catalogo, chaves);
  const catalogo = catalogos[codigo];
  const t = (chave, valores = {}) => {
    if (typeof catalogo[chave] !== 'string') throw new Error(`IDIOMA-INCOMPLETO: falta ${chave}`);
    return catalogo[chave].replace(/\{(\w+)\}/g, (original, nome) => Object.hasOwn(valores, nome) ? String(valores[nome]) : original);
  };
  return { codigo, t, meta: escolhido === undefined ? '' : `<meta name="idioma" content="${codigo}">` };
}
