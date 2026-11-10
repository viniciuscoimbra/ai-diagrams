// Lê uma lista de grafos ELK em JSON da entrada padrão e escreve a lista com posições na saída.
// O build_c4.py manda várias variantes de uma vez e fica com a de menor custo.
const ELK = require('../states/vendor/elk.bundled.js');
let entrada = '';
process.stdin.on('data', d => { entrada += d; });
process.stdin.on('end', async () => {
  const elk = new ELK();
  const saida = [];
  for (const g of JSON.parse(entrada)) {
    try { saida.push(await elk.layout(g)); } catch (e) { saida.push({erro: String(e)}); }
  }
  process.stdout.write(JSON.stringify(saida));
});
