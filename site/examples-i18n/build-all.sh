#!/usr/bin/env bash
# Rebuilds the eleven examples in en and es with the same generators and gates as the originals.
# Run outside a sandbox: the full gates need Chrome.
# Usage: bash site/examples-i18n/build-all.sh
set -euo pipefail
E="$(cd "$(dirname "$0")" && pwd)"
SK="$E/../../skills/ai-diagrams"
for lang in en es; do
  python3 "$SK/scripts/build.py" "$E/$lang/aws-architecture/output/_src/transfer-antifraud.html"
  python3 "$SK/scripts/build.py" "$E/$lang/step-flow/output/_src/payment-reconciliation.html"
  python3 "$SK/scripts/build.py" "$E/$lang/comparison-table/output/_src/statement-comparison.html"
  python3 "$SK/scripts/build_c4.py" "$E/$lang/c4/output/_src/billing-c4.json"
  node "$SK/er/er-build.mjs" "$E/$lang/er-schema/output/_src/er-billing.layout.mjs"
  python3 "$SK/scripts/build.py" "$E/$lang/er-schema/output/_src/er-billing.html"
  node "$SK/er/er-overview.mjs" "$E/$lang/dependency-matrix/output/_src/model.json" "$E/$lang/dependency-matrix/output/_src/er-overview.html"
  python3 "$SK/scripts/build.py" "$E/$lang/dependency-matrix/output/_src/er-overview.html"
  python3 "$SK/scripts/build_swimlanes.py" "$E/$lang/swimlanes/output/_src/limit-increase.json"
  python3 "$SK/scripts/conceptual.py" "$E/$lang/swimlanes/output/_src/limit-increase.html" | tail -3
  python3 "$SK/scripts/conceptual.py" "$E/$lang/card-catalog/output/_src/event-catalog.html" | tail -3
  python3 "$SK/scripts/build_sequence.py" "$E/$lang/sequence/output/_src/purchase-authorization.json"
  python3 "$SK/scripts/conceptual.py" "$E/$lang/sequence/output/_src/purchase-authorization.html" | tail -3
  python3 "$SK/scripts/build_states.py" "$E/$lang/state-machine/output/_src/card-lifecycle.json"
  python3 "$SK/scripts/conceptual.py" "$E/$lang/state-machine/output/_src/card-lifecycle.html" | tail -3
  python3 "$SK/bpmn/build_bpmn.py" "$E/$lang/bpmn/output/_src/access-recovery.json"
done
echo "examples-i18n: en + es: total: 0"
