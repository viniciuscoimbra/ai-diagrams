# How it works

This page describes the pipeline behind the skill: what each script does, why there is no layout engine, and how each gate decides that a diagram fails. To install and draw a first diagram, see [install.md](install.md).

## 1. No layout engine

ai-diagrams does not use a diagramming tool or an auto-layout algorithm. The AI writes every source by hand, or writes a JSON spec that a script turns into coordinates. Posters and step flows are HTML files with absolute positions in pixels and arrows in SVG. Layout is a decision of whoever draws, not the output of a generic algorithm.

The scripts turn that source into deliverables and reject defects on the way:

```
diagrams/_src/NN-name.html   (source, edited by hand)
        │
        ├── poster_lint.py   → checks arrows, badges, steps and overlap (--fix snaps loose ends)
        └── build.py         → runs the lint, inlines CSS and icons, screenshots with headless Chrome
                ├── diagrams/NN-name.html  (self-contained, opens in any browser)
                └── diagrams/NN-name.png   (1760px wide, scale 1.5)
```

The ER diagram and the dependency matrix add one step in front. A Node script writes the HTML source from the logical model, and the rest of the pipeline is the same:

```
model.json + er-<schema>.layout.mjs → er-build.mjs    → er-<schema>.html   → build.py → PNG
model.json                          → er-overview.mjs → er-overview.html   → build.py → PNG
```

Swimlanes, cards, sequence diagrams and state machines use their own gate:

```
spec.json → build_swimlanes.py     → NN-flow.html → conceptual.py (lint measured in Chrome + capture) → PNG
NN-catalog.html (by hand)                     → conceptual.py                                     → PNG
spec.json → build_sequence.py → NN-name.html → conceptual.py                                     → PNG
spec.json → build_states.py (elkjs) → NN-name.html → conceptual.py                               → PNG
```

C4 comes from one JSON model: `build_c4.py` derives each view (landscape, context, containers, components, dynamic, deployment), lays it out with elkjs, and builds each page through the poster pipeline (`build.py`).

BPMN comes from a JSON model and is rendered by bpmn-js:

```
model.json → build_bpmn.py → .bpmn (editable) + HTML viewer + PNG
```

## 2. The eleven types and their gates

| Type | Reference model | Source | Gate |
|---|---|---|---|
| AWS architecture poster | `skills/ai-diagrams/templates/01-aws-architecture/` | HTML by hand | `build.py` (runs `poster_lint.py`) |
| Numbered-step flow | `skills/ai-diagrams/templates/02-step-flow/` | HTML by hand | `build.py` |
| ER diagram per schema | `skills/ai-diagrams/templates/03-er-schema/` | `model.json` + layout | `er-build.mjs`, then `build.py` |
| Schema dependency matrix | `skills/ai-diagrams/templates/04-dependency-matrix/` | `model.json` | `er-overview.mjs`, then `build.py` |
| Comparison table | `skills/ai-diagrams/templates/05-comparison-table/` | HTML by hand | `build.py` |
| Swimlanes | `skills/ai-diagrams/templates/06-swimlanes/` | JSON spec | `build_swimlanes.py`, then `conceptual.py` |
| Cards catalog | `skills/ai-diagrams/templates/07-card-catalog/` | HTML by hand | `conceptual.py` |
| BPMN 2.0 | `skills/ai-diagrams/templates/08-bpmn/` | JSON model | `build_bpmn.py` |
| Sequence diagram | `skills/ai-diagrams/templates/09-sequence/` | JSON spec | `build_sequence.py`, then `conceptual.py` |
| State machine | `skills/ai-diagrams/templates/10-state-machine/` | JSON spec | `build_states.py`, then `conceptual.py` |
| C4 (all views) | `skills/ai-diagrams/templates/11-c4/` | JSON model | `build_c4.py`, which runs `build.py` per view |

Each model folder has the source in `_src/` and the generated PNG. `skills/ai-diagrams/templates/build-all.sh` rebuilds all eleven through their gates.

The router in `skills/ai-diagrams/SKILL.md` picks the type from the request.

## 3. Requirements

| Item | Role |
|---|---|
| Google Chrome | renders the PNG and measures overlap in headless mode |
| Python 3.9+ | runs `build.py`, the lints and the generators |
| `diagrams` pip package | provides the official AWS icons as PNG; the library itself never runs |
| Node 18+ | runs the ER and matrix generators and the elkjs layout of the state machine |
| Network access at render time | the theme fonts load from Google Fonts (IBM Plex Sans and IBM Plex Mono in the default theme) |

`build.py` finds the icons in `<site-packages>/resources/aws` and Chrome in the usual macOS and Linux locations. To use other locations, export `POSTER_ICONBASE` or `POSTER_CHROME`.

