# How it works

This page describes the pipeline behind the skill: what each script does, why there is no layout engine, and how each gate decides that a diagram fails. To install and draw a first diagram, see [install.md](install.md).

## 1. No layout engine

ai-diagrams does not use a diagramming tool or an auto-layout algorithm. The AI writes every source by hand, or writes a JSON spec that a script turns into coordinates. Posters and step flows are HTML files with absolute positions in pixels and arrows in SVG. Layout is a decision of whoever draws, not the output of a generic algorithm.

The scripts turn that source into deliverables and reject defects on the way:

```
diagramas/_src/NN-name.html   (source, edited by hand)
        │
        ├── poster_lint.py   → checks arrows, badges, steps and overlap (--fix snaps loose ends)
        └── build.py         → runs the lint, inlines CSS and icons, screenshots with headless Chrome
                ├── diagramas/NN-name.html  (self-contained, opens in any browser)
                └── diagramas/NN-name.png   (1760px wide, scale 1.5)
```

The ER diagram and the dependency matrix add one step in front. A Node script writes the HTML source from the logical model, and the rest of the pipeline is the same:

```
modelo.json + der-<schema>.layout.mjs → der-montar.mjs      → der-<schema>.html     → build.py → PNG
modelo.json                           → der-visao-geral.mjs → der-visao-geral.html  → build.py → PNG
```

Swimlanes, cards, sequence diagrams and state machines use their own gate:

```
spec.json → gerar_raias.py     → NN-flow.html → conceitual.py (lint measured in Chrome + capture) → PNG
NN-catalog.html (by hand)                     → conceitual.py                                     → PNG
spec.json → gerar_sequencia.py → NN-name.html → conceitual.py                                     → PNG
spec.json → gerar_estados.py (elkjs) → NN-name.html → conceitual.py                               → PNG
```

The C4 container diagram uses the poster pipeline (`build.py`).

BPMN comes from a JSON model and is rendered by bpmn-js:

```
modelo.json → gerar_bpmn.py → .bpmn (editable) + HTML viewer + PNG
```

## 2. The eleven types and their gates

| Type | Reference model | Source | Gate |
|---|---|---|---|
| AWS architecture poster | `skills/ai-diagrams/modelos/01-arquitetura-aws/` | HTML by hand | `build.py` (runs `poster_lint.py`) |
| Numbered-step flow | `skills/ai-diagrams/modelos/02-fluxo-passos/` | HTML by hand | `build.py` |
| ER diagram per schema | `skills/ai-diagrams/modelos/03-der-schema/` | `modelo.json` + layout | `der-montar.mjs`, then `build.py` |
| Schema dependency matrix | `skills/ai-diagrams/modelos/04-matriz-dependencia/` | `modelo.json` | `der-visao-geral.mjs`, then `build.py` |
| Comparison table | `skills/ai-diagrams/modelos/05-tabela-comparacao/` | HTML by hand | `build.py` |
| Swimlanes | `skills/ai-diagrams/modelos/06-raias/` | JSON spec | `gerar_raias.py`, then `conceitual.py` |
| Cards catalog | `skills/ai-diagrams/modelos/07-catalogo-cards/` | HTML by hand | `conceitual.py` |
| BPMN 2.0 | `skills/ai-diagrams/modelos/08-bpmn/` | JSON model | `gerar_bpmn.py` |
| Sequence diagram | `skills/ai-diagrams/modelos/09-sequencia/` | JSON spec | `gerar_sequencia.py`, then `conceitual.py` |
| State machine | `skills/ai-diagrams/modelos/10-maquina-estados/` | JSON spec | `gerar_estados.py`, then `conceitual.py` |
| C4 (context and containers) | `skills/ai-diagrams/modelos/11-c4/` | HTML by hand | `build.py` |

Each model folder has the source in `_src/` and the generated PNG. `skills/ai-diagrams/modelos/gerar.sh` rebuilds all eleven through their gates.

