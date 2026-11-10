#!/usr/bin/env bash
# Builds the upload packages in dist/:
#   ai-diagrams-skill.zip  skill to upload to Claude.ai (folder with SKILL.md at the zip root)
#   ai-diagrams-kb.zip     knowledge base for a Claude or ChatGPT Project, a Custom GPT or Bedrock
# Usage: bash tools/package.sh   (from any folder)
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
SK="$R/skills/ai-diagrams"
D="$R/dist"
rm -rf "$D" && mkdir -p "$D/skill" "$D/kb"

# 1. Skill for Claude.ai: description of at most 200 characters.
cp -R "$SK" "$D/skill/ai-diagrams"
python3 - "$D/skill/ai-diagrams/SKILL.md" <<'PY'
import re, sys
p = sys.argv[1]; t = open(p).read()
short = ('Technical diagrams with a gate: AWS poster, C4, flow, swimlanes, sequence, states, '
         'BPMN, table, cards, ER and matrix. Use for any diagram, flow, '
         'process, comparison or data model.')
assert len(short) <= 200, len(short)
t = re.sub(r'^description: .*$', 'description: ' + short, t, count=1, flags=re.M)
open(p, 'w').write(t)
PY
(cd "$D/skill" && zip -qr "$D/ai-diagrams-skill.zip" ai-diagrams)

# 2. Knowledge base: text and sources only, without the bpmn-js bundle and without PNGs.
cp "$R/kb/INSTRUCTIONS.md" "$D/kb/00-INSTRUCTIONS.md"
cp "$SK/SKILL.md" "$D/kb/01-router-SKILL.md"
n=2
for f in visual-language table swimlanes bpmn er sequence states c4; do
  cp "$SK/references/$f.md" "$D/kb/$(printf '%02d' $n)-ref-$f.md"; n=$((n+1))
done
cp "$SK/assets/style.css" "$D/kb/10-style.css"
cp "$SK/assets/style-conceptual.css" "$D/kb/11-style-conceptual.css"
cp "$SK/assets/template-poster.html" "$D/kb/12-template-poster.html"
cp "$SK/templates/01-aws-architecture/_src/"*.html "$D/kb/20-template-aws-poster.html"
cp "$SK/templates/02-step-flow/_src/"*.html "$D/kb/21-template-step-flow.html"
cp "$SK/templates/03-er-schema/_src/model.json" "$D/kb/22-template-er-model.json"
cp "$SK/templates/03-er-schema/_src/er-account.layout.mjs" "$D/kb/23-template-er-layout.mjs"
cp "$SK/templates/05-comparison-table/_src/"*.html "$D/kb/24-template-table.html"
cp "$SK/templates/06-swimlanes/_src/"*.json "$D/kb/25-template-swimlanes.json"
cp "$SK/templates/07-card-catalog/_src/"*.html "$D/kb/26-template-cards.html"
cp "$SK/templates/08-bpmn/_src/"*.json "$D/kb/27-template-bpmn.json"
cp "$SK/templates/09-sequence/_src/"*.json "$D/kb/28-template-sequence.json"
cp "$SK/templates/10-state-machine/_src/"*.json "$D/kb/29-template-states.json"
cp "$SK/templates/11-c4/_src/"*.html "$D/kb/30-template-c4.html"
(cd "$D/kb" && zip -qr "$D/ai-diagrams-kb.zip" .)

ls -la "$D"/*.zip
echo "files in the KB: $(ls "$D/kb" | wc -l | tr -d ' ')"
