# Decisão: antifraude em tempo real de transferências

Status: aprovada · 2026-10

## Contexto

Toda transferência iniciada no app passa por uma decisão de risco antes de sair da conta. Hoje a regra roda em lote a cada 15 minutos e só pega a fraude depois que o dinheiro saiu. A decisão precisa acontecer na mesma chamada da transferência, com orçamento de 300 ms no p99.

Volume medido: 1,8 milhão de transferências por dia, pico de 120 por segundo no horário de almoço.

## Decisão

1. O app chama `POST /transferencias` no **API Gateway**, com o token da sessão.
2. O API Gateway invoca a **Lambda decisão** de forma síncrona.
3. A Lambda lê as features da conta e do destinatário no **DynamoDB features** (valor médio dos últimos 30 dias, quantidade de destinatários novos em 24 horas, idade da chave de destino).
4. A Lambda chama o **SageMaker endpoint** com o vetor de features e recebe um score de 0 a 1.
5. Pela faixa do score, a Lambda devolve ao app `aprovar`, `revisar` ou `bloquear` e publica o evento `decisao registrada v1` no **Kinesis Data Streams**, com o id da conta como partition key.
6. A **Lambda features** consome o stream e recalcula os agregados da conta.
7. Os agregados atualizados voltam para o DynamoDB features e valem para a próxima transferência.
8. A **Lambda alerta** consome o mesmo stream e filtra as decisões `revisar` e `bloquear`.
9. A Lambda alerta publica no tópico **SNS** de casos para análise.
10. O **analista de prevenção** recebe o caso pela assinatura do tópico e decide no console interno.

## Faixas do score

| Faixa | Decisão | Efeito |
|---|---|---|
| abaixo de 0,40 | aprovar | transferência segue |
| 0,40 a 0,85 | revisar | transferência retida até o analista decidir, prazo de 30 minutos |
| acima de 0,85 | bloquear | transferência recusada e cliente avisado |

## Alternativas descartadas

- Regra em lote no Aurora: não decide antes de o dinheiro sair.
- Chamar o modelo de dentro do API Gateway com integração direta: sem lugar para ler features e aplicar a faixa.

## Fora do escopo

Treino e publicação de nova versão do modelo; ficam no pipeline de ML, em documento próprio.
