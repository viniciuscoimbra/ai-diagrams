# Poster visual language

The poster is an editorial page: a text frame around a drawing canvas. Everything inside the canvas uses `position:absolute` with pixel coordinates. The layout is the decision of whoever draws; there is no auto-layout.

## Editorial frame (outside the canvas)

| Element | Class | Content |
|---|---|---|
| Header | `.hdr` | two spans: identity on the left, diagram code on the right |
| Kicker | `.kicker` | category in caps, with `<span class="sq">■</span>` in the accent color |
| Title | `h1` | the technical name of the flow or system; no thesis, no catchphrase, technical terms in English |
| Subtitle | `.sub` | 2 to 3 factual sentences: what the diagram shows and the measured state, with numbers; no dramatization |
| Steps | `.passos` | numbered list `.pitem` (badge `.pb` + sentence); narrates the flow in reading order |
| Footer | `.foot` | author · company · date |

Body layout: `.wrap` puts canvas and steps side by side (canvas 1140px). `.wrap.stack` stacks them (canvas 1700px, steps in 3 columns below); use it when the drawing needs width.

## Containers (frames)

All are `<div class="frame X">` with `.flabel` inside:

| Class | Meaning | Stroke |
|---|---|---|
| `awscloud` | AWS boundary; the flabel carries `<img src="aws://aws.png">` | solid black 1.6px |
| `region` | AWS region | dark dashed |
| `account` | AWS account (isolation) | gray dashed |
| `zone` | logical grouping inside the account | background `var(--zone)` |
| `ext` | external system or outside our control | border `var(--risk)` on `var(--risk-bg)` |

## Content boxes

| Class | Use | Anatomy |
|---|---|---|
| `.node` | main AWS service | `<img src="aws://…">` 44px + `.nl` (name) + `.ns` (role) |
| `.svc` | compact AWS service (one line) | 24px icon on the left + `.ot` + `.os`; set `width`/`height` |
| `.oss` | pluggable open source component | like `.svc`, 28px icon, with a `.tag` seal in the accent color |
| `.chip` | concept without an icon (topic, contract, policy) | centered text; `.chip.red` for risk/negative |
| `.bchip` | reference to another architecture block | `.bn` (number) + `.bt` (title) + `.bs` (relation) |
| `.badge` | step number on the drawing | 20px black square with the number |
| `.elabel` | edge label | small gray text placed next to the arrow |

## Arrows

A single `<svg class="edges">` covers the canvas (`viewBox` = canvas dimensions). Rules:

- Always orthogonal: `path` with `M`/`H`/`V` segments (never diagonals or curves).
- `style="stroke:var(--support)" stroke-width="1.6"` with `marker-end` (define the `<marker>` in `<defs>`, with `style="fill:var(--support)"` on the arrowhead). The SVG `stroke` or `fill` attribute does not accept `var()`; that is why the color goes in `style`.
- The arrowhead touches the target box and the start leaves the source box. The lint checks this with a 6px tolerance; between 6 and 60px, `--fix` corrects it on its own.
- Secondary or return flow: `style="stroke:var(--muted)"` or `stroke-dasharray`.


## Badges and steps on the drawing

- The step badge **is born with the arrow**: its center sits on the line (6px tolerance in the lint), and it can slide along the orthogonal segments so it does not compete with the arrow's label or with neighboring boxes. A badge beside the line or loose on the canvas fails (`BADGE-DETACHED`).
- Pick the segment where the badge is not ambiguous: when two arrows run close together, each badge goes on the segment that belongs only to its own arrow.
- Connections on the same box: converging flows can meet at the same point, as long as the separation of the paths is clear up to there; flows from different paths enter and leave the same box at spaced points.

## Coordinate recipe

Math done before writing the source. With it the lint passes on the first round.

**Solid box of each element** (this is where the arrow touches):

