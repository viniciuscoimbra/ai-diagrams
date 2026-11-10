#!/usr/bin/env bash
# Fails if a tracked or staged file looks like a credential.
# Usage: bash tools/check-secrets.sh   (run before every commit)
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
cd "$R"
PADRAO='AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ATATT[0-9A-Za-z_-]{10,}|ATBB[0-9A-Za-z]{10,}|ghp_[0-9A-Za-z]{20,}|github_pat_|sk-ant-|sk-[A-Za-z0-9]{32,}|xox[abp]-|aws_secret_access_key|https://[^/ ]+:[^@ ]+@'
found=$(git ls-files -c -o --exclude-standard | grep -v -E '\.png$|bpmn/vendor/|tools/check-secrets.sh' | xargs grep -n -I -E "$PADRAO" 2>/dev/null)
files=$(git ls-files -c -o --exclude-standard | grep -i -E '(^|/)(\.env|.*\.pem|.*\.key|.*\.p12|id_rsa.*|id_ed25519.*|credentials.*)$')
if [ -n "$found$files" ]; then
  echo "SECRET FOUND: remove it from the repository before committing."
  [ -n "$found" ] && echo "$found" | cut -c1-160
  [ -n "$files" ] && echo "$files"
  exit 1
fi
echo "no credential found"
