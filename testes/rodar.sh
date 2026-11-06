#!/usr/bin/env bash
# Casos negativos: cada fonte tem um defeito plantado e precisa reprovar no gate pelo motivo certo.
# Uso: bash testes/rodar.sh   (de qualquer pasta). Sai com erro se algum caso passar.
set -uo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
SK="$T/../skills/ai-diagrams"
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
espera SEM-INICIAL      python3 "$SK/scripts/gerar_estados.py" "$N/estados-sem-inicial.json"
espera DESCONHECIDO     python3 "$SK/scripts/gerar_estados.py" "$N/estados-desconhecido.json"
espera SEM-EVENTO       python3 "$SK/scripts/gerar_estados.py" "$N/estados-sem-evento.json"
espera SAI-DO-FINAL     python3 "$SK/scripts/gerar_estados.py" "$N/estados-sai-do-final.json"
espera INALCANCAVEL     python3 "$SK/scripts/gerar_estados.py" "$N/estados-inalcancavel.json"
espera SEM-SAIDA        python3 "$SK/scripts/gerar_estados.py" "$N/estados-sem-saida.json"
espera C4-SEM-LEGENDA   python3 "$SK/scripts/poster_lint.py" --static "$N/c4-sem-legenda.html"
espera C4-SEM-TIPO      python3 "$SK/scripts/poster_lint.py" --static "$N/c4-sem-tipo.html"
espera PONTA-DENTRO    python3 "$SK/scripts/poster_lint.py" "$N/c4-setas.html"
espera SETA-NA-BORDA   python3 "$SK/scripts/poster_lint.py" "$N/c4-setas.html"
espera ROTULO-SOLTO    python3 "$SK/scripts/poster_lint.py" "$N/c4-setas.html"
espera DENTRO-DA-CAIXA python3 "$SK/scripts/poster_lint.py" "$N/dentro-e-borda.html"
espera TEXTO-SOBRE-BORDA python3 "$SK/scripts/poster_lint.py" "$N/dentro-e-borda.html"
espera CORTADO         python3 "$SK/scripts/build.py" "$SK/modelos/01-arquitetura-aws/_src/01-api-pagamentos.html" 400 --out "$(mktemp -d)"

# sem o marcador /*ESTILO*/ o build e o conceitual param antes do Chrome
D0="$(mktemp -d)"; mkdir -p "$D0/_src"
sed 's#/\*ESTILO\*/##' "$SK/modelos/11-c4/_src/11-c4-pix.html" > "$D0/_src/sem-estilo.html"
espera SEM-ESTILO python3 "$SK/scripts/build.py" "$D0/_src/sem-estilo.html"
sed 's#/\*ESTILO\*/##' "$SK/modelos/07-catalogo-cards/_src/07-catalogo-apis.html" > "$D0/_src/sem-estilo-cards.html"
espera SEM-ESTILO python3 "$SK/scripts/conceitual.py" "$D0/_src/sem-estilo-cards.html"

# cor literal no fonte reprova nos três gates; o tema diverge do CSS reprova na conferência
DC="$(mktemp -d)"; mkdir -p "$DC/_src"
sed 's#/\*ESTILO\*/#/*ESTILO*/ .nota{color:\#14B8A6}#' "$SK/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html" > "$DC/_src/cor.html"
espera COR-FORA-DO-TEMA python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/cor.html"
sed 's#/\*ESTILO\*/#/*ESTILO*/ .nota{background:linear-gradient(\#F3F4F6 0,transparent 1px)}#' "$SK/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html" > "$DC/_src/cor-gradiente.html"
espera COR-FORA-DO-TEMA python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/cor-gradiente.html"
sed 's#/\*ESTILO\*/#/*ESTILO*/ .card{border-color:rgba(55,65,81,.4)}#' "$SK/modelos/07-catalogo-cards/_src/07-catalogo-apis.html" > "$DC/_src/cor-cards.html"
espera COR-FORA-DO-TEMA python3 "$SK/scripts/conceitual.py" --so-lint "$DC/_src/cor-cards.html"
python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); m["nodes"][0]["fill"]="#FEF08A"; json.dump(m,open(sys.argv[2],"w"))' \
  "$SK/modelos/08-bpmn/_src/08-contestacao-pagamento.json" "$DC/_src/cor-bpmn.json"
