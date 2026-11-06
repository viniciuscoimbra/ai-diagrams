# Contributing

Changes to the skill go in `skills/ai-diagrams/`. Read [docs/how-it-works.md](docs/how-it-works.md) before you change a script or a gate.

## Before every commit

Run these four commands in this order:

```bash
bash ferramentas/checar-segredos.sh
```

**Expected:** `nenhuma credencial encontrada` (no credential found).

```bash
bash testes/rodar.sh
```

**Expected:** ends with `total: 0`. The cases in `testes/negativos/` each carry one planted defect: overflow on the right, collinear arrows, marketing text, text over a lifeline, text inside a box or on its border, a cut capture, a loose badge, a missing style marker, a literal color outside the theme, a theme file that diverges from the CSS, defects in the C4 frame and arrows, and one broken graph per state machine check. The script checks that the gate still rejects each one for the right reason.

```bash
bash skills/ai-diagrams/modelos/gerar.sh
```

**Expected:** every model passes its gate, the last lines are `total: 0` and `tema: 34 tokens conferidos, 0 falhas` (theme checked), and the command exits without error.

```bash
bash exemplos/gerar.sh
```

**Expected:** ends with `exemplos: total: 0`.

## PNG files

- Open the PNGs of the models and examples you changed. A passing gate does not guarantee a readable diagram.
- Commit the source and the PNG together.
- Restore the PNGs you did not change with `git checkout`. Chrome never produces two byte-identical PNGs.
- The self-contained HTML built next to each model and example is not tracked by git. The `.bpmn` file is.

## Adding a diagram type

A new type must:

1. **Use only the theme colors and fonts.** Write every color as `var(--token)` and every font as `var(--fonte-texto)` or `var(--fonte-mono)`; `skills/ai-diagrams/scripts/tema.py` generates the tokens from the theme JSON in `skills/ai-diagrams/temas/`. A literal color fails with `COR-FORA-DO-TEMA`, a literal font family with `FONTE-FORA-DO-TEMA`. A new token goes in every theme file, in `OBRIGATORIAS` of `tema.py` and in the fallback `:root` of both base stylesheets, and `scripts/conferir_tema.py` must pass. A new command takes `--tema` through `tema.py` (see [docs/how-it-works.md](docs/how-it-works.md#5-theme)).
2. **Ship a reference model** in `skills/ai-diagrams/modelos/NN-<type>/`, with the source in `_src/` and the generated PNG. Add its build command to `skills/ai-diagrams/modelos/gerar.sh`.
3. **Pass the gate.** Use an existing gate (`skills/ai-diagrams/scripts/build.py`, `skills/ai-diagrams/scripts/conceitual.py` or `skills/ai-diagrams/bpmn/gerar_bpmn.py`), or add a gate that exits with code 1 on any defect and writes no PNG.
4. **Add a negative test** in `testes/negativos/` and a line in `testes/rodar.sh` for each new defect code.
5. **Add a row to the router** in `skills/ai-diagrams/SKILL.md` and a reference in `skills/ai-diagrams/references/`.
6. **Add an example** in `exemplos/<type>/` with `prompt.md`, a data file and `resultado/`, and its build command in `exemplos/gerar.sh`.

## Text in diagrams

Titles, subtitles, kickers and bands describe what the diagram shows. The gate rejects marketing vocabulary with `TEXTO-MARKETING`. The word list is in `skills/ai-diagrams/scripts/texto_tecnico.py`.

## Credentials

No key, token or password goes into the repository. `ferramentas/checar-segredos.sh` rejects common credential patterns and files such as `.env`, `*.pem` and `*.key`.
