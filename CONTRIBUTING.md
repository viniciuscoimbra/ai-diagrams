# Contributing

Changes to the skill go in `skills/prosa/`. Read [docs/how-it-works.md](docs/how-it-works.md) before you change a script or a gate.

## Before every commit

Run these four commands in this order:

```bash
bash ferramentas/checar-segredos.sh
```

**Expected:** `nenhuma credencial encontrada` (no credential found).

```bash
bash testes/rodar.sh
```

**Expected:** ends with `total: 0`. The cases in `testes/negativos/` each carry one planted defect: overflow on the right, collinear arrows, marketing text, text over a lifeline, text inside a box or on its border, a cut capture and a loose badge. The script checks that the gate still rejects each one for the right reason.

```bash
bash skills/prosa/modelos/gerar.sh
```

**Expected:** every model passes its gate and the command exits without error.

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

1. **Use only the theme colors.** Take every color from `skills/prosa/assets/estilo.css` or `skills/prosa/assets/estilo-conceitual.css`. Do not add new colors in the source or in local CSS.
2. **Ship a reference model** in `skills/prosa/modelos/NN-<type>/`, with the source in `_src/` and the generated PNG. Add its build command to `skills/prosa/modelos/gerar.sh`.
3. **Pass the gate.** Use an existing gate (`skills/prosa/scripts/build.py`, `skills/prosa/scripts/conceitual.py` or `skills/prosa/bpmn/gerar_bpmn.py`), or add a gate that exits with code 1 on any defect and writes no PNG.
4. **Add a negative test** in `testes/negativos/` and a line in `testes/rodar.sh` for each new defect code.
5. **Add a row to the router** in `skills/prosa/SKILL.md` and a reference in `skills/prosa/references/`.
6. **Add an example** in `exemplos/<type>/` with `prompt.md`, a data file and `resultado/`, and its build command in `exemplos/gerar.sh`.

## Text in diagrams

Titles, subtitles, kickers and bands describe what the diagram shows. The gate rejects marketing vocabulary with `TEXTO-MARKETING`. The word list is in `skills/prosa/scripts/texto_tecnico.py`.

## Credentials

No key, token or password goes into the repository. `ferramentas/checar-segredos.sh` rejects common credential patterns and files such as `.env`, `*.pem` and `*.key`.
