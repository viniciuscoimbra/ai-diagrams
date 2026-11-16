---
name: ai-diagrams
description: Builds technical diagrams with one visual standard and picks the right type. AWS architecture poster and flow with numbered steps (AWS icons, geometric lint, PNG); C4 context and containers; comparison table of options; sequence diagram between services (call, reply, alt and loop); state machine (lifecycle and status); swimlane flow between teams; conceptual cards or catalog; BPMN 2.0 editable in Camunda or bpmn.io; ER diagram per schema in crow's foot; dependency matrix. Use whenever the user asks for a diagram, poster, architecture drawing, AWS topology, C4, containers, flow, process, BPMN, swimlanes, sequence, calls between services, state machine, status, lifecycle, comparison table, A vs B, catalog, ERD, logical model, table diagram or dependency matrix, or wants a document turned into a diagram (pt-BR: diagrama, fluxo, raias, sequência, máquina de estados, tabela comparativa, catálogo, DER, matriz de dependência). Also use to edit, audit or regenerate existing diagrams in diagrams/_src/.
---

# Standardized diagrams

One entry point for every diagram type. Every type follows the same principle: the content comes from a document or a model, the layout is decided (by hand or by computed coordinates; when a layout engine is used, it only positions things and the drawing belongs to the skill), an automatic gate fails defects and the PNG is looked at before delivery.

## 1. Router: which type to make

Read the request and pick the row. The templates are in `templates/`, inside this skill, next to this `SKILL.md`; each one has its source in `_src/` and the generated PNG. `templates/build-all.sh` regenerates all of them through each type's gate.

| Type | When (trigger in the request) | Reference | Template | Gate |
|---|---|---|---|---|
| AWS architecture poster | architecture, topology, AWS services, "block poster", solution drawing | `references/visual-language.md` | `01-aws-architecture` | `poster_lint.py` via `build.py` |
| Flow with numbered steps | technical flow between components or services, with an order: "how the event leaves here and gets there" | `references/visual-language.md` | `02-step-flow` | `poster_lint.py` via `build.py` |
| C4 (landscape, context, containers, components, dynamic, deployment) | C4, context, container or component diagram, "system view", who uses it and which systems it depends on, where each part runs, or a Structurizr `workspace.dsl` | `references/c4.md` | `11-c4` | `build_c4.py` (elkjs), then `poster_lint.py` via `build.py` |
| Comparison table | compare options, "A vs B", comparison, criteria, trade-off, decision matrix | `references/table.md` | `05-comparison-table` | `poster_lint.py` via `build.py` |
| Sequence diagram | sequence, "who calls whom", call and reply between services, API or partner, with waiting, `alt` or `loop` | `references/sequence.md` | `09-sequence` | `conceptual.py` |
| State machine | state machine, lifecycle, status of an order, payment or account, "where it can go from where" | `references/states.md` | `10-state-machine` | `build_states.py` and `conceptual.py` |
| Swimlane flow | flow between teams, roles or actors, without AWS: swimlane, "who does what", handoff | `references/swimlanes.md` | `06-swimlanes` | `conceptual.py` |
| Conceptual cards | catalog, service inventory, anatomy of an artifact, map of responsibilities with no order | `references/swimlanes.md` | `07-card-catalog` | `conceptual.py` |
| BPMN 2.0 | BPMN, business process, gateway, event, or a result editable in Camunda or bpmn.io | `references/bpmn.md` | `08-bpmn` | `build_bpmn.py` |
| ER diagram per schema | ERD, logical model, tables and FKs, database diagram, schema | `references/er.md` | `03-er-schema` | `poster_lint.py` via `build.py` |
| Dependency matrix | dependency between schemas, modules or domains in an overview | `references/er.md` | `04-dependency-matrix` | `poster_lint.py` via `build.py` |

Variations that use the poster pipeline, without their own template: illustrated glossary or analogy (chips and frames without AWS icons), as-built map (frames with a count per block).

**"Flow" is ambiguous.** Decide like this:

1. is the subject the order of the calls and who waits for the reply, more than where each service lives? **sequence**;
2. is the subject the status of one thing and the events that change it, with no call order? **state machine**;
3. are there AWS services, queues, databases or APIs as boxes, and does the topology matter? **flow with steps**;
4. are the rows teams or roles, with no AWS? **swimlanes**;
5. did the user ask for BPMN, gateway, event, or want to edit it in a process tool? **BPMN**.

