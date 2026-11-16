#!/usr/bin/env bash
# Negative cases: each source has a planted defect and must fail the gate for the right reason.
# Usage: bash tests/run.sh   (from any folder). Exits with an error if any case passes.
set -uo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
SK="$T/../skills/ai-diagrams"
N="$T/negative"
failures=0
expect() {  # expect <reason> <command...>
  local reason="$1"; shift
  local out; out="$("$@" 2>&1)"; local rc=$?
  if [ $rc -ne 0 ] && echo "$out" | grep -q -- "$reason"; then
    echo "ok     failed with $reason: ${*: -1}"
  else
    echo "FAILED expected $reason: ${*: -1}"; echo "$out" | tail -5; failures=$((failures + 1))
  fi
}
check() {  # check <description> <command...>: the command must exit 0
  local what="$1"; shift
  local out; out="$("$@" 2>&1)"
  if [ $? -eq 0 ]; then echo "ok     $what"; else echo "FAILED $what"; echo "$out" | tail -5; failures=$((failures + 1)); fi
}
expect OVERFLOW         python3 "$SK/scripts/poster_lint.py" "$N/overflow.html"
expect MARKETING-COPY   python3 "$SK/scripts/poster_lint.py" --static "$N/marketing.html"
expect COLLINEAR        python3 "$SK/scripts/conceptual.py" --lint-only "$N/collinear-conceptual.html"
expect TEXT-OVER-LIFELINE python3 "$SK/scripts/conceptual.py" --lint-only "$N/text-over-lifeline-conceptual.html"
expect NO-INITIAL       python3 "$SK/scripts/build_states.py" "$N/states-no-initial.json"
expect UNKNOWN          python3 "$SK/scripts/build_states.py" "$N/states-unknown.json"
expect NO-EVENT         python3 "$SK/scripts/build_states.py" "$N/states-no-event.json"
expect LEAVES-FINAL     python3 "$SK/scripts/build_states.py" "$N/states-leaves-final.json"
expect UNREACHABLE      python3 "$SK/scripts/build_states.py" "$N/states-unreachable.json"
expect NO-EXIT          python3 "$SK/scripts/build_states.py" "$N/states-no-exit.json"
expect C4-NO-LEGEND     python3 "$SK/scripts/poster_lint.py" --static "$N/c4-no-legend.html"
expect C4-NO-TYPE       python3 "$SK/scripts/poster_lint.py" --static "$N/c4-no-type.html"
expect ARROWHEAD-INSIDE python3 "$SK/scripts/poster_lint.py" "$N/c4-arrows.html"
expect ARROW-ON-EDGE    python3 "$SK/scripts/poster_lint.py" "$N/c4-arrows.html"
expect LABEL-DETACHED   python3 "$SK/scripts/poster_lint.py" "$N/c4-arrows.html"
expect INSIDE-BOX       python3 "$SK/scripts/poster_lint.py" "$N/inside-and-edge.html"
expect TEXT-OVER-EDGE   python3 "$SK/scripts/poster_lint.py" "$N/inside-and-edge.html"
expect CROPPED          python3 "$SK/scripts/build.py" "$SK/templates/01-aws-architecture/_src/01-payments-api.html" 400 --out "$(mktemp -d)"

# without the /*STYLE*/ marker, build and conceptual stop before Chrome
D0="$(mktemp -d)"; mkdir -p "$D0/_src"
sed 's#/\*STYLE\*/##' "$SK/templates/11-c4/_src/11-c4-pix.html" > "$D0/_src/no-style.html"
expect NO-STYLE python3 "$SK/scripts/build.py" "$D0/_src/no-style.html"
sed 's#/\*STYLE\*/##' "$SK/templates/07-card-catalog/_src/07-api-catalog.html" > "$D0/_src/no-style-cards.html"
expect NO-STYLE python3 "$SK/scripts/conceptual.py" "$D0/_src/no-style-cards.html"