| Element | Written as | Solid box |
|---|---|---|
| `.node` | `left:L;top:T` (width 110) | only the icon: x from `L+33` to `L+77`, y from `T` to `T+44`; center at `(L+55, T+22)` |
| `.svc`, `.oss`, `.chip`, `.bchip` | `left`, `top`, `width`, `height` | the whole box |

The name (`.nl`) and the role (`.ns`) of a `.node` sit below the icon, from `T+50` to about `T+95`, in a 110px band (`L` to `L+110`). No arrow passes through that band.

**Arrows between nodes:**

- Same row: horizontal at the height of the icon center. From `A` to `B` on the right: `M(LA+77),(TA+22) H(LB+33)`.
- Upward: leaves from the top of the icon, `M(L+55),T V...`.
- Downward: never leaves from the bottom of the icon (it would cross the name). It leaves from the side, `M(L+77),(T+22) H(corridor)`, goes down the corridor and enters the target box.
- To a `.svc`: the arrowhead touches the edge of the box (`left`, `left+width`, `top` or `top+height`).

**Corridors:** they are the free x values between the grid columns, at least 10px from any box and from any name band (`L` to `L+110`). Each arrow has its own x, at least 14px from the x of another arrow that runs on the same stretch. The same applies to the y values of horizontal segments.

**Badge:** the center sits in the middle of the longest segment of its own arrow. On a segment from `(x1,y)` to `(x2,y)`, the badge is `left:((x1+x2)/2 - 10)px;top:(y - 10)px`. On a vertical one from `(x,y1)` to `(x,y2)`, it is `left:(x - 10)px;top:((y1+y2)/2 - 10)px`. The segment must be at least 40px long.

**Work order:**

1. Write the source with the math above.
2. Run `poster_lint.py --fix`: it snaps arrowheads that are up to 60px from the box (forward, or backing up if the arrow went past the edge) and moves each detached badge to the nearest arrow. The `FIXED` lines say what changed.
3. Run `poster_lint.py` again, without `--fix`. `DETACHED` gives the nearest box edge; `ARROW-OVER-TEXT` gives the x or y range the arrow must avoid. Fix the source with these numbers.
4. Repeat step 3 until `total: 0`. Only then run `build.py`.

## AWS icons

Reference in the HTML: `aws://category/file.png`. The build embeds it in base64 from the icon collection of the `diagrams` pip package (`<site-packages>/resources/aws/`). Most used categories: `compute`, `database`, `network`, `analytics`, `integration`, `security`, `storage`, `ml`, `management`, `general`. To find the exact name of an icon:

```bash
python3 -c "import diagrams,os;print(os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)),'resources','aws'))"
ls <path>/database/ | grep -i aurora
```

The build fails with a clear list if an `aws://` does not exist; fix the name and run it again.

## Palette

Color comes from the theme, never from a literal in the source. Tokens: `--ink` (main text), `--support` (supporting text and arrows), `--muted`, `--zone` (zone background), `--paper`, `--accent` (accent color, never a text color), `--risk` on `--risk-bg`. The values come from the chosen theme (`--theme`, default `themes/ai-diagrams.json`); the gate generates the `:root` from it (`scripts/theme.py`). Hexadecimal or `rgb()` in the source fails with `COLOR-OUTSIDE-THEME`, including in a local style. Fonts: `var(--font-text)` for text and `var(--font-mono)` for technical labels (caps with letter-spacing); in the default theme, IBM Plex Sans and IBM Plex Mono. A family written in the source fails with `FONT-OUTSIDE-THEME`.

## Naming conventions

| Pattern | What it is |
|---|---|
| `NN-name.html` | poster of block NN |
| `NN.M-descriptive.html` | detail poster (satellite of block NN) |
| `NN.M-descriptive-topology.html` | AWS landing topology of the detail |
| `NN-name-N-part.html` | block split into parts |

Source in `_src/`, deliverables (self-contained HTML + PNG) in the parent folder.
