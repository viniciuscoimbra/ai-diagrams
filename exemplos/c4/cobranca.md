# Sistema de cobrança por boleto

Documento de exemplo. Descreve o sistema que emite e baixa boletos para clientes PJ, no nível de contêineres.

## Quem usa

- **Cliente PJ**: emite boletos e acompanha os pagamentos pelo portal web ou pela API.
- **Analista financeiro**: trata boleto pago em duplicidade e devolução, pelo backoffice.

## Contêineres do sistema

- **Portal PJ** (Next.js na Vercel): tela de emissão em lote e painel de recebimentos.
- **API de cobrança** (Node.js em Lambda atrás do API Gateway): recebe o pedido de emissão, valida o pagador e grava o boleto.
- **Banco de cobrança** (DynamoDB): boletos, situação e histórico de eventos.
- **Processador de retorno** (Lambda acionada por fila SQS): lê o arquivo de retorno do banco liquidante e dá baixa no boleto.
- **Backoffice** (React): consulta e ajuste manual, usa a mesma API com papel de operador.

## Sistemas de fora

- **CIP · Nova Plataforma de Cobrança** (registro do boleto): a API registra cada boleto antes de devolver a linha digitável. Mensageria via HTTPS com certificado.
- **Banco liquidante** (parceiro): manda o arquivo CNAB 240 de retorno por SFTP para um bucket; o evento do bucket vai para a fila do processador.
- **Webhook do cliente**: o processador avisa o cliente PJ a cada boleto pago, por HTTPS com assinatura HMAC.
- **ERP contábil** (outro time): recebe o lançamento de cada baixa por evento no EventBridge.

## Fora do escopo

Pix cobrança, protesto e negativação.