If the request does not fall clearly into one row, or falls into two, ask the user before drawing, offering the two options with one sentence about each.

## 2. Setup (once per machine)

### When importing an existing file

If the user brings Mermaid, `.bpmn`, SQL DDL, a catalog CSV or a comparison YAML, use `scripts/import_cli.py` before writing a source by hand. The importer converts the file to the native contract and calls the same generators and gates of this skill:

```bash
python3 <skill>/scripts/import_cli.py process.mmd --out diagrams --lang pt-BR
python3 <skill>/scripts/import_cli.py schema.sql --type matrix --out diagrams --lang pt-BR
```

With the CLI installed, `ai-diagrams import` accepts the same arguments. The extension and the header pick the format; `--type` selects the output when needed, such as `er` or `matrix` for SQL. Mermaid `flowchart`/`graph` without `subgraph` becomes BPMN; `subgraph` stands for a lane, not a generic grouping. `sequenceDiagram`, `stateDiagram-v2` and `erDiagram` become sequence, states and ER. The layout is recomputed by the engine.

Read `references/import.md` for the accepted subset. `MERMAID-UNSUPPORTED` or `BPMN-UNSUPPORTED` says what needs to be adapted; never drop the rejected statement to fake success. The importer does not translate authored content. In an environment without Chrome, `--source-only` prepares the source and declares the full gate and the PNG as pending; this does not replace validation or the visual audit. The default is still to generate and run the full gate.

### Dependencies

1. `pip3 install diagrams`: only the collection of official AWS icons in PNG; the library never runs.
2. Google Chrome: build, lint and capture use headless mode.
3. Node 18 or newer, for the ER, matrix and state machine generators.
4. Overrides if needed: `POSTER_CHROME` (Chrome path) and `POSTER_ICONBASE` (the `resources/aws` folder).

## 3. Working layout

In the user's project, sources go in `diagrams/_src/`, deliverables (self-contained HTML, PNG and, for BPMN, the `.bpmn`) in the parent folder `diagrams/`. Create the structure if it does not exist. The scripts use the project's CSS (`_src/_style.css`, `_src/_style-conceptual.css`) when it exists; otherwise, the skill's.

## 4. Cycle common to every type

