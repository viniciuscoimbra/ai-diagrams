#!/usr/bin/env bash
# Instala a skill no Kiro por CÓPIA (o Kiro nega leitura de symlink que aponta para fora do workspace).
# Uso: bash ferramentas/instalar-kiro.sh <pasta-do-projeto>   copia a skill, o steering e o agente para o projeto
#      bash ferramentas/instalar-kiro.sh --global              copia a skill para ~/.kiro/skills
# Rode de novo depois de cada git pull: a cópia antiga é apagada e substituída.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
SK="$R/skills/ai-diagrams"
[ $# -eq 1 ] || { sed -n '2,5p' "$0"; exit 1; }

if [ "$1" = "--global" ]; then
  DEST="$HOME/.kiro/skills/ai-diagrams"
else
  mkdir -p "$1"
  P="$(cd "$1" && pwd)"
  DEST="$P/.kiro/skills/ai-diagrams"
  mkdir -p "$P/.kiro/steering" "$P/.kiro/agents"
  cp "$R/kiro/steering/ai-diagrams.md" "$P/.kiro/steering/ai-diagrams.md"
  cp "$R/kiro/agents/ai-diagrams.json" "$P/.kiro/agents/ai-diagrams.json"
  echo "steering: $P/.kiro/steering/ai-diagrams.md"
  echo "agente:   $P/.kiro/agents/ai-diagrams.json"
fi

[ -L "$DEST" ] && rm "$DEST"
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
cp -RL "$SK" "$DEST"
echo "skill:    $DEST"
echo "modelos:  $(ls "$DEST/modelos" | grep -c -E '^(0[1-9]|1[01])-') de 11"