The router in `skills/ai-diagrams/SKILL.md` picks the type from the request.

## 3. Requirements

| Item | Role |
|---|---|
| Google Chrome | renders the PNG and measures overlap in headless mode |
| Python 3.9+ | runs `build.py`, the lints and the generators |
| `diagrams` pip package | provides the official AWS icons as PNG; the library itself never runs |
| Node 18+ | runs the ER and matrix generators and the elkjs layout of the state machine |
| Network access at render time | the IBM Plex Sans and IBM Plex Mono fonts load from Google Fonts |

`build.py` finds the icons in `<site-packages>/resources/aws` and Chrome in the usual macOS and Linux locations. To use other locations, export `POSTER_ICONBASE` or `POSTER_CHROME`.

## 4. The scripts

Program output and defect codes are in Portuguese. This page quotes them as printed.

### `skills/ai-diagrams/scripts/build.py`

```bash
python3 build.py <source.html> [height-px] [--out DIR]
```

1. Stops with `SEM-ESTILO` if the source has no `/*ESTILO*/` marker. Otherwise injects the CSS at the marker. It uses `_estilo.css` or `estilo.css` from the source folder if present, otherwise `skills/ai-diagrams/assets/estilo.css`.
2. Replaces each `aws://category/file.png` with the icon PNG in base64.
3. Runs the full lint.
4. Calls Chrome only if the lint passes.

A missing icon or any lint issue stops the build, and nothing is written. When the source is in `_src/`, the output goes to the parent folder. The capture is 1760px wide at scale 1.5, unless the source declares another width in `<meta name="largura">`. If the page is taller than the capture, the build fails with `CORTADO` (cut).

### `skills/ai-diagrams/scripts/poster_lint.py`

```bash
python3 poster_lint.py [--fix] [--static] source.html [...]
```

Reads the source and checks:

1. Both ends of every arrow touch a box or a frame border (tolerance 6px). Between 6 and 60px along the segment, `--fix` snaps the end.
2. No arrow segment crosses a box that is not its endpoint (`ATRAVESSA`). Two different arrows never run on the same line (`COLINEAR`).
3. Badges 1..N on the canvas match the items in `.passos` (`SEM-BADGES`, `SEM-PASSOS`, `PASSOS-DIVERGEM`).
4. The center of each badge sits on an arrow line (`BADGE-SOLTO`).
5. Measured in Chrome: badges, labels, icons and chips do not overlap (`SOBREPOE`), and no arrow passes over text (`SETA-SOBRE-TEXTO`), including the text inside boxes. No arrow runs along a frame border (`SETA-NA-BORDA`), every edge label sits within 30px of an arrow (`ROTULO-SOLTO`) and no arrowhead ends in the middle of a box (`PONTA-DENTRO`). `--static` skips this check.
6. Measured in Chrome: nothing goes past the right edge of the page, where the capture cuts (`TRANSBORDA`).
7. Title, subtitle, kicker and bands use technical wording, without marketing vocabulary (`TEXTO-MARKETING`). The word list is in `skills/ai-diagrams/scripts/texto_tecnico.py`.
8. In a C4 diagram, every `.bchip.c4` has a type (`.bn`) and a name (`.bt`), and the page has the `.c4leg` legend (`C4-SEM-TIPO`, `C4-SEM-LEGENDA`). The format is in `skills/ai-diagrams/references/c4.md`.
9. Colors come only from the theme: a hex, `rgb()` or `hsl()` literal in the source fails with `COR-FORA-DO-TEMA` (see section 5).

A document without `<svg class="edges">`, such as the matrix, skips checks 3 and 4. If Chrome cannot run, the measured checks report `MEDICAO-FALHOU` (measurement failed). Exit code 1 on any issue.

### `skills/ai-diagrams/der/der-tabelas.mjs`, `der-montar.mjs`, `der-visao-geral.mjs`