# a literal color in the source fails in the three gates; a theme that differs from the CSS fails the check
DC="$(mktemp -d)"; mkdir -p "$DC/_src"
sed 's#/\*STYLE\*/#/*STYLE*/ .nota{color:\#14B8A6}#' "$SK/templates/05-comparison-table/_src/05-messaging-comparison.html" > "$DC/_src/color.html"
expect COLOR-OUTSIDE-THEME python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/color.html"
sed 's#/\*STYLE\*/#/*STYLE*/ .nota{background:linear-gradient(\#F3F4F6 0,transparent 1px)}#' "$SK/templates/05-comparison-table/_src/05-messaging-comparison.html" > "$DC/_src/color-gradient.html"
expect COLOR-OUTSIDE-THEME python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/color-gradient.html"
sed 's#/\*STYLE\*/#/*STYLE*/ .card{border-color:rgba(55,65,81,.4)}#' "$SK/templates/07-card-catalog/_src/07-api-catalog.html" > "$DC/_src/color-cards.html"
expect COLOR-OUTSIDE-THEME python3 "$SK/scripts/conceptual.py" --lint-only "$DC/_src/color-cards.html"
python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); m["nodes"][0]["fill"]="#FEF08A"; json.dump(m,open(sys.argv[2],"w"))' \
  "$SK/templates/08-bpmn/_src/08-payment-dispute.json" "$DC/_src/color-bpmn.json"
expect COLOR-OUTSIDE-THEME python3 "$SK/bpmn/build_bpmn.py" "$DC/_src/color-bpmn.json" --bpmn-only
sed 's/"#14B8A6"/"#14B8A7"/' "$SK/themes/ai-diagrams.json" > "$DC/theme.json"
expect TOKEN-MISMATCH python3 "$SK/scripts/check_theme.py" "$DC/theme.json"
check "themes/ai-diagrams.json matches the base CSS and the generators" python3 "$SK/scripts/check_theme.py"

# theme from a file: --theme paper replaces the :root and the fonts in the final HTML; an incomplete theme fails before Chrome
DT="$(mktemp -d)"; mkdir -p "$DT/_src"
cp "$SK/templates/05-comparison-table/_src/05-messaging-comparison.html" "$DT/_src/"
if python3 "$SK/scripts/build.py" "$DT/_src/05-messaging-comparison.html" --theme paper > "$DT/build.log" 2>&1 \
   && python3 - "$DT/05-messaging-comparison.html" "$SK/themes/paper.json" <<'PY_THEME'
import json, re, sys
html, theme = open(sys.argv[1]).read(), json.load(open(sys.argv[2]))
roots = [r for r in re.findall(r':root\{(.*?)\}', html, re.S) if '--ink:' in r]
assert len(roots) == 1, 'expected one token :root, found %d' % len(roots)
tok = dict(re.findall(r'--([\w-]+):([^;]+);', roots[0]))
for k, v in list(theme['colors'].items()) + list(theme['derived'].items()):
    assert tok[k.replace('_', '-')].upper() == v.upper(), (k, tok.get(k.replace('_', '-')), v)
assert tok['font-text'].startswith("'Public Sans'") and tok['font-mono'].startswith("'Source Code Pro'"), tok
assert 'family=Public+Sans' in html and 'IBM+Plex' not in html, 'the Google Fonts link is not the theme link'
PY_THEME
then
  echo "ok     --theme paper: the :root and the link of the final HTML carry the values of themes/paper.json"
else
  echo "FAILED --theme paper did not reach the final HTML: $DT"; tail -5 "$DT/build.log"; failures=$((failures + 1))
fi
cp "$SK/templates/06-swimlanes/_src/06-account-opening.json" "$DT/_src/"
AI_DIAGRAMS_THEME=paper python3 "$SK/scripts/build_swimlanes.py" "$DT/_src/06-account-opening.json" > /dev/null
if grep -q '<meta name="theme" content="paper">' "$DT/_src/06-account-opening.html" \
   && grep -q 'family=Public+Sans' "$DT/_src/06-account-opening.html"; then
  echo "ok     AI_DIAGRAMS_THEME=paper: the generator writes the theme meta and link into the source"
else
  echo "FAILED AI_DIAGRAMS_THEME did not reach the generated source: $DT/_src/06-account-opening.html"; failures=$((failures + 1))
fi
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); del t["colors"]["accent"]; json.dump(t,open(sys.argv[2],"w"))' \
  "$SK/themes/paper.json" "$DT/incomplete.json"
