# Autorização de compra no cartão de débito

Documento de exemplo. Descreve o caminho de uma compra com cartão de débito, do terminal da loja até a resposta de aprovação ou recusa.

## Participantes

- **Terminal da loja** (POS ou e-commerce): envia a compra para o adquirente.
- **Bandeira**: roteia a mensagem ISO 8583 `0100` do adquirente para o emissor.
- **Autorizador**: serviço do emissor em ECS Fargate que recebe a `0100` por um Network Load Balancer e responde com a `0110`.
- **Antifraude**: endpoint SageMaker que devolve um score entre 0 e 1.
- **Ledger**: Aurora PostgreSQL com saldo, bloqueio e outbox.
- **Notificações**: fila SQS consumida pelo serviço de push.

## Caminho

1. O terminal envia a compra; a bandeira entrega a `0100` ao autorizador.
2. O autorizador valida o cartão (situação, validade, criptograma) sem chamar ninguém.
3. O autorizador chama o antifraude e espera o score. O tempo máximo é 120 ms; sem resposta, segue como score 0,5.
4. Score abaixo de 0,85:
   - o autorizador pede ao ledger o bloqueio do valor; o ledger confere o saldo e grava o bloqueio e a linha da outbox na mesma transação;
   - com saldo, a resposta é `0110` com código `00` (aprovada);
   - sem saldo, a resposta é `0110` com código `51` (saldo insuficiente) e nada é bloqueado.
5. Score a partir de 0,85: a resposta é `0110` com código `59` (suspeita de fraude), sem consultar o ledger.
6. Em todos os casos o autorizador responde à bandeira, que responde ao terminal.
7. Só na compra aprovada, o autorizador publica o evento `compra.aprovada` na fila de notificações, sem esperar resposta. O cliente recebe o push.

## Fora do escopo

Captura e liquidação (arquivo do adquirente no dia seguinte), estorno e compra parcelada.