- `der-tabelas.mjs` loads the model and builds the HTML of each table box: header in the color of the table type, name, description, and one row per column with a PK, FK or UQ mark.
- `der-montar.mjs` reads the layout file, places the boxes, draws orthogonal arrows with crow's-foot ends, and adds the domain band, the boundary with other schemas and the fixed legend.
- `der-visao-geral.mjs` counts foreign keys between schemas and builds the matrix.

The model and layout format is in `skills/ai-diagrams/references/der.md`.

### `skills/ai-diagrams/scripts/gerar_raias.py` and `conceitual.py`

`gerar_raias.py` computes the coordinates of a swimlane flow from JSON (a lane is a row, a phase is a column) and writes the HTML.

`conceitual.py` injects `skills/ai-diagrams/assets/estilo-conceitual.css`, measures the real page height and every box in Chrome, and only then captures the PNG. It rejects:

| Code | Defect |
|---|---|
| `TRANSBORDA` | content larger than its box (text cut or squeezed) |
| `SOBREPOE` | two content boxes intersect |
| `FORA-DA-PAGINA` | element goes past the body width or out on the left |
| `FORA-DO-CANVAS` | element inside `.canvas` goes past the canvas frame |
| `TEXTO-MINIMO` | text below the minimum readable size at display width |
| `ROTULO-SOBRE-CAIXA` | loose label covering a content box it does not belong to |
| `SETA-SOLTA` | arrow end that touches no box (tolerance 6px) |
| `SETA-SOBRE-TEXTO` | arrow segment crossing a text box |
| `COLINEAR` | two different arrows on the same line |
| `TEXTO-MARKETING` | marketing vocabulary in title, subtitle, kicker or bands |

On success it prints `lint 0` and two `OK` lines. `--so-lint` runs the checks without capturing. The format is in `skills/ai-diagrams/references/raias.md`.

### `skills/ai-diagrams/scripts/gerar_sequencia.py`

Computes the coordinates of a sequence diagram from JSON (a participant is a column, a message is a row). Gap width follows the label length. Activation bars follow call and response. Frames cover `alt`, `loop` and `opt`. The gate is `conceitual.py`, which also rejects `TEXTO-SOBRE-VIDA` (text over a lifeline) in sequence diagrams. The format is in `skills/ai-diagrams/references/sequencia.md`.

### `skills/ai-diagrams/scripts/gerar_estados.py`

Before drawing, checks the state graph and rejects `SEM-INICIAL` (no initial state), `DESCONHECIDO` (transition to an unknown state), `SEM-EVENTO` (transition without an event), `SAI-DO-FINAL` (transition out of a final state), `INALCANCAVEL` (state not reachable) and `SEM-SAIDA` (non-final state without an exit). Then it sends states and transitions to elkjs 0.12.0 (`skills/ai-diagrams/estados/elk-layout.cjs`, vendored in `skills/ai-diagrams/estados/vendor/` with its license and sha256). elkjs only returns positions and orthogonal routes; the script draws the boxes, the double border of final states, loops and `event [guard] / action` labels. The gate is `conceitual.py`. The format is in `skills/ai-diagrams/references/estados.md`.

### `skills/ai-diagrams/bpmn/gerar_bpmn.py`

```bash
python3 gerar_bpmn.py <modelo.json> [--out DIR] [--so-bpmn]
```

Reads a JSON model (lanes, nodes with column and row, connections), places the shapes and routes the connections in Manhattan style around shapes and labels. It writes BPMN 2.0 with BPMNDI, a self-contained bpmn-js viewer and a PNG. The gate rejects with `BPMN REPROVOU` and writes nothing:

| Check | Defect |
|---|---|
| `ESTRUTURA` | duplicate ids, connection to a missing node, node without input (except start) or output (except end), decision branch without a label |
| `ALCANCE` | node not reachable from a start, or that cannot reach an end |
| `SOBREPOSICAO` | two shapes in the same place |
| `IMPORTACAO` | bpmn-js reports an error or warning when importing the XML in Chrome |
| `TEXTO-MARKETING` | marketing vocabulary in title or subtitle |