1. **Content before drawing.** The diagram materializes a decision document, a described process or a data model. Read the source or ask what it is. Without a written source, draft the narrative with the user first.
2. **Source.** Start from the type's template in `templates/` and read the type's reference before writing.
3. **Gate at zero.** Run the type's command (below). A gate with problems does not generate the PNG; fix the source and run it again.
   - Run the command as written here, without a pipe (`|`), redirection (`2>&1`, `>`) or `&&`: some environments only allow the plain command.
   - Do not create a helper script and do not copy or edit the skill's CSS in the project (`_style.css`, `_style-conceptual.css`). Width, font and grid already come right; changing the CSS is the most common cause of `TEXT-TOO-SMALL`.
   - Do not embed fonts, icons or images in base64 in the source: `build.py` does that in the final HTML. The source keeps `/*STYLE*/`, `aws://` and the Google Fonts link.
   - If the gate gives `MEASURE-FAILED` or Chrome does not respond, the cause is usually a sandbox that blocks Chrome (Codex with `workspace-write`, for example). Ask for the command to be run outside the sandbox; do not work around the gate.
   - **A failed gate is not a delivery.** Never say you are done while the gate fails. If the gate still fails after five rounds of fixes, stop and deliver the source, the output of the last gate and the sentence "the gate failed; the PNG was not generated" (in the user's language).
4. **Visual audit (mandatory).** Read the PNG with the Read tool and critique it: text cut or squeezed, a label touching another, an arrow stuck to another or crossing a box, footer cut, dead area, confusing hierarchy. The gate measures geometry, not reading. Fix and repeat 3 and 4 until it passes clean. Never deliver without looking at the PNG.
5. **Delivery.** Source, final HTML and PNG together (for BPMN, also the `.bpmn`).

In a batch, do the whole cycle for one diagram before starting the next.

### Legibility beats the default size

The default width (1760px on the poster, 1400px on the conceptual page) and the template measurements exist to standardize, not to squeeze. If the drawing is not legible at them, increase what is needed: the page width (the source declares `<meta name="width" content="N">` and `build.py` captures at that width; the ER diagram already does this from the layout canvas), the height, the size of the boxes or the space between them. No element leaves the frame or goes past the edge of another block on the page: legend, bands and drawing align on the same width.

### Request options: client, footer and version

Before drawing, check whether the request says if the client name appears in the diagram. If it does not, ask in a single message, with the two options:

1. **with client**: header `<Project> · <subject> · <Client>`, and say what the name is;
2. **without client**: header `<Project> · <subject>`.

`<Project>` is the name of the team, product or organization the user gives. If they do not give one, the header starts directly with `<subject>`.

In the same question, confirm the footer (default `<Project> · <diagram type> · YYYY-MM`, or only `<diagram type> · YYYY-MM` without a project) and the version (default `V1`), offering the default. If the request already states client, footer and version, or says "no client in the header", do not ask.

**User texts.** If the user gives a title, subtitle, kicker, section texts or band texts, use the literal text, without rewriting it. In the question above, say they can send these texts; if they do not, the skill writes them.

Never infer the client, the author or the version from the folder path, the repository name or another file in the project: only what the user or the diagram's source says counts.

When there is no way to ask (non-interactive run, such as `claude -p` or Kiro without interaction, or use through a knowledge base), go on without a client, with the default footer and version, and say so in the delivery.

### Label language

Use `--lang <pt-BR|en|es>` on the generator and on the gate for the fixed labels. The selection follows this priority: flag, `<meta name="lang" content="…">` in the HTML or the `lang` field in the JSON/ER layout, the `AI_DIAGRAMS_LANG` variable, default `pt-BR`. In the ER diagram, the layout field takes precedence over the model's. The catalogs `i18n/pt-BR.json`, `en.json` and `es.json` have the same keys; an unknown language fails with `LANG-NOT-FOUND` and a missing key with `LANG-INCOMPLETE`. Title, subtitle, boxes, notes and other authored content come from the source and must be written in the requested language. With no language selected, the Portuguese output keeps text and geometry byte for byte. The gates identify sections by class, without depending on the translated text.

### Theme: color and font

The theme is a JSON file with colors and fonts. The skill ships `themes/ai-diagrams.json` (default) and `themes/paper.json` (cream paper, brown ink, Public Sans). Every command accepts `--theme <name or path.json>`: a name resolves to `themes/<name>.json` of this skill; a path points to a JSON file in any folder.

1. **The user names a theme or passes a JSON file:** use it with `--theme` on every command of the diagram, generator and gate.
2. **The project already has a theme** (`diagrams/_src/theme.json`, or the `AI_DIAGRAMS_THEME` variable is set): use it without asking, with `--theme diagrams/_src/theme.json`.
3. **Neither:** include the theme in the same question about client, footer and version, offering the default `ai-diagrams` and the names that exist in `themes/`. With no way to ask, go on with the default.

To create the user's theme (brand color, another font family), copy `themes/ai-diagrams.json` to `diagrams/_src/theme.json` in the project and change only the values: every key in `colors`, `derived`, `er_palette` and `fonts` stays. Color as `#RRGGBB`; a font is a Google Fonts family name. Never change color or font by editing the CSS. A theme with a missing key fails with `THEME-INCOMPLETE: missing <group>.<key>`: complete the JSON, do not work around it. The generator writes the chosen theme into the source (`<meta name="theme">`), and the gate uses that theme when it does not receive `--theme`. Changing the theme does not change the geometry: do not touch coordinates because of it.

### Text register

The text that opens the diagram only serves to place the reader in the drawing. It is strictly technical:

- **Title:** the technical name of the system, flow or decision, with the scope when it helps ("API de pagamentos e extrato assíncrono", "schema conta · Contas e movimentos"). Never a thesis, promise or conclusion.
- **Subtitle:** one to three sentences that say what the drawing shows, the scope (what is inside and what was left out) and how to read it (order of the steps, what the color or the lane means). A number only if it is in the source.
- **Closing band** (conceptual): a fact about the flow or what was left out of the drawing, not a sales conclusion.
- Forbidden: value adjectives, promises, benefits, metaphors, catchphrases and antitheses. The gate fails these terms with `MARKETING-COPY` (list in `scripts/technical_text.py`); what the list does not catch, you check when reading the PNG. Technical terms in English as the market uses them (bucket, dead-letter topic, consumer group, deploy); no invented translations. Box text short; the explanation goes in the steps or the sections.

**Color and font only from the theme.** The source never writes hexadecimal or `rgb()`, not even in a local style: it uses `var(--ink)`, `var(--support)`, `var(--muted)`, `var(--zone)`, `var(--paper)`, `var(--accent)`, `var(--risk)` and `var(--risk-bg)`, which the gate declares in `:root` with the values of the chosen theme. Font only through `var(--font-text)` and `var(--font-mono)`; a family written in the source fails with `FONT-OUTSIDE-THEME`. In SVG the color goes in `style` (`style="stroke:var(--support)"`), because the `stroke` and `fill` attributes do not accept `var()`. The gate fails a literal color with `COLOR-OUTSIDE-THEME`.

## 5. Commands per type

`<skill>` is this skill's folder. With a chosen theme, add `--theme <name or path.json>` to each command below (section "Theme: color and font").

**Poster, flow with steps and table**
```bash
python3 <skill>/scripts/poster_lint.py --fix diagrams/_src/NN-name.html
python3 <skill>/scripts/build.py diagrams/_src/NN-name.html
```
The build measures the real page height and captures at it; if it receives a height smaller than the page, it fails with `CROPPED`. The width is 1760px, or the one in the source's `<meta name="width">`; content that goes past it fails with `OVERFLOW`. Poster rules that avoid rework:

- Plan the grid first: columns per layer, rows per actor. Do the math for the arrowheads, corridors and badges with the "Coordinate recipe" in `references/visual-language.md`.
- Run `poster_lint.py --fix` before the build: it snaps detached arrowheads and moves badges onto the arrow; then run it without `--fix` and fix the rest with the coordinates it suggests.
- Orthogonal arrows (`path` with `H`/`V`); the arrowhead touches the target box. In a `.node`, the solid box is the 44px icon: a vertical arrow never crosses the label below it.
- Two arrows never run on the same line: use corridors between the columns.
- Each step has a badge on the line of its own arrow and an item in `.passos`.
- Icons as `aws://category/file.png`, with the name checked in the icon collection.

The lint fails `DETACHED`, `CROSSES`, `COLLINEAR`, `NO-BADGES`, `NO-STEPS`, `STEPS-MISMATCH`, `BADGE-DETACHED`, `OVERLAP`, `ARROW-OVER-TEXT`, `INSIDE-BOX`, `TEXT-OVER-EDGE`, `ARROW-ON-EDGE`, `LABEL-DETACHED`, `ARROWHEAD-INSIDE`, `OVERFLOW`, `MARKETING-COPY` and `NO-STYLE`; `OVERLAP`, `ARROW-OVER-TEXT`, `TEXT-OVER-EDGE`, `ARROW-ON-EDGE`, `LABEL-DETACHED`, `ARROWHEAD-INSIDE` and `OVERFLOW` are measured in Chrome. Dead area (a zone much larger than its content) is not measured by the gate: check it in the PNG and shrink the zone. A document without `<svg class="edges">` (table, matrix) does not require badges or steps. In C4 (`references/c4.md`), `C4-NO-TYPE` and `C4-NO-LEGEND` also apply; a C4 page drawn by `build_c4.py` carries a `.rel` label on each arrow instead of badges and steps, checked by `C4-REL-MISSING`, `C4-REL-INCOMPLETE` and `C4-REL-DETACHED`.

**Swimlanes and conceptual**
```bash
python3 <skill>/scripts/build_swimlanes.py diagrams/_src/NN-flow.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-flow.html
```
The first command only exists for swimlanes; cards and panels are HTML written by hand from template 07.

**Sequence**
```bash
python3 <skill>/scripts/build_sequence.py diagrams/_src/NN-name.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-name.html
```
Besides the conceptual rules, it fails `TEXT-OVER-LIFELINE` (a label on top of a lifeline or activation bar).

**State machine**
```bash
python3 <skill>/scripts/build_states.py diagrams/_src/NN-name.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-name.html
```
The generator uses `node` (elkjs in `states/`) and fails before drawing: `NO-INITIAL`, `UNKNOWN`, `NO-EVENT`, `LEAVES-FINAL`, `UNREACHABLE` and `NO-EXIT`.

**BPMN**
```bash
python3 <skill>/bpmn/build_bpmn.py diagrams/_src/NN-process.json
```

**ER diagram and matrix**
```bash
node <skill>/er/er-build.mjs diagrams/_src/er-<schema>.layout.mjs
python3 <skill>/scripts/build.py diagrams/_src/er-<schema>.html
node <skill>/er/er-overview.mjs diagrams/_src/model.json
python3 <skill>/scripts/build.py diagrams/_src/er-overview.html
```
The ER diagram is not drawn box by box: the content of each table comes from `model.json`, and only the position and the lane of each arrow are decided by hand in the layout.
