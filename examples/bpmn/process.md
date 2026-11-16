# Processo: recuperação de acesso à conta

Fintech de exemplo. O cliente perdeu a senha ou trocou de celular e não consegue entrar no app.

## Atores

- **Cliente**: pede a recuperação e, no fim, entra com a nova senha.
- **App**: coleta documento e selfie, cadastra a nova senha e o novo dispositivo.
- **Segurança**: verifica a identidade por biometria facial e bloqueia a conta quando há suspeita de fraude.
- **Central de atendimento**: faz a validação manual por chamada quando a verificação automática não confirma a identidade.

## Passos

1. O cliente toca em "Não consigo entrar" e pede a recuperação de acesso.
2. O app coleta foto do documento e uma selfie.
3. A segurança compara a selfie com a foto do documento e com a base do cadastro.
4. Decisão: a identidade foi confirmada?
   - Sim: o app cadastra a nova senha e vincula o novo dispositivo.
   - Não: o caso vai para a central de atendimento.
5. A central liga para o cliente e confere dados que só o titular conhece.
6. Decisão: a validação por chamada foi aceita?
   - Sim: volta ao app, que cadastra a nova senha e o dispositivo.
   - Não: a segurança bloqueia a conta e registra a suspeita de fraude. Fim: conta bloqueada.
7. Com a senha nova, o cliente entra na conta. Fim: acesso recuperado.

## Regras

- A verificação por biometria tem SLA de 2 minutos; acima disso, o caso também vai para a central.
- A conta bloqueada só é liberada presencialmente ou por novo processo com a segurança.
