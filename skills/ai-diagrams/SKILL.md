---
name: ai-diagrams
description: Cria diagramas técnicos com um padrão visual único e escolhe sozinha o tipo certo. Poster de arquitetura AWS e fluxo com passos numerados (ícones AWS, lint geométrico, PNG); C4 de contexto e contêineres; tabela de comparação ou comparativo de opções; diagrama de sequência entre serviços (chamada, resposta, alt e loop); máquina de estados (ciclo de vida e status); fluxo em raias (swimlane) entre times; conceitual em cards ou catálogo; BPMN 2.0 editável no Camunda ou bpmn.io; DER por schema em pé de galinha; matriz de dependência. Use sempre que o usuário pedir diagrama, poster, desenho de arquitetura, topologia AWS, C4, contêineres, fluxo, processo, BPMN, raias, swimlane, sequência, chamada entre serviços, máquina de estados, status, ciclo de vida, tabela comparativa, comparação entre A e B, catálogo, DER, modelo lógico, diagrama de tabelas ou matriz de dependência, ou quiser transformar documento em diagrama. Também use para editar, auditar ou regenerar diagramas existentes em diagramas/_src/.
---

# Diagramas padronizados

Uma porta de entrada para todos os tipos de diagrama. Todo tipo segue o mesmo princípio: o conteúdo vem de um documento ou modelo, o layout é decidido (à mão ou por coordenadas calculadas; quando um motor de layout entra, ele só posiciona e o desenho é da skill), um gate automático reprova defeito e o PNG é olhado antes da entrega.

## 1. Roteador: qual tipo fazer

Leia o pedido e escolha a linha. Os modelos ficam em `modelos/`, dentro desta skill, ao lado deste `SKILL.md`; cada um tem o fonte em `_src/` e o PNG gerado. `modelos/gerar.sh` regenera todos pelo gate de cada tipo.

| Tipo | Quando (gatilho no pedido) | Referência | Modelo | Gate |
|---|---|---|---|---|
| Poster de arquitetura AWS | arquitetura, topologia, serviços AWS, "poster do bloco", desenho de solução | `references/linguagem-visual.md` | `01-arquitetura-aws` | `poster_lint.py` via `build.py` |
| Fluxo com passos numerados | fluxo técnico entre componentes ou serviços, com ordem: "como o evento sai daqui e chega lá" | `references/linguagem-visual.md` | `02-fluxo-passos` | `poster_lint.py` via `build.py` |
| C4 (contexto e contêineres) | C4, diagrama de contexto ou de contêineres, "visão do sistema", quem usa e de que sistemas depende | `references/c4.md` | `11-c4` | `poster_lint.py` via `build.py` |
| Tabela de comparação | comparar opções, "A vs B", comparativo, critérios, trade-off, matriz de decisão | `references/tabela.md` | `05-tabela-comparacao` | `poster_lint.py` via `build.py` |
| Diagrama de sequência | sequência, "quem chama quem", chamada e resposta entre serviços, API ou parceiro, com espera, `alt` ou `loop` | `references/sequencia.md` | `09-sequencia` | `conceitual.py` |
| Máquina de estados | máquina de estados, ciclo de vida, status de pedido, pagamento ou conta, "de onde para onde pode ir" | `references/estados.md` | `10-maquina-estados` | `gerar_estados.py` e `conceitual.py` |
| Fluxo em raias | fluxo entre times, papéis ou atores, sem AWS: swimlane, "quem faz o quê", handoff | `references/raias.md` | `06-raias` | `conceitual.py` |
| Conceitual em cards | catálogo, inventário de serviços, anatomia de um artefato, mapa de responsabilidades sem ordem | `references/raias.md` | `07-catalogo-cards` | `conceitual.py` |
| BPMN 2.0 | BPMN, processo de negócio, gateway, evento, ou resultado editável no Camunda ou bpmn.io | `references/bpmn.md` | `08-bpmn` | `gerar_bpmn.py` |
| DER por schema | DER, modelo lógico, tabelas e FKs, diagrama do banco, schema | `references/der.md` | `03-der-schema` | `poster_lint.py` via `build.py` |
| Matriz de dependência | dependência entre schemas, módulos ou domínios em visão geral | `references/der.md` | `04-matriz-dependencia` | `poster_lint.py` via `build.py` |

