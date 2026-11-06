# Models

Diagram quality depends on the model. This page lists only what was measured. A cell without a measurement says "not measured".

## Compatibility: diagram type × model

| Type | Claude Code · Sonnet 4.5 | Claude Code · Opus 5.5 | Claude Code · Sonnet 5.5 | Claude Code · Haiku 5.5 | Codex CLI | Kiro CLI · Sonnet 4.5 |
|---|---|---|---|---|---|---|
| AWS architecture poster | gate 0 ¹ | pass ² | pass ³ | defect: no side margin ² | not measured ⁴ | not measured ⁵ |
| Numbered-step flow | gate 0 ¹ | defect: panel past the margin ² | pass ² | defect: box past the margin ² | not measured | not measured ⁵ |
| Comparison table | gate 0 ¹ | pass ² | pass ² | pass ² | not measured | gate 0 ⁵ |
| ER diagram per schema | gate 0 ¹ | pass ² | pass ² | pass ² | not measured | gate 0 ⁵ |
| Schema dependency matrix | gate 0 ¹ | pass ² | pass ² | pass ² | not measured | gate 0 ⁵ |
| Swimlanes | gate 0 ¹ | pass ² | pass ² | pass ² | not measured | gate 0 ⁵ |
| Cards catalog | gate 0 ¹ | pass ² | pass ² | pass ² | not measured | not measured ⁵ |
| BPMN 2.0 | gate 0 ¹ | pass ² | defect: one arrow crosses another ² | pass ² | not measured | gate 0 ⁵ |
| Sequence diagram | defect: labels touching ² | defect: note over activation bars ² | pass ³ | pass ² | not measured | not measured |
| State machine | defect: labels far from their arrow ⁶ | not measured | not measured | not measured | not measured | not measured |
| C4 container diagram | fail: 3 runs ⁷ | pass ⁷ | not measured | not measured | not measured | not measured |

- **pass**: the PNG was produced, the gate returned 0 when re-run on the saved source, and the PNG shows no visible defect.
- **defect**: the PNG was produced and the gate returned 0, but the PNG has a visible defect the gate does not catch.
- **gate 0**: the gate returned 0. The PNG was not re-read for this table.
- **fail**: the run did not deliver a correct diagram.

### Where each result comes from

1. 2026-11-04, end-to-end run of the eight original types (all except sequence) in a clean install, before later fixes to the skill. Result: 8 of 8 with the gate at 0.
2. 2026-11-06, one run per cell, before the visual theme of this repository. The gate and the layout scripts were the same; only colors, fonts and names changed afterwards.
3. 2026-11-06, on this repository under its previous name, Claude Code 2.1.318, before the state machine, C4 and color tokens were added. Poster: one frame ends about 8 px past the right margin (5 gate calls, 5 min 34 s, US$0.53). Sequence: 7 gate calls, 2 rejected and then fixed (6 min 12 s, US$0.41). Before the theme change, the same model also passed both types.
4. Codex CLI was not measured on this repository. Before the theme change, one poster run passed the gate (2026-11-04); its PNG was not re-read.
5. Kiro round 2, before later fixes to the skill. Poster, step flow and cards were not run again after those fixes: the account hit the request limit.
6. 2026-11-06, one run. The gate returned 0, but two-line labels sat far from their arrow. The generator was fixed and the PNG regenerated from the same spec; the model was not run again.
7. 2026-11-06. Sonnet 4.5, three runs: the first delivered a PNG without CSS, the second passed the gate of the time with arrows starting inside boxes and a loose label (that source became the negative test `testes/negativos/c4-setas.html`), the third passed the new gate but one arrow reached the wrong system. Opus 5.5, one run: gate 0 and a clean PNG, 11 relations, all to the right target. It is the result in `exemplos/c4/resultado/`.

### Versions

| Column | CLI | Model |
|---|---|---|
| Sonnet 4.5 | Claude Code | `claude-sonnet-4-5` |
| Opus 5.5 | Claude Code 2.1.318 | `claude-opus-5-5` |
| Sonnet 5.5 | Claude Code 2.1.318 | `claude-sonnet-5-5` |
| Haiku 5.5 | Claude Code 2.1.318 | `claude-haiku-5-5` |
| Kiro CLI | Kiro CLI | Claude Sonnet 4.5 |

Each run was a fresh, non-interactive session with only this skill installed, using the prompt from `exemplos/<type>/prompt.md`, one run at a time.

## Known issues the gate does not catch

- An element can end a few pixels past the right page margin (posters and step flows).
- Decision exits in swimlanes are drawn without labels.
- In cards, the last line of a field can sit very close to the card footer rule.
- In the swimlanes example, one arrow ends on a status chip instead of the box above it.

## Tests to run

- Every type on this repository after the state machine, C4 and color tokens were added.
- State machine and C4 on Sonnet 5.5, Opus 5.5 (state machine) and Haiku 5.5.
- Codex CLI with `codex exec --sandbox danger-full-access`.
- Kiro CLI: poster, step flow, cards, sequence, state machine and C4.
- Repeated runs of each type, to measure stability.
