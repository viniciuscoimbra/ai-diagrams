# Swimlane flow and conceptual diagrams

Diagrams without AWS: who does what, in which order, between teams or roles. They use `assets/style-conceptual.css` (off-white background with a grid, white panels, black closing band) and the `scripts/conceptual.py` gate.

Templates: `templates/06-swimlanes/` (swimlane flow generated from JSON) and `templates/07-card-catalog/` (card catalog written by hand), in the skill folder.

## Swimlane flow (`build_swimlanes.py`)

A lane is a row (the actor), a phase is a column (the moment). The coordinates are computed from the JSON; nobody writes pixels.

```json
{
  "page_title": "06 · Abertura de conta",
  "header": ["Company · Project", "06 · Raias"],
  "kicker": "Fluxo em raias",
  "h1": "Abertura de conta: do pedido à conta ativa",
  "sub": "one or two factual sentences",
  "lanes": [{"name": "Cliente", "sub": "pelo app"}, {"name": "Onboarding", "sub": ""}],
  "phases": ["Pedir", "Verificar"],
  "elements": [
    {"lane": 0, "phase": 0, "text": "Enviar documento"},
    {"lane": 1, "phase": 1, "text": "Conferir documento", "chip": "em análise", "title": "optional", "style": "focus"}
  ],
  "sequence": [[0, 0, 1, 1]],
  "sections": [
    {"title": "Situação do pedido", "type": "steps", "items": [["Em análise", "what it means"]]},
    {"title": "Quem recebe", "type": "targets", "items": [["Cliente", "what they receive"]]}
  ],
  "band": {"f1": "the sentence that closes the diagram", "f2": "what was left out"},
  "footer": ["Author", "Project · YYYY-MM"]
}
```

The sample content is in pt-BR, like the template; write it in the language the user asks for.

- `elements`: one per lane × phase cell. `chip` is the status below the panel; `style` accepts `focus` (border in the accent color) and `out` (risk, red).
- `sequence`: pairs `[lane, phase, lane, phase]`. The arrow goes from left to right through the corridor between the phases; in the same phase, it goes down or up the column. A panel can have several exits (fork) and several arrivals: each arrow gets its own exit height, arrival height and corridor x, and the corridor widens with the number of arrows. An arrow that skips phases bends in the corridor next to the source or next to the target; the generator tries the options and the exit and arrival orders and keeps the drawing with the fewest crossings. If the arrow could only pass over a panel, the generator stops with a message: change the lane or the phase of one of the panels.
- Width: the canvas stays at up to 1320px; with many corridors, the panels narrow down to 140px before the page grows.
- `sections`: `steps` becomes the legend with a black top border; `targets` becomes cards with a top border.
- Up to seven phases fit in the 1400px width; five lanes is the comfortable reading limit.

```bash
python3 <skill>/scripts/build_swimlanes.py diagrams/_src/NN-flow.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-flow.html
```

## Conceptual diagram by hand (cards, panels)

For a catalog, the anatomy of an artifact or a relationship between teams with no flow order, write the HTML starting from template 07. Classes of the conceptual CSS:

| Class | Use |
|---|---|
| `.grid` + `.card` (`.sid`, `.snome`, `.linha` with `.rot` and `.txt`, `.slug`) | card catalog, five per row |
| `.canvas` + `.painel` (`.pt`, `.ps`, `.ptag`) | absolutely positioned panels, with arrows in `svg.edges` |
| `.lane`, `.fase`, `.chip` | lanes, phase titles and status |
| `.legenda` + `.passo`, `.destinos` + `.destino` | sections below the drawing |
| `.faixa` (`.f1`, `.f2`) | closing in a dark band with a bar in the accent color |

### Cards: width, grid and frame

- The conceptual page is 1400px wide and is read displayed at 1000px; the gate fails text below the minimum at that scale (`TEXT-TOO-SMALL`). Do not widen the page or copy the CSS into the project: with a wider page, the same text becomes too small and fails.
- `.grid` has five fixed columns. Six to ten cards wrap into two rows on their own; do not change `grid-template-columns`. More than ten cards: split into two diagrams.
- Each card has `.sid` (short code), `.snome` (name in up to three words, to fit on one line), up to three `.linha` with `.rot` and `.txt` (one short sentence each) and `.slug`. Text that does not fit fails with `OVERFLOW`.
- Frame: `.hdr` with `<Project> · <subject>` on the left and `NN · <name>` on the right; `.foot` with author or project on the left and `<type> · YYYY-MM` on the right. The footer does not go in the header.

## Gate (`conceptual.py`)

It measures everything in Chrome under the same conditions as the screenshot and fails with exit 1:

- `OVERFLOW`: text larger than the box;
- `OVERLAP`: two content boxes intersect;
- `OFF-PAGE`, `OFF-CANVAS`: an element leaves the frame;
- `TEXT-TOO-SMALL`: text below the reading minimum at the display width (`--display`, default 1000px);
- `LABEL-OVER-BOX`: a loose label covering someone else's box;
- `ARROW-DETACHED`, `ARROW-OVER-TEXT`: an arrowhead that does not touch a box, an arrow crossing text;
- `COLLINEAR`: two different arrows running on the same line.

It does not require numbered steps or a badge on the arrow: that rule belongs to the posters. The capture height is measured on its own (`--height auto`, default). The CSS comes from the project's `_style-conceptual.css`, if it exists; otherwise, the skill's.
