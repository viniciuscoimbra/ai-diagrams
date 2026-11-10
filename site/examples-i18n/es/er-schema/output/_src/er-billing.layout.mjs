// DER do schema cobranca. A fatura no centro; quem aponta para ela à esquerda e à direita.
// Coordenadas no canvas de 1700px; cada seta sai da linha da coluna de FK e corre pela raia indicada.
export default {
  lang: 'es',
  model: './model.json',
  schema: 'cobranca',
  title: 'schema cobranca · Facturas y cobros',
  sub: 'La factura emitida al cliente, los conceptos cobrados, los intentos de cobro y los pagos recibidos. Pagos e intentos son hechos: se registran una vez. El lote diario agrupa los intentos automáticos y la outbox lleva los eventos al bus.',
  canvas: { w: 1700 },
  tables: {
    'cobranca.itens_fatura': { x: 20, y: 60, desc: 'cada concepto cobrado en la factura' },
    'cobranca.outbox': { x: 20, y: 300, desc: 'evento a publicar, leído por CDC' },
    'cobranca.faturas_cobranca': { x: 685, y: 60, desc: 'la factura emitida al cliente' },
    'cobranca.execucoes_cobranca': { x: 685, y: 398, desc: 'ejecución del lote de cobro del día' },
    'cobranca.pagamentos_recebidos': { x: 1350, y: 40, desc: 'cada importe recibido; nunca cambia' },
    'cobranca.tentativas_cobranca': { x: 1300, y: 330, desc: 'cada intento de cobrar la factura' }
  },
  edges: [
    { from: 'cobranca.itens_fatura', column: 'fatura_id', exit: 'R', to: 'cobranca.faturas_cobranca', enter: 'L', lane: 500, dy: 40,
      text: 'Una <b>factura</b> tiene cero o muchos <b>conceptos</b>; el importe total es su suma.' },
    { from: 'cobranca.pagamentos_recebidos', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1200, dy: 40,
      text: 'Un <b>pago</b> liquida una <b>factura</b>; vacío si llega sin identificar y espera la conciliación.' },
    { from: 'cobranca.tentativas_cobranca', column: 'fatura_id', exit: 'L', to: 'cobranca.faturas_cobranca', enter: 'R', lane: 1160, dy: 140,
      text: 'Una <b>factura</b> recibe cero o muchos <b>intentos</b> de cobro hasta que se paga o cancela.' },
    { from: 'cobranca.tentativas_cobranca', column: 'execucao_id', exit: 'L', to: 'cobranca.execucoes_cobranca', enter: 'R', dy: 'straight',
      text: 'La <b>ejecución</b> del lote agrupa los <b>intentos</b> automáticos; un intento manual queda sin ejecución.' },
    { from: 'cobranca.tentativas_cobranca', column: 'pagamento_recebido_id', exit: 'R', to: 'cobranca.pagamentos_recebidos', enter: 'B',
      points: [['x0', 'y0'], [1660, 'y0'], [1660, 219]],
      text: 'El <b>intento</b> exitoso apunta al <b>pago</b> generado; vacío en los intentos fallidos.' }
  ]
};