Variações que usam o pipeline do poster, sem modelo próprio: glossário ilustrado ou analogia (chips e frames sem ícone AWS), mapa as-built (frames com contagem por bloco).

**"Fluxo" é ambíguo.** Decida assim:

1. o assunto é a ordem das chamadas e quem espera a resposta, mais que onde cada serviço fica? **sequência**;
2. o assunto é a situação de uma coisa e os eventos que a mudam, sem ordem de chamada? **máquina de estados**;
3. tem serviço AWS, fila, banco ou API como caixa e a topologia importa? **fluxo com passos**;
4. as linhas são times ou papéis e não há AWS? **raias**;
5. pediu BPMN, gateway, evento, ou quer editar numa ferramenta de processo? **BPMN**.

Se o pedido não cai claramente numa linha, ou cai em duas, pergunte ao usuário antes de desenhar, oferecendo as duas opções com uma frase sobre cada.

## 2. Setup (uma vez por máquina)

1. `pip3 install diagrams`: só o acervo de ícones oficiais AWS em PNG; a biblioteca nunca roda.
2. Google Chrome: build, lint e captura usam modo headless.
3. Node 18 ou mais novo, para os geradores de DER, matriz e máquina de estados.
4. Overrides se preciso: `POSTER_CHROME` (caminho do Chrome) e `POSTER_ICONBASE` (pasta `resources/aws`).

## 3. Estrutura de trabalho

No projeto do usuário, fontes em `diagramas/_src/`, entregáveis (HTML self-contained, PNG e, no BPMN, o `.bpmn`) na pasta pai `diagramas/`. Crie a estrutura se não existir. Os scripts usam o CSS do projeto (`_src/_estilo.css`, `_src/_estilo-conceitual.css`) quando existe; senão, o da skill.

## 4. Ciclo comum a todos os tipos

1. **Conteúdo antes de desenho.** O diagrama materializa um documento de decisão, um processo descrito ou um modelo de dados. Leia a fonte ou pergunte qual é. Sem fonte escrita, rascunhe a narrativa com o usuário primeiro.
2. **Fonte.** Parta do modelo do tipo em `modelos/` e leia a referência do tipo antes de escrever.
3. **Gate em zero.** Rode o comando do tipo (abaixo). Gate com problema não gera PNG; corrija o fonte e rode de novo.
   - Rode o comando como está aqui, sem pipe (`|`), redirecionamento (`2>&1`, `>`) ou `&&`: alguns ambientes só liberam o comando puro.
   - Não crie script auxiliar e não copie nem edite o CSS da skill no projeto (`_estilo.css`, `_estilo-conceitual.css`). Largura, fonte e grade já vêm certas; mudar o CSS é a causa mais comum de `TEXTO-MINIMO`.
   - Não incorpore fontes, ícones ou imagens em base64 no fonte: o `build.py` faz isso no HTML final. O fonte fica com `/*ESTILO*/`, `aws://` e o link do Google Fonts.
   - Se o gate der `MEDICAO-FALHOU` ou o Chrome não responder, a causa costuma ser um sandbox que bloqueia o Chrome (Codex com `workspace-write`, por exemplo). Peça para rodar o comando fora do sandbox; não contorne o gate.
   - **Gate reprovado não é entrega.** Nunca diga que terminou enquanto o gate reprova. Se depois de cinco rodadas de correção o gate ainda reprovar, pare e entregue o fonte, a saída do último gate e a frase "o gate reprovou; o PNG não foi gerado".
4. **Auditoria visual (obrigatória).** Leia o PNG com a tool Read e critique: texto cortado ou espremido, rótulo encostado em outro, seta colada em outra ou atravessando caixa, rodapé cortado, área morta, hierarquia confusa. O gate mede geometria, não leitura. Corrija e repita 3 e 4 até passar limpo. Nunca entregue sem olhar o PNG.
5. **Entrega.** Fonte, HTML final e PNG juntos (no BPMN, também o `.bpmn`).

