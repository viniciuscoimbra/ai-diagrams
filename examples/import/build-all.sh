#!/usr/bin/env bash
# Without --source-only this runs the normal Chrome gates and writes PNGs.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != '--source-only' ]; }; then
  echo 'usage: bash examples/import/build-all.sh [--source-only]' >&2
  exit 1
fi
python3 -m unittest discover -s "$ROOT/tests" -p 'test_import*.py'
for language in en es pt-BR; do
  for input in flowchart.mmd swimlanes.mmd sequence.mmd state.mmd er.mmd process.bpmn schema.sql catalog.csv comparison.yaml workspace.dsl; do
    python3 "$ROOT/skills/ai-diagrams/scripts/import_cli.py" "$HERE/$language/$input" --out "$HERE/$language/output/${input%.*}" --lang "$language" "$@"
  done
  python3 "$ROOT/skills/ai-diagrams/scripts/import_cli.py" "$HERE/$language/schema.sql" --type matrix --out "$HERE/$language/output/schema-matrix" --lang "$language" "$@"
done
python3 - "$HERE" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
entries = []
for language in ('en', 'es', 'pt-BR'):
    for name in ('flowchart', 'swimlanes', 'sequence', 'state', 'er', 'process', 'schema', 'catalog', 'comparison', 'workspace', 'schema-matrix'):
        folder = root / language / 'output' / name
        report = json.loads((folder / (('schema' if name == 'schema-matrix' else name) + '.import.json')).read_text())
        # report paths are relative to the report's folder
        output = (folder / report['sources'][0]).resolve()
        entries.append({'id': name, 'language': language, 'input': (folder / report['input']).resolve().relative_to(root).as_posix(),
                        'output': output.relative_to(root).as_posix(), 'type': report['type'], 'tested': True, 'gate': report['gate']})
(root / 'manifest.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print('total: 0; ' + str(len(entries)) + ' imports; gate: ' + entries[0]['gate'])
PY
