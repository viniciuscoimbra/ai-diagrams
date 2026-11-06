#!/usr/bin/env bash
# Without --somente-fonte this runs the normal Chrome gates and writes PNGs.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != '--somente-fonte' ]; }; then
  echo 'uso: bash exemplos/importar/gerar.sh [--somente-fonte]' >&2
  exit 1
fi
python3 -m unittest discover -s "$ROOT/testes" -p 'test_importar*.py'
for language in en es pt-BR; do
  for input in flowchart.mmd raias.mmd sequence.mmd state.mmd er.mmd process.bpmn schema.sql catalog.csv comparison.yaml; do
    python3 "$ROOT/skills/ai-diagrams/scripts/importar.py" "$HERE/$language/$input" --saida "$HERE/$language/resultado/${input%.*}" --idioma "$language" "$@"
  done
  python3 "$ROOT/skills/ai-diagrams/scripts/importar.py" "$HERE/$language/schema.sql" --tipo matriz --saida "$HERE/$language/resultado/schema-matrix" --idioma "$language" "$@"
done
python3 - "$HERE" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
entries = []
for language in ('en', 'es', 'pt-BR'):
    for name in ('flowchart', 'raias', 'sequence', 'state', 'er', 'process', 'schema', 'catalog', 'comparison', 'schema-matrix'):
        report = json.loads((root / language / 'resultado' / name / (('schema' if name == 'schema-matrix' else name) + '.importacao.json')).read_text())
        output = Path(report['sources'][0])
        entries.append({'id': name, 'language': language, 'input': str(Path(report['input']).relative_to(root)),
                        'output': str(output.relative_to(root)), 'type': report['type'], 'tested': True, 'gate': report['gate']})
(root / 'manifest.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
print('total: 0; ' + str(len(entries)) + ' importações; gate: ' + entries[0]['gate'])
PY
