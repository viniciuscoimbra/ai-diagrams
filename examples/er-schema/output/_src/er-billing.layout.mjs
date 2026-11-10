// DER do schema cobranca. A fatura no centro; quem aponta para ela à esquerda e à direita.
// Coordenadas no canvas de 1700px; cada seta sai da linha da coluna de FK e corre pela raia indicada.
export default {
  model: './model.json',
  schema: 'cobranca',
  title: 'schema cobranca · Faturas e recebimentos',
  sub: 'A fatura emitida para o cliente, os itens cobrados, as tentativas de cobrança e os pagamentos recebidos. Pagamento e tentativa são fatos: gravados uma vez. O lote diário agrupa as tentativas automáticas e a outbox leva os eventos para o barramento.',
  canvas: { w: 1700 },
  tables: {
    'cobranca.itens_fatura': { x: 20, y: 60, desc: 'cada linha cobrada na fatura' },
    'cobranca.outbox': { x: 20, y: 300, desc: 'evento a publicar, lido pelo CDC' },
    'cobranca.faturas_cobranca': { x: 685, y: 60, desc: 'a fatura emitida para o cliente' },
    'cobranca.execucoes_cobranca': { x: 685, y: 398, desc: 'execução do lote de cobrança do dia' },
    'cobranca.pagamentos_recebidos': { x: 1350, y: 40, desc: 'cada valor recebido; nunca muda' },
    'cobranca.tentativas_cobranca': { x: 1300, y: 330, desc: 'cada tentativa de cobrar a fatura' }
  },
  edges: [
    { from: 'cobranca.itens_fatura', column: 'fatura_id', exit: 'R', to: 'cobranca.faturas_cobranca', enter: 'L', lane: 500, dy: 40,
      text: 'Uma <b>fatura</b> tem zero ou muitos <b>itens</b>; o valor total é a soma deles.' },
    { from: 'cobranca.pagamentos_recebidos', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1200, dy: 40,
      text: 'Um <b>pagamento</b> quita uma <b>fatura</b>; vazio quando chega sem identificação e espera a conciliação.' },
    { from: 'cobranca.tentativas_cobranca', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1160, dy: 140,
      text: 'Uma <b>fatura</b> recebe zero ou muitas <b>tentativas</b> de cobrança até ser paga ou cancelada.' },
    { from: 'cobranca.tentativas_cobranca', column: 'execucao_id', exit: 'L', to: 'cobranca.execucoes_cobranca', enter: 'R', dy: 'straight',
      text: 'A <b>execução</b> do lote agrupa as <b>tentativas</b> automáticas; tentativa manual fica sem execução.' },
    { from: 'cobranca.tentativas_cobranca', column: 'pagamento_recebido_id', exit: 'R', to: 'cobranca.pagamentos_recebidos', enter: 'B',
      points: [['x0', 'y0'], [1660, 'y0'], [1660, 219]],
      text: 'A <b>tentativa</b> que deu certo aponta o <b>pagamento</b> gerado; vazio nas que falharam.' }
  ]
};
