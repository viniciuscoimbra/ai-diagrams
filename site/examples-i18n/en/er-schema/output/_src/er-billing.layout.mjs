// DER do schema cobranca. A fatura no centro; quem aponta para ela à esquerda e à direita.
// Coordenadas no canvas de 1700px; cada seta sai da linha da coluna de FK e corre pela raia indicada.
export default {
  lang: 'en',
  model: './model.json',
  schema: 'cobranca',
  title: 'schema cobranca · Invoices and receipts',
  sub: 'The customer\'s invoice, billed items, collection attempts and received payments. Payments and attempts are facts: recorded once. The daily batch groups automatic attempts and the outbox carries events to the bus.',
  canvas: { w: 1700 },
  tables: {
    'cobranca.itens_fatura': { x: 20, y: 60, desc: 'each item billed on the invoice' },
    'cobranca.outbox': { x: 20, y: 300, desc: 'event to publish, read by CDC' },
    'cobranca.faturas_cobranca': { x: 685, y: 60, desc: 'the invoice issued to the customer' },
    'cobranca.execucoes_cobranca': { x: 685, y: 398, desc: 'daily collection batch run' },
    'cobranca.pagamentos_recebidos': { x: 1350, y: 40, desc: 'each amount received; never changes' },
    'cobranca.tentativas_cobranca': { x: 1300, y: 330, desc: 'each attempt to collect the invoice' }
  },
  edges: [
    { from: 'cobranca.itens_fatura', column: 'fatura_id', exit: 'R', to: 'cobranca.faturas_cobranca', enter: 'L', lane: 500, dy: 40,
      text: 'An <b>invoice</b> has zero or many <b>items</b>; its total is their sum.' },
    { from: 'cobranca.pagamentos_recebidos', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1200, dy: 40,
      text: 'A <b>payment</b> settles an <b>invoice</b>; empty when unidentified and awaiting reconciliation.' },
    { from: 'cobranca.tentativas_cobranca', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1160, dy: 140,
      text: 'An <b>invoice</b> receives zero or many collection <b>attempts</b> until paid or canceled.' },
    { from: 'cobranca.tentativas_cobranca', column: 'execucao_id', exit: 'L', to: 'cobranca.execucoes_cobranca', enter: 'R', dy: 'straight',
      text: 'The batch <b>run</b> groups automatic <b>attempts</b>; manual attempts have no run.' },
    { from: 'cobranca.tentativas_cobranca', column: 'pagamento_recebido_id', exit: 'R', to: 'cobranca.pagamentos_recebidos', enter: 'B',
      points: [['x0', 'y0'], [1660, 'y0'], [1660, 219]],
      text: 'A successful <b>attempt</b> points to the resulting <b>payment</b>; empty for failed attempts.' }
  ]
};
