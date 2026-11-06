// DER do schema cobranca. A fatura no centro; quem aponta para ela à esquerda e à direita.
// Coordenadas no canvas de 1700px; cada seta sai da linha da coluna de FK e corre pela raia indicada.
export default {
  modelo: './modelo.json',
  schema: 'cobranca',
  titulo: 'schema cobranca · Faturas e recebimentos',
  sub: 'A fatura emitida para o cliente, os itens cobrados, as tentativas de cobrança e os pagamentos recebidos. Pagamento e tentativa são fatos: gravados uma vez. O lote diário agrupa as tentativas automáticas e a outbox leva os eventos para o barramento.',
  canvas: { w: 1700 },
  tabelas: {
    'cobranca.itens_fatura': { x: 20, y: 60, desc: 'cada linha cobrada na fatura' },
    'cobranca.outbox': { x: 20, y: 300, desc: 'evento a publicar, lido pelo CDC' },
    'cobranca.faturas_cobranca': { x: 685, y: 60, desc: 'a fatura emitida para o cliente' },
    'cobranca.execucoes_cobranca': { x: 685, y: 398, desc: 'execução do lote de cobrança do dia' },
    'cobranca.pagamentos_recebidos': { x: 1350, y: 40, desc: 'cada valor recebido; nunca muda' },
    'cobranca.tentativas_cobranca': { x: 1300, y: 330, desc: 'cada tentativa de cobrar a fatura' }
  },
  arestas: [
    { de: 'cobranca.itens_fatura', coluna: 'fatura_id', sai: 'R', para: 'cobranca.faturas_cobranca', chega: 'L', raia: 500, dy: 40,
      texto: 'Uma <b>fatura</b> tem zero ou muitos <b>itens</b>; o valor total é a soma deles.' },
    { de: 'cobranca.pagamentos_recebidos', coluna: 'fatura_id', sai: 'L', para: 'cobranca.faturas_cobranca', chega: 'R', raia: 1200, dy: 40,
      texto: 'Um <b>pagamento</b> quita uma <b>fatura</b>; vazio quando chega sem identificação e espera a conciliação.' },
    { de: 'cobranca.tentativas_cobranca', coluna: 'fatura_id', sai: 'L', para: 'cobranca.faturas_cobranca', chega: 'R', raia: 1160, dy: 140,
      texto: 'Uma <b>fatura</b> recebe zero ou muitas <b>tentativas</b> de cobrança até ser paga ou cancelada.' },
    { de: 'cobranca.tentativas_cobranca', coluna: 'execucao_id', sai: 'L', para: 'cobranca.execucoes_cobranca', chega: 'R', dy: 'reto',
      texto: 'A <b>execução</b> do lote agrupa as <b>tentativas</b> automáticas; tentativa manual fica sem execução.' },
    { de: 'cobranca.tentativas_cobranca', coluna: 'pagamento_recebido_id', sai: 'R', para: 'cobranca.pagamentos_recebidos', chega: 'B',
      pontos: [['x0', 'y0'], [1660, 'y0'], [1660, 219]],
      texto: 'A <b>tentativa</b> que deu certo aponta o <b>pagamento</b> gerado; vazio nas que falharam.' }
  ]
};