## 4. The scripts

### `skills/ai-diagrams/scripts/build.py`

```bash
python3 build.py <source.html> [height-px] [--out DIR] [--theme NAME|path.json]
```

1. Stops with `NO-STYLE` if the source has no `/*STYLE*/` marker (the 0.1 marker `/*ESTILO*/` is still read). Otherwise injects the CSS at the marker. It uses `_style.css` or `style.css` from the source folder if present, otherwise `skills/ai-diagrams/assets/style.css`. The token `:root` of that CSS is replaced by the one of the selected theme, and the Google Fonts link of the source by the one of the theme families (section 5).
2. Replaces each `aws://category/file.png` with the icon PNG in base64.
3. Runs the full lint.
4. Calls Chrome only if the lint passes.

A missing icon or any lint issue stops the build, and nothing is written. When the source is in `_src/`, the output goes to the parent folder. The capture is 1760px wide at scale 1.5, unless the source declares another width in `<meta name="width">`. If the page is taller than the capture, the build fails with `CROPPED`.

### `skills/ai-diagrams/scripts/poster_lint.py`

```bash
python3 poster_lint.py [--fix] [--static] source.html [...]
```

Reads the source and checks:

1. Both ends of every arrow touch a box or a frame border (tolerance 6px). Between 6 and 60px along the segment, `--fix` snaps the end.
2. No arrow segment crosses a box that is not its endpoint (`CROSSES`). Two different arrows never run on the same line (`COLLINEAR-V`, `COLLINEAR-H`).
3. Badges 1..N on the canvas match the items in `.passos` (`NO-BADGES`, `NO-STEPS`, `STEPS-MISMATCH`).
4. The center of each badge sits on an arrow line (`BADGE-DETACHED`).
5. Measured in Chrome: badges, labels, icons and chips do not overlap (`OVERLAP`), and no arrow passes over text (`ARROW-OVER-TEXT`), including the text inside boxes. No arrow runs along a frame border (`ARROW-ON-EDGE`), every edge label sits within 30px of an arrow (`LABEL-DETACHED`) and no arrowhead ends in the middle of a box (`ARROWHEAD-INSIDE`). `--static` skips this check.
6. Measured in Chrome: nothing goes past the right edge of the page, where the capture cuts (`OVERFLOW`).
7. Title, subtitle, kicker and bands use technical wording, without marketing vocabulary (`MARKETING-COPY`). The word list is in `skills/ai-diagrams/scripts/technical_text.py`.
8. In a C4 diagram, every `.bchip.c4` has a type (`.bn`) and a name (`.bt`), and the page has the `.c4leg` legend (`C4-NO-TYPE`, `C4-NO-LEGEND`). A C4 page drawn from the model has one `.rel` label per arrow, with what it does and the technology, on or within 14px of its own arrow (`C4-REL-MISSING`, `C4-REL-INCOMPLETE`, `C4-REL-DETACHED`); it needs no badges. The format is in `skills/ai-diagrams/references/c4.md`.
9. Colors and fonts come only from the theme: a hex, `rgb()` or `hsl()` literal in the source fails with `COLOR-OUTSIDE-THEME`, and a `font-family` with a literal family name fails with `FONT-OUTSIDE-THEME` (see section 5).

A document without `<svg class="edges">`, such as the matrix, skips checks 3 and 4. If Chrome cannot run, the measured checks report `MEASURE-FAILED`. Exit code 1 on any issue.

### `skills/ai-diagrams/er/er-tables.mjs`, `er-build.mjs`, `er-overview.mjs`

- `er-tables.mjs` loads the model and builds the HTML of each table box: header in the color of the table type, name, description, and one row per column with a PK, FK or UQ mark.
- `er-build.mjs` reads the layout file, places the boxes, draws orthogonal arrows with crow's-foot ends, and adds the domain band, the boundary with other schemas and the fixed legend.
- `er-overview.mjs` counts foreign keys between schemas and builds the matrix.

The model and layout format is in `skills/ai-diagrams/references/er.md`.

### `skills/ai-diagrams/scripts/build_swimlanes.py` and `conceptual.py`

`build_swimlanes.py` computes the coordinates of a swimlane flow from JSON (a lane is a row, a phase is a column) and writes the HTML.

`conceptual.py` injects `skills/ai-diagrams/assets/style-conceptual.css`, measures the real page height and every box in Chrome, and only then captures the PNG. It rejects:

