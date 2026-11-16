---
inclusion: always
---

# Diagrams in this project

Every diagram request in this project (AWS architecture poster, C4, flow, sequence, state machine, swimlanes, BPMN, comparison table, card catalog, ER diagram or dependency matrix) uses the `ai-diagrams` skill. Do not answer with markdown, Mermaid or text in place of the diagram.

Before drawing:

1. Read the skill's `SKILL.md`, in `.kiro/skills/ai-diagrams/` in the project or in `~/.kiro/skills/ai-diagrams/`. Its router picks the type.
2. If the request does not say whether the client name appears in the diagram, ask first, in a single message: with client (`<Project> · <subject> · <Client>`, and what the name is) or without client (`<Project> · <subject>`), offering the footer `<Project> · <diagram type> · YYYY-MM` and the version `V1`. Never infer the client from the folder or repository name. With no possible interaction, go on without a client and say so in the delivery.
3. Open the type's template in `templates/` and the reference in `references/`, inside the skill folder.
4. Write the source in `diagrams/_src/` and run the type's command, which is in `SKILL.md` and generates the PNG in `diagrams/`.
5. The command's gate has to end at zero. Open the PNG and check how it reads before saying you are done.

Rules:

- Do not create a helper script (`.py`, `.sh` or other) to run the build. Run the skill's command directly. If you cannot run it, deliver the source and the exact command for the user to run.
- Run each command alone, without a pipe (`|`), without redirection (`2>&1`, `>`) and without `&&`: the project's agent only allows the plain command.
- Do not copy or edit the skill's CSS in the project. Width, font and grid already come right.
- On the poster and the flow with steps, follow the "Coordinate recipe" in `references/visual-language.md` and run `poster_lint.py --fix` before `build.py`.
- A failed gate is not a delivery. Never say you are done while the gate fails. After five rounds of fixes without reaching zero, stop and deliver the source, the output of the last gate and the sentence "the gate failed; the PNG was not generated" (in the user's language).
- If a flow request is ambiguous between steps, swimlanes and BPMN, ask first.
