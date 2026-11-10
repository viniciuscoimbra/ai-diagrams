# Decision: real-time fraud prevention for transfers

Status: approved · 2026-10

## Context

Every transfer initiated in the app goes through a risk decision before leaving the account. The current rule runs in batches every 15 minutes and only catches fraud after the money has left. The decision must happen within the transfer request, with a 300 ms budget at p99.

Measured volume: 1.8 million transfers per day, peaking at 120 per second at lunchtime.

## Decision

1. The app calls `POST /transferencias` on **API Gateway**, with the session token.
2. API Gateway invokes the **Decision Lambda** synchronously.
3. The Lambda reads account and recipient features from **DynamoDB features** (average amount over the last 30 days, number of new recipients in 24 hours, age of the destination key).
4. The Lambda calls the **SageMaker endpoint** with the feature vector and receives a score from 0 to 1.
5. Depending on the score band, the Lambda returns `approve`, `review` or `block` to the app and publishes the `decision recorded v1` event to **Kinesis Data Streams**, using the account ID as the partition key.
6. The **Features Lambda** consumes the stream and recalculates account aggregates.
7. Updated aggregates return to DynamoDB features and apply to the next transfer.
8. The **Alert Lambda** consumes the same stream and filters `review` and `block` decisions.
9. The Alert Lambda publishes to the **SNS** topic for review cases.
10. The **fraud analyst** receives the case through the topic subscription and decides in the internal console.

## Score bands

| Band | Decision | Effect |
|---|---|---|
| below 0.40 | approve | transfer proceeds |
| 0.40 to 0.85 | review | transfer held until the analyst decides, with a 30-minute deadline |
| above 0.85 | block | transfer declined and customer notified |

## Rejected alternatives

- Batch rule in Aurora: does not decide before the money leaves.
- Calling the model directly from API Gateway: no place to read features and apply the score band.

## Out of scope

Training and publishing a new model version belong to the ML pipeline, documented separately.
