// Lê um grafo ELK em JSON da entrada padrão e escreve o grafo com posições na saída.
// Só posição e roteamento: o desenho é do gerar_estados.py.
const ELK = require('./vendor/elk.bundled.js');
let entrada = '';
process.stdin.on('data', d => { entrada += d; });
process.stdin.on('end', () => {
  new ELK().layout(JSON.parse(entrada))
    .then(g => process.stdout.write(JSON.stringify(g)))
    .catch(e => { process.stderr.write(String(e) + '\n'); process.exit(1); });
});
