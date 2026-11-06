# Manual usage

The commands on this page run without any AI. Use them to learn the build cycle or to edit a diagram by hand. With an AI, the AI writes the source and runs the same commands.

Complete the requirements in [install.md](install.md) first. Set three variables before you start:

```bash
export PROSA="/path/where/you/cloned/prosa"
```

```bash
export SKILL="$PROSA/skills/prosa"
```

```bash
export PROJECT="/path/to/your/project"
```

Sources go in `diagramas/_src/` inside your project. The build writes the self-contained HTML and the PNG to `diagramas/`, the parent folder of `_src/`.

Program output is in Portuguese. This page quotes it as printed.

## AWS architecture poster and numbered-step flow

1. Create the folder and copy the template:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/assets/template-poster.html "$PROJECT"/diagramas/_src/01-example.html
```

2. Edit the source: title, boxes, arrows, step badges and the step list. The layout rules are in `skills/prosa/references/linguagem-visual.md`. For a numbered-step flow, start from `skills/prosa/modelos/02-fluxo-passos/_src/02-outbox-eventos.html` instead.

3. Run the lint. `--fix` snaps loose arrow ends to the nearest box, up to 60px:

```bash
python3 "$SKILL"/scripts/poster_lint.py --fix "$PROJECT"/diagramas/_src/01-example.html
```

4. Build the self-contained HTML and the PNG. The capture height is measured automatically:

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagramas/_src/01-example.html
```

**Expected:** two lines starting with `OK`, the HTML and the PNG in `"$PROJECT"/diagramas/`.

5. Open `"$PROJECT"/diagramas/01-example.png` and read it. A passing lint does not guarantee a readable diagram. Cut text, labels touching boxes and empty areas only show in the PNG.

## ER diagram per schema

1. Copy the logical model and the layout from the reference model:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/03-der-schema/_src/modelo.json "$SKILL"/modelos/03-der-schema/_src/der-conta.layout.mjs "$PROJECT"/diagramas/_src/
```

2. Change tables and columns in `modelo.json` and positions in the layout file. The format is in `skills/prosa/references/der.md`.

3. Generate the source, then build the PNG:

```bash
node "$SKILL"/der/der-montar.mjs "$PROJECT"/diagramas/_src/der-conta.layout.mjs
```

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagramas/_src/der-conta.html
```

## Schema dependency matrix

The matrix uses the same `modelo.json` as the ER diagram.

```bash
node "$SKILL"/der/der-visao-geral.mjs "$PROJECT"/diagramas/_src/modelo.json
```

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagramas/_src/der-visao-geral.html
```

## Swimlanes

1. Copy the reference spec:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/06-raias/_src/06-abertura-de-conta.json "$PROJECT"/diagramas/_src/
```

2. Change lanes, phases, elements and order in the JSON. The format is in `skills/prosa/references/raias.md`.

3. Generate the HTML from the spec:

```bash
python3 "$SKILL"/scripts/gerar_raias.py "$PROJECT"/diagramas/_src/06-abertura-de-conta.json
```

**Expected:** the path of `06-abertura-de-conta.html` and a line `canvas ... · 4 raias · 5 fases · 5 setas` (lanes, phases, arrows).

4. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceitual.py "$PROJECT"/diagramas/_src/06-abertura-de-conta.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `06-abertura-de-conta.png`.

## Sequence diagram

1. Copy the reference spec:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/09-sequencia/_src/09-pix-saida.json "$PROJECT"/diagramas/_src/
```

2. Change participants and messages in the JSON. The format is in `skills/prosa/references/sequencia.md`.

3. Generate the HTML from the spec:

```bash
python3 "$SKILL"/scripts/gerar_sequencia.py "$PROJECT"/diagramas/_src/09-pix-saida.json
```

**Expected:** the path of `09-pix-saida.html` and a line `canvas 1290x1216 · 6 participantes · 16 mensagens · 2 fragmentos` (participants, messages, fragments).

4. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceitual.py "$PROJECT"/diagramas/_src/09-pix-saida.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `09-pix-saida.png`.

## Cards catalog

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/07-catalogo-cards/_src/07-catalogo-apis.html "$PROJECT"/diagramas/_src/
```

2. Change the cards in the HTML. The classes are in `skills/prosa/references/raias.md`, in the section on hand-written conceptual diagrams.

3. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceitual.py "$PROJECT"/diagramas/_src/07-catalogo-apis.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `07-catalogo-apis.png`.

## BPMN 2.0

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/08-bpmn/_src/08-contestacao-pagamento.json "$PROJECT"/diagramas/_src/
```

2. Change lanes, nodes and connections in the JSON. The format is in `skills/prosa/references/bpmn.md`.

3. Generate the BPMN file, the viewer and the PNG:

```bash
python3 "$SKILL"/bpmn/gerar_bpmn.py "$PROJECT"/diagramas/_src/08-contestacao-pagamento.json
```

**Expected:** `estrutura, alcance, sobreposição e importação no bpmn-js: 0 problemas` (structure, reachability, overlap and bpmn-js import: 0 problems) and three lines starting with `OK`: the `.bpmn`, the `.html` and the `.png` in `"$PROJECT"/diagramas/`. The `.bpmn` file opens in Camunda Modeler or at demo.bpmn.io for editing.

## Comparison table

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagramas/_src && cp "$SKILL"/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html "$PROJECT"/diagramas/_src/
```

2. Change criteria and options. The format is in `skills/prosa/references/tabela.md`.

3. Build the PNG:

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagramas/_src/05-comparacao-mensageria.html
```

**Expected:** two lines starting with `OK`, the last one ending in `05-comparacao-mensageria.png`.

## When the gate fails

The gate prints the defect and its position, and no PNG is written. Fix the source and run the same command again. The defect codes and what each one checks are listed in [how-it-works.md](how-it-works.md).