The bpmn-js bundle is in `skills/ai-diagrams/bpmn/vendor/`, with its license in `skills/ai-diagrams/bpmn/vendor/LICENSE`. The format is in `skills/ai-diagrams/references/bpmn.md`.

## 5. Theme

Every color is a token. The values live in `skills/ai-diagrams/temas/ai-diagrams.json` and are declared in the `:root` block of `skills/ai-diagrams/assets/estilo.css` and `estilo-conceitual.css` (and in the `TEMA` dictionary of `gerar_bpmn.py`). Sources and generators use only `var(--token)`: `--tinta` (main text), `--apoio` (secondary text and arrows), `--cinza`, `--zona`, `--papel`, `--acento`, `--risco` on `--risco-fundo`, plus the C4 and ER tokens. In SVG the color goes in `style` (`style="stroke:var(--apoio)"`), because the `stroke` and `fill` attributes do not accept `var()`. `python3 skills/ai-diagrams/scripts/conferir_tema.py` checks that the CSS and the generators match the theme file (`TOKEN-DIVERGE`) and that no literal color is left outside the theme (`COR-FORA-DO-TEMA`). To change the look, edit the theme file and the matching `:root` values, then run it.


`skills/ai-diagrams/assets/estilo.css` is the single stylesheet for posters, flows, tables, ER diagrams and the matrix. The build injects it. Main classes:

| Class | Element |
|---|---|
| `.page`, `.hdr`, `.kicker`, `.sub`, `.foot` | page frame: header, subtitle, footer |
| `.canvas` | drawing area with `position:relative`; everything inside is absolute |
| `.frame` (`awscloud`, `region`, `account`, `zone`, `ext`) | containers, labeled with `.flabel` |
| `.node` | AWS service with a 44px icon, name and role |
| `.svc`, `.oss`, `.chip`, `.bchip` | compact boxes: service, open source, concept and reference chip |
| `.badge`, `.elabel` | step number on an arrow and edge label |
| `.passos`, `.pitem`, `.ptitle` | numbered step list |
| `.wrap.stack` | steps in three columns below a 1700px canvas |

`skills/ai-diagrams/assets/estilo-conceitual.css` is the stylesheet for swimlanes, cards, sequence diagrams and state machines. The ER diagram adds local CSS for table boxes, band, boundary and legend, generated by `der-tabelas.mjs`.

## 6. Work cycle

1. **Content first.** Content comes from a decision document, a process description or a data model.
2. **The AI writes the source** in `diagramas/_src/`: frames, boxes, orthogonal arrows and the page frame. For an ER diagram, it writes `modelo.json` and the layout file. For swimlanes, sequence, state machine and BPMN, it writes the JSON spec.
3. **Gate.** The type's command runs the lint and builds the PNG only when the lint passes.
4. **Visual check.** The AI opens the PNG and looks for overlap, cut text, arrows crossing boxes, a cut footer and empty areas. It fixes the source and repeats steps 3 and 4.
5. **Stop rule.** If the gate does not pass after five rounds, the AI delivers the source and the last gate output, and says that the gate failed.
6. **Commit** the source, the final HTML and the PNG.

## 7. File names

| Pattern | Content |
|---|---|
| `NN-name.html` / `.png` | poster, flow, table, swimlanes, cards, sequence, state machine, C4 |
| `NN-name.json` | spec for swimlanes, sequence, state machine or BPMN |
| `NN-name.bpmn` | editable BPMN 2.0 file |
| `der-<schema>.html` / `.png`, `der-<schema>.layout.mjs` | ER diagram of one schema and its layout |
| `der-visao-geral.html` / `.png` | dependency matrix between schemas |
| `modelo.json` | logical model shared by the ER diagram and the matrix |
