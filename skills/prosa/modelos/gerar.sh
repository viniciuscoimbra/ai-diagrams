#!/usr/bin/env bash
# Regenera os nove modelos, cada um pelo próprio gate. Sai com erro no primeiro problema.
# Uso: bash <skill>/modelos/gerar.sh   (de qualquer pasta)
set -euo pipefail
M="$(cd "$(dirname "$0")" && pwd)"
SK="$M/.."

# Gate poster_lint.py (roda dentro do build.py): poster, fluxo, DER, matriz e tabela
python3 "$SK/scripts/build.py" "$M/01-arquitetura-aws/_src/01-api-pagamentos.html"
python3 "$SK/scripts/build.py" "$M/02-fluxo-passos/_src/02-outbox-eventos.html"
node "$SK/der/der-montar.mjs" "$M/03-der-schema/_src/der-conta.layout.mjs"
python3 "$SK/scripts/build.py" "$M/03-der-schema/_src/der-conta.html"
node "$SK/der/der-visao-geral.mjs" "$M/03-der-schema/_src/modelo.json" "$M/04-matriz-dependencia/_src/der-visao-geral.html"
python3 "$SK/scripts/build.py" "$M/04-matriz-dependencia/_src/der-visao-geral.html"
python3 "$SK/scripts/build.py" "$M/05-tabela-comparacao/_src/05-comparacao-mensageria.html"

# Gate conceitual.py: raias e cards
python3 "$SK/scripts/gerar_raias.py" "$M/06-raias/_src/06-abertura-de-conta.json"
python3 "$SK/scripts/conceitual.py" "$M/06-raias/_src/06-abertura-de-conta.html" | tail -3
python3 "$SK/scripts/conceitual.py" "$M/07-catalogo-cards/_src/07-catalogo-apis.html" | tail -3

# Gate conceitual.py: sequência
python3 "$SK/scripts/gerar_sequencia.py" "$M/09-sequencia/_src/09-pix-saida.json"
python3 "$SK/scripts/conceitual.py" "$M/09-sequencia/_src/09-pix-saida.html" | tail -3

# Gate gerar_bpmn.py: estrutura, alcance, sobreposição e importação no bpmn-js
python3 "$SK/bpmn/gerar_bpmn.py" "$M/08-bpmn/_src/08-contestacao-pagamento.json"

# Releitura final do lint geométrico nos fontes dos posters
python3 "$SK/scripts/poster_lint.py" "$M"/0[1-5]-*/_src/*.html
