# Processo: solicitação de aumento de limite

## Atores

- **Cliente**: pede o aumento pelo app.
- **App**: canal digital; valida a sessão e conversa com o motor.
- **Motor de crédito**: aplica a política de crédito de forma automática.
- **Analista de crédito**: decide os pedidos que o motor não decide sozinho.
- **Operações**: aplica o limite novo na conta.

## Etapas

1. O cliente abre a tela de limite, informa o valor desejado e a renda atual e confirma o pedido.
2. O app valida a sessão, confere se já existe pedido aberto para a conta e envia o pedido ao motor de crédito. Situação: **recebido**.
3. O motor calcula o score com os dados de movimentação dos últimos 12 meses e o limite máximo permitido pela política. Situação: **em avaliação**.
   - Valor pedido até o limite máximo e score acima do corte: aprovado direto, segue para operações.
   - Valor acima do limite máximo ou score na faixa cinza: vai para o analista.
   - Score abaixo do corte: recusado; o cliente pode pedir de novo em 90 dias.
4. O analista de crédito revisa o pedido, pode pedir comprovante de renda pelo app e decide aprovar, aprovar com valor menor ou recusar. Prazo: 1 dia útil. Situação: **em análise**.
5. Operações aplica o limite novo na conta e registra a trilha de auditoria da decisão.
6. O app avisa o cliente com o limite aprovado. Situação: **concluído**.
7. O cliente vê o limite novo na tela da conta.

## Números (último trimestre)

- 42 mil pedidos por mês.
- 71% decididos pelo motor sem analista.
- Tempo médio até o aviso: 3 minutos sem analista, 9 horas com analista.

## Quem recebe o resultado

- Cliente: o limite novo, ou o motivo da recusa e a data para pedir de novo.
- Analista de crédito: o resultado de cada caso volta para a calibragem da política.
- Atendimento: o histórico do pedido para responder dúvidas.