| Code | Defect |
|---|---|
| `OVERFLOW-X`, `OVERFLOW-Y` | content larger than its box (text cut or squeezed) |
| `OVERFLOW-PAGE` | document wider than the page; the capture cuts the right side |
| `OVERLAP` | two content boxes intersect |
| `OFF-PAGE` | element goes past the body width or out on the left |
| `OFF-CANVAS` | element inside `.canvas` goes past the canvas frame |
| `TEXT-TOO-SMALL` | text below the minimum readable size at display width |
| `LABEL-OVER-BOX` | loose label covering a content box it does not belong to |
| `ARROW-DETACHED` | arrow end that touches no box (tolerance 6px) |
| `ARROW-OVER-TEXT` | arrow segment crossing a text box |
| `COLLINEAR-V`, `COLLINEAR-H` | two different arrows on the same line |
| `MARKETING-COPY` | marketing vocabulary in title, subtitle, kicker or bands |
| `COLOR-OUTSIDE-THEME`, `FONT-OUTSIDE-THEME` | literal color or font family in the source |

On success it prints `lint 0` and two `OK` lines. `--lint-only` runs the checks without capturing. The format is in `skills/ai-diagrams/references/swimlanes.md`.

### `skills/ai-diagrams/scripts/build_sequence.py`

Computes the coordinates of a sequence diagram from JSON (a participant is a column, a message is a row). Gap width follows the label length. Activation bars follow call and response. Frames cover `alt`, `loop` and `opt`. The gate is `conceptual.py`, which also rejects `TEXT-OVER-LIFELINE` in sequence diagrams. The format is in `skills/ai-diagrams/references/sequence.md`.

### `skills/ai-diagrams/scripts/build_states.py`

Before drawing, checks the state graph and rejects `NO-INITIAL` (no initial state), `UNKNOWN` (transition to an unknown state), `NO-EVENT` (transition without an event), `LEAVES-FINAL` (transition out of a final state), `UNREACHABLE` (state not reachable), `NO-EXIT` (non-final state without an exit), `WIDTH-INVALID` (state width that is not an integer above 34) and `NAME-TOO-LONG` (state name that does not fit on one line). Each failure prints `STATES FAILED <code>: <detail>`. Then it sends states and transitions to elkjs 0.12.0 (`skills/ai-diagrams/states/elk-layout.cjs`, vendored in `skills/ai-diagrams/states/vendor/` with its license and sha256). elkjs only returns positions and orthogonal routes; the script draws the boxes, the double border of final states, loops and `event [guard] / action` labels. The gate is `conceptual.py`. The format is in `skills/ai-diagrams/references/states.md`.

### `skills/ai-diagrams/bpmn/build_bpmn.py`

```bash
python3 build_bpmn.py <model.json> [--out DIR] [--bpmn-only] [--theme NAME|path.json] [--lang pt-BR|en|es] [--no-chrome]
```

Reads a JSON model (lanes, nodes with column and row, connections), places the shapes and routes the connections in Manhattan style around shapes and labels. It writes BPMN 2.0 with BPMNDI, a self-contained bpmn-js viewer and a PNG. The gate rejects with `BPMN FAILED` and writes nothing:

| Check | Defect |
|---|---|
| `STRUCTURE` | duplicate ids, connection to a missing node, node without input (except start) or output (except end), decision branch without a label |
| `REACHABILITY` | node not reachable from a start, or that cannot reach an end |
| `OVERLAP` | two shapes in the same place |
| `IMPORT-FAILED` | bpmn-js reports an error or warning when importing the XML in Chrome |
| `MARKETING-COPY` | marketing vocabulary in title or subtitle |
| `COLOR-OUTSIDE-THEME` | a node with its own fill; colors come from the theme |

The bpmn-js bundle is in `skills/ai-diagrams/bpmn/vendor/`, with its license in `skills/ai-diagrams/bpmn/vendor/LICENSE`. The format is in `skills/ai-diagrams/references/bpmn.md`.

## 5. Theme

Every color and both font families are tokens. A theme is one JSON file: `skills/ai-diagrams/themes/ai-diagrams.json` (the default) and `themes/paper.json` (cream paper, dark brown ink, petrol-blue accent, Public Sans and Source Code Pro) ship with the skill. Theme files use `schema_version` 2. Required groups: `colors` (`ink`, `support`, `muted`, `zone`, `paper`, `accent`, `risk`, `risk_bg`), `derived` (`accent_strong`, `muted_light`, `c4_person_type`, `c4_person_desc`, `c4_external`, `c4_boundary`), `er_palette` (the `er_*` colors of the ER diagram) and `fonts` (`text`, `mono`). The optional `frame` group sets `header`, `footer`, `footer_right`, `classification` and `show_client`. A 0.1 theme file (version 1, Portuguese keys such as `cores` and `fontes`) is still read; the engine writes only version 2, and `python3 skills/ai-diagrams/scripts/theme.py --theme old.json --json` prints a v1 file converted to v2. Colors are `#RRGGBB`; fonts are Google Fonts family names with weights 400 to 700. The stylesheets set tight line heights (1.2 in card titles), so a family with tall vertical metrics can overflow its box and fail the gate with `OVERFLOW-Y`: Source Sans 3 does, by 2px, in the cards model. Before adopting a theme, build the reference models with it in a copy of `skills/ai-diagrams/templates/` (`AI_DIAGRAMS_THEME=<theme>` applies to every command).

