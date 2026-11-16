#!/usr/bin/env bash
# Rebuilds the eleven templates, each through its own gate. Exits with an error if any gate fails.
# Usage: bash <skill>/templates/build-all.sh   (from any folder)
# In a clone of the repository it also writes docs/models/gates.json with the result of each type.
set -uo pipefail
M="$(cd "$(dirname "$0")" && pwd)"
SK="$M/.."
REPORT="$SK/../../docs/models/gates.json"
results=()
failures=0
gate() {  # gate <type> <command...>: runs one step; a type fails if any of its steps fails
  local type="$1"; shift
  local out; out="$("$@" 2>&1)"; local rc=$?
  echo "$out" | tail -3
  if [ $rc -ne 0 ]; then
    echo "FAILED $type: $*"; failures=$((failures + 1)); results+=("$type=fail")
  else
    results+=("$type=pass")
  fi
}

# poster_lint.py gate (runs inside build.py): poster, step flow, ER, matrix, table and C4
gate aws-architecture python3 "$SK/scripts/build.py" "$M/01-aws-architecture/_src/01-payments-api.html"
gate step-flow python3 "$SK/scripts/build.py" "$M/02-step-flow/_src/02-event-outbox.html"
gate er-schema node "$SK/er/er-build.mjs" "$M/03-er-schema/_src/er-account.layout.mjs"
gate er-schema python3 "$SK/scripts/build.py" "$M/03-er-schema/_src/er-account.html"
gate dependency-matrix node "$SK/er/er-overview.mjs" "$M/03-er-schema/_src/model.json" "$M/04-dependency-matrix/_src/er-overview.html"
gate dependency-matrix python3 "$SK/scripts/build.py" "$M/04-dependency-matrix/_src/er-overview.html"
gate comparison-table python3 "$SK/scripts/build.py" "$M/05-comparison-table/_src/05-messaging-comparison.html"
gate c4 python3 "$SK/scripts/build_c4.py" "$M/11-c4/_src/11-c4-pix.json"

# conceptual.py gate: swimlanes and cards
gate swimlanes python3 "$SK/scripts/build_swimlanes.py" "$M/06-swimlanes/_src/06-account-opening.json"
gate swimlanes python3 "$SK/scripts/conceptual.py" "$M/06-swimlanes/_src/06-account-opening.html"
gate card-catalog python3 "$SK/scripts/conceptual.py" "$M/07-card-catalog/_src/07-api-catalog.html"

# conceptual.py gate: sequence
gate sequence python3 "$SK/scripts/build_sequence.py" "$M/09-sequence/_src/09-pix-outbound.json"
gate sequence python3 "$SK/scripts/conceptual.py" "$M/09-sequence/_src/09-pix-outbound.html"

# build_states.py gate (reachability, initial, final) and conceptual.py: state machine
gate state-machine python3 "$SK/scripts/build_states.py" "$M/10-state-machine/_src/10-pix-states.json"
gate state-machine python3 "$SK/scripts/conceptual.py" "$M/10-state-machine/_src/10-pix-states.html"

# build_bpmn.py gate: structure, reachability, overlap and import into bpmn-js
gate bpmn python3 "$SK/bpmn/build_bpmn.py" "$M/08-bpmn/_src/08-payment-dispute.json"

# Final re-read of the geometric lint on the poster sources
gate poster-lint python3 "$SK/scripts/poster_lint.py" "$M"/0[1-5]-*/_src/*.html "$M"/11-*/_src/*.html

# Theme: themes/ai-diagrams.json matches the base CSS :root and the generators
gate theme python3 "$SK/scripts/check_theme.py"

if [ -d "$(dirname "$REPORT")" ]; then
  python3 - "$REPORT" "${results[@]}" <<'PY'
import datetime, json, platform, sys
report, *pairs = sys.argv[1:]
types = {}
for pair in pairs:
    t, r = pair.split('=')
    types[t] = 'fail' if r == 'fail' or types.get(t) == 'fail' else 'pass'
json.dump({'_doc': 'Written by skills/ai-diagrams/templates/build-all.sh: the gate result of each template on this run.',
           'date': datetime.date.today().isoformat(), 'platform': platform.system().lower(), 'types': types},
          open(report, 'w'), indent=2)
open(report, 'a').write('\n')
PY
fi
[ $failures -eq 0 ] && echo "total: 0" || { echo "total: $failures"; exit 1; }
