// DER do schema conta. A conta no centro; quem aponta para ela à esquerda e à direita.
// Coordenadas no canvas de 1700px; cada seta sai da linha da coluna de FK e corre pela raia indicada.
export default {
  model: './model.json',
  schema: 'conta',
  title: 'schema conta · Contas e movimentos',
  sub: 'A conta de pagamento, quem pode movimentá-la, os movimentos que ela recebe e o saldo calculado a partir deles. O limite é versionado: cada mudança cria uma linha nova. A outbox leva os eventos para o barramento.',
  canvas: { w: 1700 },
  tables: {
    'conta.titulares': { x: 20, y: 60, desc: 'quem pode movimentar a conta e com qual papel' },
    'conta.limites': { x: 20, y: 420, desc: 'limite da conta; uma linha por mudança' },
    'conta.outbox': { x: 685, y: 40, desc: 'evento a publicar, lido pelo CDC' },
    'conta.contas': { x: 685, y: 260, desc: 'a conta de pagamento do cliente' },
    'conta.fechamentos_diarios': { x: 685, y: 500, desc: 'execução do fechamento de cada dia' },
    'conta.movimentos': { x: 1350, y: 60, desc: 'cada crédito ou débito; nunca muda' },
    'conta.saldos': { x: 1300, y: 420, desc: 'saldo calculado a partir dos movimentos' }
  },
  edges: [
    { from: 'conta.titulares', column: 'conta_id', exit: 'R', to: 'conta.contas', enter: 'L', lane: 500, dy: 40,
      text: 'Uma <b>conta</b> tem zero ou muitos <b>titulares</b>; o mesmo cliente pode ser titular de várias contas.' },
    { from: 'conta.limites', column: 'conta_id', exit: 'R', to: 'conta.contas', enter: 'L', lane: 540, dy: 120,
      text: 'Cada mudança de <b>limite</b> grava uma versão nova; a vigente é a de maior <code>versao</code>.' },
    { from: 'conta.movimentos', column: 'conta_id', exit: 'L', to: 'conta.contas', enter: 'R', lane: 1200, dy: 40,
      text: 'Uma <b>conta</b> recebe zero ou muitos <b>movimentos</b>; o tipo aponta o domínio <code>tipos_movimento</code>.' },
    { from: 'conta.saldos', column: 'conta_id', exit: 'L', to: 'conta.contas', enter: 'R', lane: 1160, dy: 120,
      text: 'Cada <b>conta</b> tem a linha de <b>saldo</b> dela, recalculada a cada movimento aplicado.' },
    { from: 'conta.saldos', column: 'ultimo_movimento_id', exit: 'R', to: 'conta.movimentos', enter: 'B',
      points: [['x0', 'y0'], [1660, 'y0'], [1660, 239]],
      text: 'O <b>saldo</b> guarda o último <b>movimento</b> aplicado; vazio enquanto a conta não tem movimento.' }
  ]
};
