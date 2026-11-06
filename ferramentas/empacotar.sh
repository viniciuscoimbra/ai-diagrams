#!/usr/bin/env bash
# Monta os pacotes de upload em dist/:
#   ai-diagrams-skill.zip  skill para enviar no Claude.ai (pasta com SKILL.md na raiz do zip)
#   ai-diagrams-kb.zip     knowledge base para Projeto do Claude ou do ChatGPT, Custom GPT ou Bedrock
# Uso: bash ferramentas/empacotar.sh   (de qualquer pasta)
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
SK="$R/skills/ai-diagrams"
D="$R/dist"
rm -rf "$D" && mkdir -p "$D/skill" "$D/kb"

# 1. Skill para o Claude.ai: description de no máximo 200 caracteres.
cp -R "$SK" "$D/skill/ai-diagrams"
python3 - "$D/skill/ai-diagrams/SKILL.md" <<'PY'
import re, sys
p = sys.argv[1]; t = open(p).read()
curta = ('Diagramas técnicos com gate: poster AWS, C4, fluxo, raias, sequência, estados, '
         'BPMN, tabela, cards, DER e matriz. Use ao pedir diagrama, fluxo, '
         'processo, comparação ou modelo de dados.')
assert len(curta) <= 200, len(curta)
t = re.sub(r'^description: .*$', 'description: ' + curta, t, count=1, flags=re.M)
open(p, 'w').write(t)
PY
(cd "$D/skill" && zip -qr "$D/ai-diagrams-skill.zip" ai-diagrams)

# 2. Knowledge base: só texto e fontes, sem o bundle do bpmn-js e sem PNG.
cp "$R/kb/INSTRUCOES.md" "$D/kb/00-INSTRUCOES.md"
cp "$SK/SKILL.md" "$D/kb/01-roteador-SKILL.md"
n=2
for f in linguagem-visual tabela raias bpmn der sequencia estados c4; do
  cp "$SK/references/$f.md" "$D/kb/$(printf '%02d' $n)-ref-$f.md"; n=$((n+1))
done
cp "$SK/assets/estilo.css" "$D/kb/10-estilo.css"
cp "$SK/assets/estilo-conceitual.css" "$D/kb/11-estilo-conceitual.css"
cp "$SK/assets/template-poster.html" "$D/kb/12-template-poster.html"
cp "$SK/modelos/01-arquitetura-aws/_src/"*.html "$D/kb/20-modelo-poster-aws.html"
cp "$SK/modelos/02-fluxo-passos/_src/"*.html "$D/kb/21-modelo-fluxo-passos.html"
cp "$SK/modelos/03-der-schema/_src/modelo.json" "$D/kb/22-modelo-der-modelo.json"
cp "$SK/modelos/03-der-schema/_src/der-conta.layout.mjs" "$D/kb/23-modelo-der-layout.mjs"
cp "$SK/modelos/05-tabela-comparacao/_src/"*.html "$D/kb/24-modelo-tabela.html"
cp "$SK/modelos/06-raias/_src/"*.json "$D/kb/25-modelo-raias.json"
cp "$SK/modelos/07-catalogo-cards/_src/"*.html "$D/kb/26-modelo-cards.html"
cp "$SK/modelos/08-bpmn/_src/"*.json "$D/kb/27-modelo-bpmn.json"
cp "$SK/modelos/09-sequencia/_src/"*.json "$D/kb/28-modelo-sequencia.json"
cp "$SK/modelos/10-maquina-estados/_src/"*.json "$D/kb/29-modelo-estados.json"
cp "$SK/modelos/11-c4/_src/"*.html "$D/kb/30-modelo-c4.html"
(cd "$D/kb" && zip -qr "$D/ai-diagrams-kb.zip" .)

ls -la "$D"/*.zip
echo "arquivos na KB: $(ls "$D/kb" | wc -l | tr -d ' ')"
