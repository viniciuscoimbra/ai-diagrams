# Conciliação diária de pagamentos com o arquivo do parceiro

## Contexto

O parceiro de liquidação envia todo dia, até as 6h, um arquivo CSV com os pagamentos liquidados no dia anterior (D-1). A conciliação confere cada linha do arquivo contra o que o nosso ledger registrou. Volume típico: 400 mil linhas por arquivo, cerca de 60 MB.

## Fluxo

1. O parceiro grava o arquivo `liquidacao_AAAAMMDD.csv` no bucket S3 de entrada, no prefixo `parceiro/`.
2. O S3 emite o evento `Object Created` para o EventBridge.
3. Uma regra do EventBridge filtra o prefixo e inicia uma execução do Step Functions.
4. O Step Functions divide o arquivo em lotes de 5.000 linhas (estado Map distribuído) e chama a Lambda conciliação para cada lote.
5. A Lambda lê o lote direto do S3.
6. A Lambda compara cada linha com a tabela `pagamentos` do Aurora PostgreSQL pelo id da transação: valor, data de liquidação e situação.
7. Cada divergência (pagamento ausente no ledger, ausente no arquivo, valor diferente) vira uma mensagem na fila SQS de divergências.
8. O analista de conciliação trata a fila pelo console interno; mensagem com 3 falhas de processamento vai para a DLQ.

## Regras

- Execução idempotente: o nome do arquivo é a chave da execução; reenvio do mesmo arquivo não gera divergência duplicada.
- Prazo: conciliação fechada até as 9h.
- Divergência acima de R$ 10 mil tem prioridade na fila.

## Números medidos (setembro)

- Duração média da execução: 11 minutos.
- Divergências por dia: 30 a 80, 90% delas por diferença de data de liquidação.