expect "THEME-INCOMPLETE: missing colors.accent" python3 "$SK/scripts/build.py" "$DT/_src/05-messaging-comparison.html" --theme "$DT/incomplete.json"
expect "THEME-INCOMPLETE: missing colors.accent" node "$SK/er/er-build.mjs" "$SK/templates/03-er-schema/_src/er-account.layout.mjs" --theme "$DT/incomplete.json"
expect THEME-NOT-FOUND python3 "$SK/bpmn/build_bpmn.py" "$SK/templates/08-bpmn/_src/08-payment-dispute.json" --theme does-not-exist
sed "s#/\*STYLE\*/#/*STYLE*/ .nota{font-family:'Inter',sans-serif}#" "$SK/templates/05-comparison-table/_src/05-messaging-comparison.html" > "$DC/_src/font.html"
expect FONT-OUTSIDE-THEME python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/font.html"

# 0.1.x names keep working until 0.3.0, with a warning on stderr
python3 - "$SK/themes/paper.json" "$DT/v1.json" "$SK/scripts" <<'PY_V1'
import json, sys
sys.path.insert(0, sys.argv[3])
import theme
t = json.load(open(sys.argv[1]))
back = {v: k for k, v in theme.V1_CHAVES.items()}
groups = {v: k for k, v in theme.V1_GRUPOS.items()}
v1 = {'versao_schema': 1, 'nome': t['name'], 'empresa': t['company'], 'logo': t['logo']}
for g, k in groups.items():
    v1[k] = {back.get(n, n): v for n, v in t[g].items()}
json.dump(v1, open(sys.argv[2], 'w'))
PY_V1
check "a schema_version 1 theme gives the same CSS as its v2 file" bash -c \
  '[ "$(python3 "$1/scripts/theme.py" --theme "$2" --css | tail -n +3)" = "$(python3 "$1/scripts/theme.py" --theme paper --css | tail -n +3)" ]' _ "$SK" "$DT/v1.json"
check "--tema warns that it is deprecated" bash -c 'python3 "$1/scripts/theme.py" --tema papel --link 2>&1 >/dev/null | grep -q -- "--tema is deprecated; use --theme"' _ "$SK"
check "--tema papel still resolves to themes/paper.json" bash -c 'python3 "$1/scripts/theme.py" --tema papel --link 2>/dev/null | grep -q Public+Sans' _ "$SK"
D1="$(mktemp -d)"; mkdir -p "$D1/_src"
python3 - "$SK/templates/06-swimlanes/_src/06-account-opening.json" "$D1/_src/old-keys.json" "$SK/scripts" <<'PY_SPEC'
import json, sys
sys.path.insert(0, sys.argv[3])
import spec
json.dump(spec.ler('swimlanes', json.load(open(sys.argv[1]))), open(sys.argv[2], 'w'), ensure_ascii=False)
PY_SPEC
cp "$SK/templates/06-swimlanes/_src/06-account-opening.json" "$D1/_src/new-keys.json"
python3 "$SK/scripts/build_swimlanes.py" "$D1/_src/old-keys.json" > /dev/null 2>&1
python3 "$SK/scripts/build_swimlanes.py" "$D1/_src/new-keys.json" > /dev/null 2>&1
check "a swimlanes spec with the 0.1.x keys builds the same source as the English one" cmp -s "$D1/_src/old-keys.html" "$D1/_src/new-keys.html"

# --fix: a badge moved 18px off its arrow fails, --fix brings it back, and the lint reaches zero
D="$(mktemp -d)"; mkdir -p "$D/_src"
sed 's#left:355px;top:212px">3#left:355px;top:230px">3#' "$SK/templates/01-aws-architecture/_src/01-payments-api.html" > "$D/_src/badge.html"
expect BADGE-DETACHED python3 "$SK/scripts/poster_lint.py" "$D/_src/badge.html"
python3 "$SK/scripts/poster_lint.py" --fix "$D/_src/badge.html" > /dev/null
if python3 "$SK/scripts/poster_lint.py" "$D/_src/badge.html" > /dev/null; then
  echo "ok     --fix moved the badge onto the arrow: $D/_src/badge.html"
else
  echo "FAILED --fix did not fix the badge: $D/_src/badge.html"; failures=$((failures + 1))
fi
check "engine labels: language precedence, catalogs and generators" python3 -m unittest discover -s "$SK/i18n" -p 'test_*.py'
check "ER generators: language, theme and byte-for-byte geometry" node "$SK/er/lang.test.mjs"
if python3 -m unittest discover -s "$T" -p 'test_import*.py'; then
  echo "ok     importers: formats, native models and errors"
else
  failures=$((failures + 1))
fi
[ $failures -eq 0 ] && echo "total: 0" || { echo "total: $failures"; exit 1; }
