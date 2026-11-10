#!/usr/bin/env bash
# Installs the skill in Kiro as a COPY (Kiro refuses to read a symlink that points outside the workspace).
# Usage: bash tools/install-kiro.sh <project-folder>   copies the skill, the steering and the agent into the project
#        bash tools/install-kiro.sh --global           copies the skill into ~/.kiro/skills
# Run it again after each git pull: the old copy is deleted and replaced.
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
  echo "agent:    $P/.kiro/agents/ai-diagrams.json"
fi

[ -L "$DEST" ] && rm "$DEST"
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
cp -RL "$SK" "$DEST"
echo "skill:    $DEST"
echo "templates: $(ls "$DEST/templates" | grep -c -E '^(0[1-9]|1[01])-') of 11"
