#!/usr/bin/env bash
# Regenera os nove exemplos a partir dos fontes em resultado/_src/, cada um pelo próprio gate.
# Uso: bash exemplos/gerar.sh   (de qualquer pasta). Sai com erro no primeiro problema.
set -euo pipefail
E="$(cd "$(dirname "$0")" && pwd)"
SK="$E/../skills/prosa"

python3 "$SK/scripts/build.py" "$E/arquitetura-aws/resultado/_src/antifraude-transferencias.html"
python3 "$SK/scripts/build.py" "$E/fluxo-passos/resultado/_src/conciliacao-pagamentos.html"
python3 "$SK/scripts/build.py" "$E/tabela-comparacao/resultado/_src/comparacao-extrato.html"
node "$SK/der/der-montar.mjs" "$E/der-schema/resultado/_src/der-cobranca.layout.mjs"
python3 "$SK/scripts/build.py" "$E/der-schema/resultado/_src/der-cobranca.html"
node "$SK/der/der-visao-geral.mjs" "$E/matriz-dependencia/resultado/_src/modelo.json" "$E/matriz-dependencia/resultado/_src/der-visao-geral.html"
python3 "$SK/scripts/build.py" "$E/matriz-dependencia/resultado/_src/der-visao-geral.html"
python3 "$SK/scripts/gerar_raias.py" "$E/raias/resultado/_src/aumento-de-limite.json"
python3 "$SK/scripts/conceitual.py" "$E/raias/resultado/_src/aumento-de-limite.html" | tail -3
python3 "$SK/scripts/conceitual.py" "$E/catalogo-cards/resultado/_src/catalogo-eventos.html" | tail -3
python3 "$SK/scripts/gerar_sequencia.py" "$E/sequencia/resultado/_src/autorizacao-compra.json"
python3 "$SK/scripts/conceitual.py" "$E/sequencia/resultado/_src/autorizacao-compra.html" | tail -3
python3 "$SK/bpmn/gerar_bpmn.py" "$E/bpmn/resultado/_src/recuperacao-acesso.json"
echo "exemplos: total: 0"
