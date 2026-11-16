#!/usr/bin/env bash
# Rebuilds the eleven examples from the sources in output/_src/, each through its own gate.
# Usage: bash examples/build-all.sh   (from any folder). Exits with an error at the first problem.
set -euo pipefail
E="$(cd "$(dirname "$0")" && pwd)"
SK="$E/../skills/ai-diagrams"

python3 "$SK/scripts/build.py" "$E/aws-architecture/output/_src/transfer-antifraud.html"
python3 "$SK/scripts/build.py" "$E/step-flow/output/_src/payment-reconciliation.html"
python3 "$SK/scripts/build.py" "$E/comparison-table/output/_src/statement-comparison.html"
python3 "$SK/scripts/build_c4.py" "$E/c4/output/_src/billing-c4.json"
node "$SK/er/er-build.mjs" "$E/er-schema/output/_src/er-billing.layout.mjs"
python3 "$SK/scripts/build.py" "$E/er-schema/output/_src/er-billing.html"
node "$SK/er/er-overview.mjs" "$E/dependency-matrix/output/_src/model.json" "$E/dependency-matrix/output/_src/er-overview.html"
python3 "$SK/scripts/build.py" "$E/dependency-matrix/output/_src/er-overview.html"
python3 "$SK/scripts/build_swimlanes.py" "$E/swimlanes/output/_src/limit-increase.json"
python3 "$SK/scripts/conceptual.py" "$E/swimlanes/output/_src/limit-increase.html" | tail -3
python3 "$SK/scripts/conceptual.py" "$E/card-catalog/output/_src/event-catalog.html" | tail -3
python3 "$SK/scripts/build_sequence.py" "$E/sequence/output/_src/purchase-authorization.json"
python3 "$SK/scripts/conceptual.py" "$E/sequence/output/_src/purchase-authorization.html" | tail -3
python3 "$SK/scripts/build_states.py" "$E/state-machine/output/_src/card-lifecycle.json"
python3 "$SK/scripts/conceptual.py" "$E/state-machine/output/_src/card-lifecycle.html" | tail -3
python3 "$SK/bpmn/build_bpmn.py" "$E/bpmn/output/_src/access-recovery.json"
echo "examples: total: 0"
