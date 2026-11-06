# Models

Diagram quality depends on the model. What is measured on this repository is listed below. Anything not listed has not been measured yet.

## Measured on Prosa (2026-11-06)

Claude Code 2.1.318, model `claude-sonnet-5-5`. Each run was a fresh, non-interactive session with only the Prosa skill installed, using the prompt from `exemplos/<type>/prompt.md`. A run passes when the PNG is produced, the gate returns 0 when re-run on the saved source, and the PNG shows no visible defect.

| Type | Result | Gate calls in the session | Time | Cost |
|---|---|---|---|---|
| AWS architecture poster | passes; one frame ends about 8 px past the right margin | 5 | 5 min 34 s | US$0.53 |
| Sequence diagram | passes | 7 (2 rejected, then fixed) | 6 min 12 s | US$0.41 |

The other seven types were not run on Prosa yet.

## Measured before the theme change

The same skill was measured with its previous visual theme, before it became Prosa: 9 types × 3 models, one run per cell. The gate and the layout scripts were the same, and only colors, fonts and names changed afterwards. Treat these results as a guide, not as a measurement of this repository.

| Model | Runs with a clean PNG | Gate at 0 |
|---|---|---|
| `claude-sonnet-5-5` | 8 of 9 (BPMN: one arrow crossed another) | 9 of 9 |
| `claude-opus-5-5` | 7 of 9 (step flow past the margin; sequence notes over activation bars) | 9 of 9 |
| `claude-haiku-5-5` | 7 of 9 (poster without side margin; step flow past the margin) | 9 of 9 |

Codex CLI and Kiro CLI have not been measured on this repository.

## Known issues the gate does not catch

- An element can end a few pixels past the right page margin (posters and step flows).
- Decision exits in swimlanes are drawn without labels.
- In cards, the last line of a field can sit very close to the card footer rule.
- In the swimlanes example, one arrow ends on a status chip instead of the box above it.

## Tests to run

- The seven remaining types on Prosa with `claude-sonnet-5-5`.
- Codex CLI with `codex exec --sandbox danger-full-access`.
- Kiro CLI.
- Repeated runs of each type, to measure stability.
