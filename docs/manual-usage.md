# Manual usage

The commands on this page run without any AI. Use them to learn the build cycle or to edit a diagram by hand. With an AI, the AI writes the source and runs the same commands.

Complete the requirements in [install.md](install.md) first. Set three variables before you start:

```bash
export AI_DIAGRAMS="/path/where/you/cloned/ai-diagrams"
```

```bash
export SKILL="$AI_DIAGRAMS/skills/ai-diagrams"
```

```bash
export PROJECT="/path/to/your/project"
```

Sources go in `diagrams/_src/` inside your project. The build writes the self-contained HTML and the PNG to `diagrams/`, the parent folder of `_src/`.

## Import an existing file

```bash
python3 "$SKILL"/scripts/import_cli.py process.mmd --out "$PROJECT"/diagrams --lang en
python3 "$SKILL"/scripts/import_cli.py schema.sql --type matrix --out "$PROJECT"/diagrams --lang en
```

With the npm CLI installed, use `ai-diagrams import` with the same arguments. Supported inputs are Mermaid flowcharts, sequences, states and ER, BPMN 2.0 XML, SQL DDL, CSV catalogs and YAML comparisons. The importer writes native sources and calls the generator and gate below. For the exact subset and ready-to-run examples, see [importing.md](importing.md). Use `--source-only` only to prepare sources without Chrome; the full gate and PNG remain pending.

## AWS architecture poster and numbered-step flow

1. Create the folder and copy the template:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/assets/template-poster.html "$PROJECT"/diagrams/_src/01-example.html
```

2. Edit the source: title, boxes, arrows, step badges and the step list. The layout rules are in `skills/ai-diagrams/references/visual-language.md`. For a numbered-step flow, start from `skills/ai-diagrams/templates/02-step-flow/_src/02-event-outbox.html` instead.

3. Run the lint. `--fix` snaps loose arrow ends to the nearest box, up to 60px:

```bash
python3 "$SKILL"/scripts/poster_lint.py --fix "$PROJECT"/diagrams/_src/01-example.html
```

4. Build the self-contained HTML and the PNG. The capture height is measured automatically:

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagrams/_src/01-example.html
```

**Expected:** two lines starting with `OK`, the HTML and the PNG in `"$PROJECT"/diagrams/`.

5. Open `"$PROJECT"/diagrams/01-example.png` and read it. A passing lint does not guarantee a readable diagram. Cut text, labels touching boxes and empty areas only show in the PNG.

## C4 diagrams

C4 comes from one JSON model. Start from model 11:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/11-c4/_src/11-c4-pix.json "$PROJECT"/diagrams/_src/
```

Change people, systems, containers, relationships and views. The model, the views and the rules are described in `skills/ai-diagrams/references/c4.md`. Then build every view:

```bash
python3 "$SKILL"/scripts/build_c4.py "$PROJECT"/diagrams/_src/11-c4-pix.json
```

**Expected:** for each view, the source path and two lines starting with `OK`; the container view ends in `11-c4-pix.png`, the context view in `11-c4-pix-context.png`.

A Structurizr `workspace.dsl` goes through the importer instead: `ai-diagrams import workspace.dsl --out "$PROJECT"/diagrams/name`.

## ER diagram per schema

1. Copy the logical model and the layout from the reference model:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/03-er-schema/_src/model.json "$SKILL"/templates/03-er-schema/_src/er-account.layout.mjs "$PROJECT"/diagrams/_src/
```

2. Change tables and columns in `model.json` and positions in the layout file. The format is in `skills/ai-diagrams/references/er.md`.

3. Generate the source, then build the PNG:

```bash
node "$SKILL"/er/er-build.mjs "$PROJECT"/diagrams/_src/er-account.layout.mjs
```

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagrams/_src/er-account.html
```

## Schema dependency matrix

The matrix uses the same `model.json` as the ER diagram.

```bash
node "$SKILL"/er/er-overview.mjs "$PROJECT"/diagrams/_src/model.json
```

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagrams/_src/er-overview.html
```

## Swimlanes

1. Copy the reference spec:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/06-swimlanes/_src/06-account-opening.json "$PROJECT"/diagrams/_src/
```

2. Change lanes, phases, elements and order in the JSON. The format is in `skills/ai-diagrams/references/swimlanes.md`.

3. Generate the HTML from the spec:

```bash
python3 "$SKILL"/scripts/build_swimlanes.py "$PROJECT"/diagrams/_src/06-account-opening.json
```

**Expected:** the path of `06-account-opening.html` and a line `canvas ... · 4 lanes · 5 phases · 5 arrows`.

4. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceptual.py "$PROJECT"/diagrams/_src/06-account-opening.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `06-account-opening.png`.

## Sequence diagram

1. Copy the reference spec:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/09-sequence/_src/09-pix-outbound.json "$PROJECT"/diagrams/_src/
```

