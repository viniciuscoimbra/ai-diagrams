# Decisión: prevención de fraude en transferencias en tiempo real

Estado: aprobada · 2026-10

## Contexto

Cada transferencia iniciada en la app pasa por una decisión de riesgo antes de salir de la cuenta. Hoy la regla se ejecuta por lotes cada 15 minutos y solo detecta el fraude después de que el dinero haya salido. La decisión debe ocurrir en la misma llamada de la transferencia, con un presupuesto de 300 ms en p99.

Volumen medido: 1,8 millones de transferencias al día, con un pico de 120 por segundo a la hora del almuerzo.

## Decisión

1. La app llama a `POST /transferencias` en **API Gateway**, con el token de sesión.
2. API Gateway invoca la **Lambda de decisión** de forma síncrona.
3. La Lambda lee las features de la cuenta y del destinatario en **DynamoDB features** (importe medio de los últimos 30 días, número de destinatarios nuevos en 24 horas y antigüedad de la clave de destino).
4. La Lambda llama al **SageMaker endpoint** con el vector de features y recibe un score de 0 a 1.
5. Según el rango del score, la Lambda devuelve `aprobar`, `revisar` o `bloquear` a la app y publica el evento `decisión registrada v1` en **Kinesis Data Streams**, con el ID de la cuenta como partition key.
6. La **Lambda de features** consume el stream y recalcula los agregados de la cuenta.
7. Los agregados actualizados vuelven a DynamoDB features y se aplican a la siguiente transferencia.
8. La **Lambda de alertas** consume el mismo stream y filtra las decisiones `revisar` y `bloquear`.
9. La Lambda de alertas publica en el tema **SNS** de casos para analizar.
10. El **analista de prevención** recibe el caso mediante la suscripción al tema y decide en la consola interna.

## Rangos del score

| Rango | Decisión | Efecto |
|---|---|---|
| por debajo de 0,40 | aprobar | la transferencia continúa |
| de 0,40 a 0,85 | revisar | transferencia retenida hasta la decisión del analista, con un plazo de 30 minutos |
| por encima de 0,85 | bloquear | transferencia rechazada y cliente avisado |

## Alternativas descartadas

- Regla por lotes en Aurora: no decide antes de que salga el dinero.
- Llamar al modelo desde API Gateway con integración directa: no hay dónde leer las features y aplicar el rango.

## Fuera del alcance

El entrenamiento y la publicación de una nueva versión del modelo pertenecen al pipeline de ML, documentado por separado.
