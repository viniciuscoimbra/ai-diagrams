#!/usr/bin/env bash
# Installs a local tarball without network and without touching the real HOME.
# Writes docs/models/install-checks.json: every check "fail" while running, "pass" only when all of them passed.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ai-diagrams-npm.XXXXXX")"
trap 'rm -rf "$SMOKE_ROOT"' EXIT
mkdir -p "$SMOKE_ROOT/home" "$SMOKE_ROOT/prefix" "$SMOKE_ROOT/cache"

REPORT="$R/docs/models/install-checks.json"
report() {  # report <pass|fail>
  node - "$1" "$REPORT" "$R/package.json" <<'JS'
const fs = require('fs');
const [result, file, pkg] = process.argv.slice(2);
const check = (cli, id, label) => ({ cli, id, label, result });
const checks = [];
for (const cli of ['claude', 'codex']) {
  checks.push(check(cli, 'install-global', 'install --' + cli + ' links the skill in the home folder'));
  checks.push(check(cli, 'install-project', 'install --' + cli + ' --project links the skill in a project'));
  checks.push(check(cli, 'keep-existing', 'an existing installation is kept outside a terminal'));
}
checks.push(check('claude', 'replace-with-backup', 'replacement confirmed in a terminal keeps a backup'));
checks.push(check('kiro', 'install-project', 'install --kiro copies the skill, steering and agent'));
checks.push(check('kiro', 'keep-existing', 'an existing installation is kept outside a terminal'));
checks.push(check('kiro', 'rollback', 'a failed Kiro install restores every original file'));
checks.push(check(null, 'import', 'import converts a Mermaid file with --source-only'));
checks.push(check(null, 'deprecated-names', '0.1.x names (importar, --projeto, --saida) still work with a warning'));
checks.push(check(null, 'doctor', 'doctor reports Node, Python and Chrome'));
fs.writeFileSync(file, JSON.stringify({
  _doc: 'Written by tests/npm-smoke.sh. "pass" only when the whole smoke test passed on this run.',
  date: new Date().toISOString().slice(0, 10), package: JSON.parse(fs.readFileSync(pkg, 'utf8')).version,
  node: process.versions.node, platform: process.platform, checks,
}, null, 2) + '\n');
JS
}
report fail

if [ "$#" -gt 1 ]; then
  echo "Usage: bash tests/npm-smoke.sh [package.tgz]" >&2
  exit 1
elif [ "$#" -eq 1 ]; then
  TARBALL="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
else
  npm pack "$R" --ignore-scripts --json --cache "$SMOKE_ROOT/cache" --pack-destination "$SMOKE_ROOT" > "$SMOKE_ROOT/pack.json"
  TARBALL="$SMOKE_ROOT/$(node -p 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))[0].filename' "$SMOKE_ROOT/pack.json")"
fi

env HOME="$SMOKE_ROOT/home" npm install --global --prefix "$SMOKE_ROOT/prefix" --cache "$SMOKE_ROOT/cache" --ignore-scripts --offline --no-audit --no-fund "$TARBALL"
env HOME="$SMOKE_ROOT/home" node "$R/tests/npm-cli.test.mjs" "$SMOKE_ROOT/prefix/bin/ai-diagrams" "$SMOKE_ROOT"
env HOME="$SMOKE_ROOT/home" python3 "$R/tests/npm-tty.py" "$(command -v node)" "$SMOKE_ROOT/prefix/bin/ai-diagrams" "$SMOKE_ROOT"
report pass