2. Change participants and messages in the JSON. The format is in `skills/ai-diagrams/references/sequence.md`.

3. Generate the HTML from the spec:

```bash
python3 "$SKILL"/scripts/build_sequence.py "$PROJECT"/diagrams/_src/09-pix-outbound.json
```

**Expected:** the path of `09-pix-outbound.html` and a line `canvas 1290x1216 · 6 participants · 16 messages · 2 fragments`.

4. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceptual.py "$PROJECT"/diagrams/_src/09-pix-outbound.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `09-pix-outbound.png`.

## State machine

1. Copy the reference spec:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/10-state-machine/_src/10-pix-states.json "$PROJECT"/diagrams/_src/
```

2. Change states and transitions in the JSON. The format is in `skills/ai-diagrams/references/states.md`.

3. Generate the HTML from the spec (needs `node`):

```bash
python3 "$SKILL"/scripts/build_states.py "$PROJECT"/diagrams/_src/10-pix-states.json
```

**Expected:** the path of `10-pix-states.html` and a line `canvas 969x1708 · 11 states · 14 transitions`. If the graph has a defect, the output is `STATES FAILED <code>: ` followed by the state or transition.

4. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceptual.py "$PROJECT"/diagrams/_src/10-pix-states.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `10-pix-states.png`.

## Cards catalog

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/07-card-catalog/_src/07-api-catalog.html "$PROJECT"/diagrams/_src/
```

2. Change the cards in the HTML. The classes are in `skills/ai-diagrams/references/swimlanes.md`, in the section on hand-written conceptual diagrams.

3. Run the gate and build the PNG:

```bash
python3 "$SKILL"/scripts/conceptual.py "$PROJECT"/diagrams/_src/07-api-catalog.html
```

**Expected:** `lint 0` and two lines starting with `OK`, the last one ending in `07-api-catalog.png`.

## BPMN 2.0

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/08-bpmn/_src/08-payment-dispute.json "$PROJECT"/diagrams/_src/
```

2. Change lanes, nodes and connections in the JSON. The format is in `skills/ai-diagrams/references/bpmn.md`.

3. Generate the BPMN file, the viewer and the PNG:

```bash
python3 "$SKILL"/bpmn/build_bpmn.py "$PROJECT"/diagrams/_src/08-payment-dispute.json
```

**Expected:** `structure, reachability, overlap and bpmn-js import: 0 problems` and three lines starting with `OK`: the `.bpmn`, the `.html` and the `.png` in `"$PROJECT"/diagrams/`. The `.bpmn` file opens in Camunda Modeler or at demo.bpmn.io for editing.

## Comparison table

1. Copy the reference model:

```bash
mkdir -p "$PROJECT"/diagrams/_src && cp "$SKILL"/templates/05-comparison-table/_src/05-messaging-comparison.html "$PROJECT"/diagrams/_src/
```

2. Change criteria and options. The format is in `skills/ai-diagrams/references/table.md`.

3. Build the PNG:

```bash
python3 "$SKILL"/scripts/build.py "$PROJECT"/diagrams/_src/05-messaging-comparison.html
```

**Expected:** two lines starting with `OK`, the last one ending in `05-messaging-comparison.png`.

## Themes

Every command on this page takes `--theme <name or path.json>`. A name resolves to `$SKILL/themes/<name>.json`; a path points to a theme JSON in any folder. Without the flag, the command uses the `<meta name="theme">` of the source, then the variable `AI_DIAGRAMS_THEME`, then the default `ai-diagrams`.

1. Build any diagram in the `paper` theme:
```bash
python3 "$SKILL/scripts/build.py" "$PROJECT/diagrams/_src/01-my-architecture.html" --theme paper
```

2. Create your own theme from the default and use it in every command of the session:
```bash
cp "$SKILL/themes/ai-diagrams.json" "$PROJECT/diagrams/_src/theme.json"
```

```bash
export AI_DIAGRAMS_THEME="$PROJECT/diagrams/_src/theme.json"
```

Edit the values in `colors`, `derived`, `er_palette` and `fonts`, and keep every key. A generator run with a theme (`build_swimlanes.py`, `build_sequence.py`, `build_states.py`, `er-build.mjs`, `er-overview.mjs`) writes it into the source as `<meta name="theme">`, so the build that follows uses the same theme.

**Expected:** the same `OK` lines as without the theme. A theme with a missing key stops with `THEME-INCOMPLETE: missing <group>.<key>` before Chrome opens.

## When the gate fails

The gate prints the defect and its position, and no PNG is written. Fix the source and run the same command again. The defect codes and what each one checks are listed in [how-it-works.md](how-it-works.md).
