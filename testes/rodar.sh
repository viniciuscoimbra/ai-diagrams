#!/usr/bin/env bash
# Casos negativos: cada fonte tem um defeito plantado e precisa reprovar no gate pelo motivo certo.
# Uso: bash testes/rodar.sh   (de qualquer pasta). Sai com erro se algum caso passar.
set -uo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
SK="$T/../skills/prosa"
N="$T/negativos"
falhas=0
espera() {  # espera <motivo> <comando...>
  local motivo="$1"; shift
  local saida; saida="$("$@" 2>&1)"; local rc=$?
  if [ $rc -ne 0 ] && echo "$saida" | grep -q "$motivo"; then
    echo "ok     reprovou com $motivo: ${*: -1}"
  else
    echo "FALHOU esperava $motivo: ${*: -1}"; echo "$saida" | tail -5; falhas=$((falhas + 1))
  fi
}
espera TRANSBORDA      python3 "$SK/scripts/poster_lint.py" "$N/transborda.html"
espera TEXTO-MARKETING python3 "$SK/scripts/poster_lint.py" --static "$N/marketing.html"
espera COLINEAR        python3 "$SK/scripts/conceitual.py" --so-lint "$N/colinear-conceitual.html"
espera TEXTO-SOBRE-VIDA python3 "$SK/scripts/conceitual.py" --so-lint "$N/texto-sobre-vida-conceitual.html"
espera DENTRO-DA-CAIXA python3 "$SK/scripts/poster_lint.py" "$N/dentro-e-borda.html"
espera TEXTO-SOBRE-BORDA python3 "$SK/scripts/poster_lint.py" "$N/dentro-e-borda.html"
espera CORTADO         python3 "$SK/scripts/build.py" "$SK/modelos/01-arquitetura-aws/_src/01-api-pagamentos.html" 400 --out "$(mktemp -d)"

# --fix: um badge deslocado 18px da seta reprova, o --fix o leva de volta, e o lint zera
D="$(mktemp -d)"; mkdir -p "$D/_src"
sed 's#left:355px;top:212px">3#left:355px;top:230px">3#' "$SK/modelos/01-arquitetura-aws/_src/01-api-pagamentos.html" > "$D/_src/badge.html"
espera BADGE-SOLTO python3 "$SK/scripts/poster_lint.py" "$D/_src/badge.html"
python3 "$SK/scripts/poster_lint.py" --fix "$D/_src/badge.html" > /dev/null
if python3 "$SK/scripts/poster_lint.py" "$D/_src/badge.html" > /dev/null; then
  echo "ok     --fix levou o badge para a seta: $D/_src/badge.html"
else
  echo "FALHOU --fix não corrigiu o badge: $D/_src/badge.html"; falhas=$((falhas + 1))
fi
[ $falhas -eq 0 ] && echo "total: 0" || { echo "total: $falhas"; exit 1; }