espera COR-FORA-DO-TEMA python3 "$SK/bpmn/gerar_bpmn.py" "$DC/_src/cor-bpmn.json" --so-bpmn
sed 's/"#14B8A6"/"#14B8A7"/' "$SK/temas/ai-diagrams.json" > "$DC/tema.json"
espera TOKEN-DIVERGE python3 "$SK/scripts/conferir_tema.py" "$DC/tema.json"
if python3 "$SK/scripts/conferir_tema.py" > /dev/null; then
  echo "ok     temas/ai-diagrams.json confere com o CSS base e os geradores"
else
  echo "FALHOU temas/ai-diagrams.json diverge do pipeline"; python3 "$SK/scripts/conferir_tema.py" | tail -5; falhas=$((falhas + 1))
fi

# tema por arquivo: --tema papel troca o :root e as fontes no HTML final; tema incompleto reprova antes do Chrome
DT="$(mktemp -d)"; mkdir -p "$DT/_src"
cp "$SK/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html" "$DT/_src/"
if python3 "$SK/scripts/build.py" "$DT/_src/05-comparacao-mensageria.html" --tema papel > "$DT/build.log" 2>&1 \
   && python3 - "$DT/05-comparacao-mensageria.html" "$SK/temas/papel.json" <<'PY_TEMA'
import json, re, sys
html, tema = open(sys.argv[1]).read(), json.load(open(sys.argv[2]))
roots = [r for r in re.findall(r':root\{(.*?)\}', html, re.S) if '--tinta' in r]
assert len(roots) == 1, 'esperava um só :root de tokens, achou %d' % len(roots)
tok = dict(re.findall(r'--([\w-]+):([^;]+);', roots[0]))
for k, v in list(tema['cores'].items()) + list(tema['cores_derivadas'].items()):
    assert tok[k.replace('_', '-')].upper() == v.upper(), (k, tok.get(k.replace('_', '-')), v)
assert tok['fonte-texto'].startswith("'Public Sans'") and tok['fonte-mono'].startswith("'Source Code Pro'"), tok
assert 'family=Public+Sans' in html and 'IBM+Plex' not in html, 'link do Google Fonts não é o do tema'
PY_TEMA
then
  echo "ok     --tema papel: o :root e o link do HTML final têm os valores de temas/papel.json"
else
  echo "FALHOU --tema papel não chegou ao HTML final: $DT"; tail -5 "$DT/build.log"; falhas=$((falhas + 1))
fi
cp "$SK/modelos/06-raias/_src/06-abertura-de-conta.json" "$DT/_src/"
AI_DIAGRAMS_TEMA=papel python3 "$SK/scripts/gerar_raias.py" "$DT/_src/06-abertura-de-conta.json" > /dev/null
if grep -q '<meta name="tema" content="papel">' "$DT/_src/06-abertura-de-conta.html" \
   && grep -q 'family=Public+Sans' "$DT/_src/06-abertura-de-conta.html"; then
  echo "ok     AI_DIAGRAMS_TEMA=papel: o gerador grava a meta e o link do tema no fonte"
else
  echo "FALHOU AI_DIAGRAMS_TEMA não chegou ao fonte gerado: $DT/_src/06-abertura-de-conta.html"; falhas=$((falhas + 1))
fi
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); del t["cores"]["acento"]; json.dump(t,open(sys.argv[2],"w"))' \
  "$SK/temas/papel.json" "$DT/incompleto.json"
espera "TEMA-INCOMPLETO: falta cores.acento" python3 "$SK/scripts/build.py" "$DT/_src/05-comparacao-mensageria.html" --tema "$DT/incompleto.json"
espera "TEMA-INCOMPLETO: falta cores.acento" node "$SK/der/der-montar.mjs" "$SK/modelos/03-der-schema/_src/der-conta.layout.mjs" --tema "$DT/incompleto.json"
espera TEMA-INEXISTENTE python3 "$SK/bpmn/gerar_bpmn.py" "$SK/modelos/08-bpmn/_src/08-contestacao-pagamento.json" --tema nao-existe
sed "s#/\*ESTILO\*/#/*ESTILO*/ .nota{font-family:'Inter',sans-serif}#" "$SK/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html" > "$DC/_src/fonte.html"
espera FONTE-FORA-DO-TEMA python3 "$SK/scripts/poster_lint.py" --static "$DC/_src/fonte.html"

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
if python3 -m unittest discover -s "$T" -p 'test_importar*.py'; then
  echo "ok     importadores: formatos, modelos nativos e erros"
else
  falhas=$((falhas + 1))
fi
[ $falhas -eq 0 ] && echo "total: 0" || { echo "total: $falhas"; exit 1; }