Em lote, faça o ciclo inteiro de um diagrama antes de começar o próximo.

### Legibilidade vence o tamanho padrão

A largura padrão (1760px no poster, 1400px no conceitual) e as medidas dos modelos servem para padronizar, não para espremer. Se o desenho não fica legível nelas, aumente o que for preciso: a largura da página (o fonte declara `<meta name="largura" content="N">` e o `build.py` captura nessa largura; o DER já faz isso a partir do canvas do layout), a altura, o tamanho das caixas ou o espaço entre elas. Nenhum elemento sai da moldura nem passa da borda de outro bloco da página: legenda, faixas e desenho alinham na mesma largura.

### Opções do pedido: cliente, rodapé e versão

Antes de desenhar, confira se o pedido diz se o nome do cliente aparece no diagrama. Se não disser, pergunte numa mensagem só, com as duas opções:

1. **com cliente**: cabeçalho `<Projeto> · <tema> · <Cliente>`, e diga qual é o nome;
2. **sem cliente**: cabeçalho `<Projeto> · <tema>`.

`<Projeto>` é o nome do time, do produto ou da organização que o usuário informar. Se ele não informar, o cabeçalho começa direto pelo `<tema>`.

Na mesma pergunta, confirme o rodapé (padrão `<Projeto> · <tipo de diagrama> · AAAA-MM`, ou só `<tipo de diagrama> · AAAA-MM` sem projeto) e a versão (padrão `V1`), oferecendo o padrão. Se o pedido já diz cliente, rodapé e versão, ou diz "sem cliente no cabeçalho", não pergunte.

**Textos do usuário.** Se o usuário passar título, subtítulo, kicker, textos de seção ou da faixa, use o texto literal, sem reescrever. Na pergunta acima, diga que ele pode mandar esses textos; se não mandar, a skill escreve.

Nunca deduza o cliente, o autor ou a versão do caminho da pasta, do nome do repositório ou de outro arquivo do projeto: só vale o que o usuário ou a fonte do diagrama disserem.

Quando não há como perguntar (execução não interativa, como `claude -p` ou o Kiro sem interação, ou uso por knowledge base), siga sem cliente, com rodapé e versão padrão, e diga isso na entrega.

### Registro do texto

O texto que abre o diagrama serve só para situar o leitor no desenho. É estritamente técnico:

- **Título:** o nome técnico do sistema, fluxo ou decisão, com o recorte quando ajuda ("API de pagamentos e extrato assíncrono", "schema conta · Contas e movimentos"). Nunca uma frase de tese, promessa ou conclusão.
- **Subtítulo:** uma a três frases que dizem o que o desenho mostra, o recorte (o que está dentro e o que ficou fora) e como ler (ordem dos passos, o que a cor ou a raia significa). Número só se estiver na fonte.
- **Faixa de fechamento** (conceitual): um fato do fluxo ou o que ficou fora do desenho, não uma conclusão de venda.
- Proibido: adjetivo de valor, promessa, benefício, metáfora, frase de efeito e antítese. O gate reprova esses termos com `TEXTO-MARKETING` (lista em `scripts/texto_tecnico.py`); o que a lista não pega, você confere ao ler o PNG. Termo técnico em inglês como o mercado usa (bucket, dead-letter topic, consumer group, deploy); nada de tradução inventada. Texto de caixa curto; a explicação vai nos passos ou nas seções.

**Cor só do tema.** O fonte nunca escreve hexadecimal nem `rgb()`, nem em estilo local: usa `var(--tinta)`, `var(--apoio)`, `var(--cinza)`, `var(--zona)`, `var(--papel)`, `var(--acento)`, `var(--risco)` e `var(--risco-fundo)`, declarados no `:root` do CSS base com os valores de `temas/ai-diagrams.json`. Em SVG a cor vai em `style` (`style="stroke:var(--apoio)"`), porque atributo `stroke` e `fill` não aceita `var()`. O gate reprova cor literal com `COR-FORA-DO-TEMA`.

## 5. Comandos por tipo

`<skill>` é a pasta desta skill.

