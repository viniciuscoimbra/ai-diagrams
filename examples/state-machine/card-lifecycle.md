# Ciclo de vida do cartão de débito

Documento de exemplo. Descreve as situações de um cartão de débito no emissor, da solicitação ao cancelamento. A situação fica gravada na tabela `cartao` e cada mudança gera um evento.

## Situações

- **Solicitado**: o cliente pediu o cartão no app. Ainda não há plástico.
- **Em emissão**: o pedido foi para a gráfica; o número e o criptograma já existem.
- **Em trânsito**: a gráfica entregou ao Correio, com código de rastreio.
- **Aguardando ativação**: o cartão chegou ao cliente, mas não aceita compra.
- **Ativo**: aceita compra.
- **Bloqueado**: o cliente bloqueou pelo app. Volta para Ativo quando ele desbloqueia.
- **Cancelado**: não volta mais. O número não é reaproveitado.
- **Extraviado**: o Correio devolveu ou perdeu o envio. Não volta mais; a gráfica emite outro cartão, com outro número.

## Mudanças

1. A gráfica confirma o pedido: Solicitado passa a Em emissão.
2. O pedido é recusado na análise de cadastro: Solicitado passa a Cancelado.
3. A gráfica informa a postagem: Em emissão passa a Em trânsito, e o app recebe o código de rastreio.
4. O Correio confirma a entrega: Em trânsito passa a Aguardando ativação.
5. O Correio devolve o envio ou o rastreio fica 30 dias parado: Em trânsito passa a Extraviado, e um novo pedido é aberto.
6. O cliente ativa com os 4 últimos dígitos e a senha: Aguardando ativação passa a Ativo.
7. Errar a senha na ativação não muda a situação; na terceira tentativa errada, o cartão passa a Bloqueado.
8. O cliente bloqueia no app: Ativo passa a Bloqueado. Desbloquear volta para Ativo.
9. O cliente cancela, ou o cartão vence: Ativo ou Bloqueado passa a Cancelado.

## Fora do escopo

Cartão virtual, segunda via por dano e cartão de crédito.
