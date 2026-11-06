---
inclusion: always
---

# Diagramas deste projeto

Todo pedido de diagrama neste projeto (poster de arquitetura AWS, C4, fluxo, sequência, máquina de estados, raias, BPMN, tabela de comparação, catálogo em cards, DER ou matriz de dependência) usa a skill `ai-diagrams`. Não responda com markdown, Mermaid ou texto no lugar do diagrama.

Antes de desenhar:

1. Leia o `SKILL.md` da skill, em `.kiro/skills/ai-diagrams/` no projeto ou em `~/.kiro/skills/ai-diagrams/`. O roteador dele escolhe o tipo.
2. Se o pedido não diz se o nome do cliente aparece no diagrama, pergunte antes, numa mensagem só: com cliente (`<Projeto> · <tema> · <Cliente>`, e qual é o nome) ou sem cliente (`<Projeto> · <tema>`), oferecendo o rodapé `<Projeto> · <tipo de diagrama> · AAAA-MM` e a versão `V1`. Nunca deduza o cliente do nome da pasta ou do repositório. Sem interação possível, siga sem cliente e diga isso na entrega.
3. Abra o modelo do tipo em `modelos/` e a referência em `references/`, dentro da pasta da skill.
4. Escreva o fonte em `diagramas/_src/` e rode o comando do tipo, que está no `SKILL.md` e gera o PNG em `diagramas/`.
5. O gate do comando tem que terminar em zero. Abra o PNG e confira a leitura antes de dizer que terminou.

Regras:

- Não crie script auxiliar (`.py`, `.sh` ou outro) para rodar o build. Rode o comando da skill direto. Se não puder executar, entregue o fonte e o comando exato para o usuário rodar.
- Rode cada comando sozinho, sem pipe (`|`), sem redirecionamento (`2>&1`, `>`) e sem `&&`: o agente do projeto só libera o comando puro.
- Não copie nem edite o CSS da skill no projeto. Largura, fonte e grade já vêm certas.
- No poster e no fluxo com passos, siga a "Receita de coordenadas" de `references/linguagem-visual.md` e rode `poster_lint.py --fix` antes do `build.py`.
- Gate reprovado não é entrega. Nunca diga que terminou enquanto o gate reprova. Depois de cinco rodadas de correção sem zerar, pare e entregue o fonte, a saída do último gate e a frase "o gate reprovou; o PNG não foi gerado".
- Se o pedido de fluxo for ambíguo entre passos, raias e BPMN, pergunte antes.
