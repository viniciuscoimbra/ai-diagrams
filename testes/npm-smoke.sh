#!/usr/bin/env bash
# Instala um tarball local sem rede e sem tocar no HOME real.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ai-diagrams-npm.XXXXXX")"
trap 'rm -rf "$SMOKE_ROOT"' EXIT
mkdir -p "$SMOKE_ROOT/home" "$SMOKE_ROOT/prefix" "$SMOKE_ROOT/cache"

if [ "$#" -gt 1 ]; then
  echo "Uso: bash testes/npm-smoke.sh [pacote.tgz]" >&2
  exit 1
elif [ "$#" -eq 1 ]; then
  TARBALL="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
else
  npm pack "$R" --ignore-scripts --json --cache "$SMOKE_ROOT/cache" --pack-destination "$SMOKE_ROOT" > "$SMOKE_ROOT/pack.json"
  TARBALL="$SMOKE_ROOT/$(node -p 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))[0].filename' "$SMOKE_ROOT/pack.json")"
fi

env HOME="$SMOKE_ROOT/home" npm install --global --prefix "$SMOKE_ROOT/prefix" --cache "$SMOKE_ROOT/cache" --ignore-scripts --offline --no-audit --no-fund "$TARBALL"
env HOME="$SMOKE_ROOT/home" node "$R/testes/npm-cli.test.mjs" "$SMOKE_ROOT/prefix/bin/ai-diagrams" "$SMOKE_ROOT"
env HOME="$SMOKE_ROOT/home" python3 "$R/testes/npm-tty.py" "$(command -v node)" "$SMOKE_ROOT/prefix/bin/ai-diagrams" "$SMOKE_ROOT"
