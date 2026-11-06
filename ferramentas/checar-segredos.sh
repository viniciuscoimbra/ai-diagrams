#!/usr/bin/env bash
# Reprova se algum arquivo versionado ou preparado para commit tiver cara de credencial.
# Uso: bash ferramentas/checar-segredos.sh   (rode antes de todo commit)
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
cd "$R"
PADRAO='AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ATATT[0-9A-Za-z_-]{10,}|ATBB[0-9A-Za-z]{10,}|ghp_[0-9A-Za-z]{20,}|github_pat_|sk-ant-|sk-[A-Za-z0-9]{32,}|xox[abp]-|aws_secret_access_key|https://[^/ ]+:[^@ ]+@'
achados=$(git ls-files -c -o --exclude-standard | grep -v -E '\.png$|bpmn/vendor/|ferramentas/checar-segredos.sh' | xargs grep -n -I -E "$PADRAO" 2>/dev/null)
arquivos=$(git ls-files -c -o --exclude-standard | grep -i -E '(^|/)(\.env|.*\.pem|.*\.key|.*\.p12|id_rsa.*|id_ed25519.*|credentials.*)$')
if [ -n "$achados$arquivos" ]; then
  echo "SEGREDO ENCONTRADO: tire do repositório antes do commit."
  [ -n "$achados" ] && echo "$achados" | cut -c1-160
  [ -n "$arquivos" ] && echo "$arquivos"
  exit 1
fi
echo "nenhuma credencial encontrada"
