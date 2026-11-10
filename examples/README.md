# Examples by type

Each folder holds three things:

1. `prompt.md`: the exact prompt pasted into Claude Code;
2. the data file that goes with the prompt;
3. `output/`: what the skill produced from that prompt, with the source in `output/_src/` and the PNG in `output/` (for BPMN, also the `.bpmn` file).

`bash examples/build-all.sh` rebuilds the eleven results from their sources, through the gate of each type.

The results were generated on 2026-11-04 (sequence on 2026-11-05 and state machine on 2026-11-06) by Claude Code sessions with the skill from this repository, one session per type, run from the repository root. Each session ran the gate of its type down to zero and read the PNG before delivering. The prompts and the diagram text are in Portuguese, the language the requests were written in. The prompts point to paths in `examples/`; in your project, use the path of your own data file and leave out the output folder (the skill writes to `diagrams/` by default).

| Folder | Type | Data | Gate |
|---|---|---|---|
| `aws-architecture/` | AWS architecture poster | `antifraud-decision.md` | `poster_lint.py` via `build.py` |
| `step-flow/` | numbered-step flow | `reconciliation.md` | `poster_lint.py` via `build.py` |
| `er-schema/` | ER diagram per schema | `ddl.sql` | `poster_lint.py` via `build.py` |
| `dependency-matrix/` | schema dependency matrix | `ddl.sql` | `poster_lint.py` via `build.py` |
| `comparison-table/` | comparison table | `criteria.yaml` | `poster_lint.py` via `build.py` |
| `swimlanes/` | swimlanes | `process.md` | `conceptual.py` |
| `card-catalog/` | cards catalog | `events.csv` | `conceptual.py` |
| `bpmn/` | BPMN 2.0 | `process.md` | `build_bpmn.py` |
| `sequence/` | sequence diagram | `authorization.md` | `conceptual.py` |
| `state-machine/` | state machine | `card-lifecycle.md` | `build_states.py` and `conceptual.py` |
| `c4/` | C4 container diagram | `billing.md` | `poster_lint.py` via `build.py` (result made with Opus 5.5, see below) |

`import/` holds the importer fixtures in `pt-BR`, `en` and `es`; see [docs/importing.md](../docs/importing.md).

In tools that cannot run commands (Claude.ai without the skill installed, ChatGPT, Bedrock), the same prompt returns only the source; you build the PNG on your machine with the command of the type. See `docs/install.md`.

The C4 result (`c4/`) was generated on 2026-11-06 with Claude Opus 5.5, not with the Sonnet 4.5 used for the other types: the Sonnet 4.5 run passed the gate and failed the review of the PNG.