**Selection.** Every command takes the same option, in this order of precedence:

1. `--theme <name or path.json>`;
2. `<meta name="theme" content="...">` in the HTML source (the generators write it when a theme was chosen; a path there is relative to the source folder);
3. the environment variable `AI_DIAGRAMS_THEME`;
4. the default, `ai-diagrams`.

A name resolves to `skills/ai-diagrams/themes/<name>.json`. A value that ends in `.json` or contains a slash is a path to a JSON file in any folder. The commands are `build.py`, `poster_lint.py`, `conceptual.py`, `build_swimlanes.py`, `build_sequence.py`, `build_states.py`, `bpmn/build_bpmn.py`, `er/er-build.mjs` and `er/er-overview.mjs`.

**One reader.** `skills/ai-diagrams/scripts/theme.py` is the only code that reads the JSON. It produces the `:root` with every color token, the `-rgb` channel tokens, `--font-text` and `--font-mono`, and the Google Fonts link of the two families. The gates (`build.py`, `poster_lint.py`, `conceptual.py`) replace the token `:root` of the base CSS with it and swap the font link of the source, so the lint measures with the same fonts as the PNG. The BPMN generator writes the theme colors into `bioc:fill`/`bioc:stroke` and the viewer CSS. The Node generators call `theme.py` for the link and the meta. The `:root` in `style.css` and `style-conceptual.css` is only the fallback of the default theme.

**Failures.** A theme that is missing a key stops the command before Chrome opens, with the key in the message: `THEME-INCOMPLETE: missing colors.accent`. An unknown name or path stops with `THEME-NOT-FOUND`, a color outside `#RRGGBB` with `THEME-INVALID`. There is no silent fallback.

**Geometry.** A theme changes color and font only. Box positions, arrow paths and BPMN coordinates come from the source or from the generator, which estimates text width with fixed constants, so they are the same in every theme. Elements sized by their text (header, step list, table rows) follow the font metrics of the theme.

Sources and generators use only `var(--token)`: `--ink` (main text), `--support` (secondary text and arrows), `--muted`, `--zone`, `--paper`, `--accent`, `--risk` on `--risk-bg`, plus the C4 and ER tokens, and `var(--font-text)` / `var(--font-mono)` for type. Until 0.3.0 the theme `:root` also declares the 0.1 token names (`--tinta`, `--risco-fundo`, `--fonte-texto` and the others) as aliases of the new ones, so older sources keep their colors. In SVG the color goes in `style` (`style="stroke:var(--support)"`), because the `stroke` and `fill` attributes do not accept `var()`. `python3 skills/ai-diagrams/scripts/check_theme.py` checks that the fallback `:root` of both stylesheets is exactly what `theme.py` produces for the default theme (`TOKEN-MISMATCH`), that no literal color or font family is left in the CSS or the generators (`COLOR-OUTSIDE-THEME`, `FONT-OUTSIDE-THEME`), and that every JSON in `themes/` is complete. To change the look of one diagram, pass another theme; to change the default, edit `themes/ai-diagrams.json`, paste the output of `python3 skills/ai-diagrams/scripts/theme.py --css` into both fallback blocks, and run `check_theme.py`.

`skills/ai-diagrams/assets/style.css` is the single stylesheet for posters, flows, tables, ER diagrams and the matrix. The build injects it. Main classes:

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

`skills/ai-diagrams/assets/style-conceptual.css` is the stylesheet for swimlanes, cards, sequence diagrams and state machines. The ER diagram adds local CSS for table boxes, band, boundary and legend, generated by `er-tables.mjs`.

## 6. Work cycle

1. **Content first.** Content comes from a decision document, a process description or a data model.
2. **The AI writes the source** in `diagrams/_src/`: frames, boxes, orthogonal arrows and the page frame. For an ER diagram, it writes `model.json` and the layout file. For swimlanes, sequence, state machine and BPMN, it writes the JSON spec.
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
| `er-<schema>.html` / `.png`, `er-<schema>.layout.mjs` | ER diagram of one schema and its layout |
| `er-overview.html` / `.png` | dependency matrix between schemas |
| `model.json` | logical model shared by the ER diagram and the matrix |