**Poster, fluxo com passos e tabela**
```bash
python3 <skill>/scripts/poster_lint.py --fix diagramas/_src/NN-nome.html
python3 <skill>/scripts/build.py diagramas/_src/NN-nome.html
```
O build mede a altura real da página e captura nela; se receber uma altura menor que a página, reprova com `CORTADO`. A largura é 1760px, ou a do `<meta name="largura">` do fonte; conteúdo que passa dela reprova com `TRANSBORDA`. Regras do poster que evitam retrabalho:

- Planeje a grade antes: colunas por camada, linhas por ator. Faça a conta das pontas, dos corredores e dos badges pela "Receita de coordenadas" de `references/linguagem-visual.md`.
- Rode `poster_lint.py --fix` antes do build: ele encosta pontas soltas e leva badges para a seta; depois rode sem `--fix` e corrija o resto com as coordenadas que ele sugere.
- Setas ortogonais (`path` com `H`/`V`); ponta encosta na caixa de destino. Num `.node`, a caixa sólida é o ícone de 44px: seta vertical nunca atravessa o rótulo embaixo dele.
- Duas setas nunca correm na mesma linha: use corredores entre as colunas.
- Cada passo tem um badge sobre a linha da própria seta e um item em `.passos`.
- Ícones como `aws://categoria/arquivo.png`, com o nome conferido no acervo.

O lint reprova `SOLTA`, `ATRAVESSA`, `COLINEAR`, `SEM-BADGES`, `SEM-PASSOS`, `PASSOS-DIVERGEM`, `BADGE-SOLTO`, `SOBREPOE`, `SETA-SOBRE-TEXTO`, `DENTRO-DA-CAIXA`, `TEXTO-SOBRE-BORDA`, `SETA-NA-BORDA`, `ROTULO-SOLTO`, `PONTA-DENTRO`, `TRANSBORDA`, `TEXTO-MARKETING` e `SEM-ESTILO`; `SOBREPOE`, `SETA-SOBRE-TEXTO`, `TEXTO-SOBRE-BORDA`, `SETA-NA-BORDA`, `ROTULO-SOLTO`, `PONTA-DENTRO` e `TRANSBORDA` são medidos no Chrome. Área morta (zona muito maior que o conteúdo) o gate não mede: confira no PNG e encolha a zona. Documento sem `<svg class="edges">` (tabela, matriz) não exige badges nem passos. No C4 (`references/c4.md`) entram também `C4-SEM-TIPO` e `C4-SEM-LEGENDA`.

**Raias e conceitual**
```bash
python3 <skill>/scripts/gerar_raias.py diagramas/_src/NN-fluxo.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-fluxo.html
```
O primeiro comando só existe para raias; cards e painéis são HTML escrito à mão a partir do modelo 07.

**Sequência**
```bash
python3 <skill>/scripts/gerar_sequencia.py diagramas/_src/NN-nome.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-nome.html
```
Além das réguas do conceitual, reprova `TEXTO-SOBRE-VIDA` (rótulo em cima de linha de vida ou barra de ativação).

**Máquina de estados**
```bash
python3 <skill>/scripts/gerar_estados.py diagramas/_src/NN-nome.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-nome.html
```
O gerador usa `node` (elkjs em `estados/`) e reprova antes do desenho: `SEM-INICIAL`, `DESCONHECIDO`, `SEM-EVENTO`, `SAI-DO-FINAL`, `INALCANCAVEL` e `SEM-SAIDA`.

**BPMN**
```bash
python3 <skill>/bpmn/gerar_bpmn.py diagramas/_src/NN-processo.json
```

**DER e matriz**
```bash
node <skill>/der/der-montar.mjs diagramas/_src/der-<schema>.layout.mjs
python3 <skill>/scripts/build.py diagramas/_src/der-<schema>.html
node <skill>/der/der-visao-geral.mjs diagramas/_src/modelo.json
python3 <skill>/scripts/build.py diagramas/_src/der-visao-geral.html
```
O DER não é desenhado caixa a caixa: o conteúdo de cada tabela vem do `modelo.json`, e só a posição e a raia de cada seta são decididas à mão no layout.
