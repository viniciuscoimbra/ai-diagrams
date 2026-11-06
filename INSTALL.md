# INSTALL: installing Prosa with an AI agent

This file is for an AI agent (Claude Code, Codex CLI or Kiro CLI) that installs the Prosa skill for a user. Follow the steps in order. Run each command on its own, without pipes and without extra `&&`. After each command, compare the output with the expected output. If the output differs, stop, show the user the command and its output, and do not continue.

For a manual install, see [docs/install.md](docs/install.md).

## Rules

- Never ask for, accept, write or store a password, token or key. The repository is public and the install needs no credential. If a command asks for one, stop and tell the user.
- Do not edit files outside the project folder and the folder the user picks for the skill.
- In every command below, replace `<PROSA>` and `<PROJECT>` with the absolute paths from step 0. Do not use environment variables: each command can run in a new shell.
- Do not use a symlink for Kiro. Kiro does not read files outside the project.
- Program output is in Portuguese. Match it exactly as written below.

## Step 0. Ask the user

Ask the three questions in one message and wait for the answer:

1. "Which CLI will you use with the skill: Claude Code, Codex or Kiro?"
2. "Which project folder should the diagrams go in?"
3. "Which folder can I keep the skill in? (If you have no preference, I will use the current folder.)"

Store the answers as `TOOL` (one of `claude-code`, `codex`, `kiro`), `<PROJECT>` (absolute path of the project folder) and `<PROSA>` (absolute path of the folder from answer 3, followed by `/prosa`). Expand `~` to the full home path.

## Step 1. Check the requirements

Run each command. All of them must succeed.

```bash
git --version
```

Expected: `git version 2.` followed by numbers.

```bash
python3 --version
```

Expected: `Python 3.9` or later.

```bash
python3 -c "import diagrams; print('diagrams ok')"
```

Expected: `diagrams ok`. If you get `ModuleNotFoundError`, run `pip3 install diagrams` and repeat. If pip refuses with `externally-managed-environment`, run `pip3 install --user --break-system-packages diagrams`. The package only provides the official AWS icons; none of its code runs.

```bash
node --version
```

Expected: `v18` or later. If Node is missing, stop and ask the user to install Node LTS. Only the ER diagram and the dependency matrix need it.

```bash
ls "/Applications/Google Chrome.app"
```

Expected: `Contents`. On Linux, run `which google-chrome` and expect a path. If Chrome is missing, stop and ask the user to install Google Chrome. If Chrome is installed somewhere else, ask the user for the path and use `POSTER_CHROME` in step 4.

Check the chosen CLI. Run only the one from the answer:

```bash
claude --version
```

```bash
codex --version
```

```bash
kiro-cli --version
```

Expected: a version number.

## Step 2. Clone or update the repository

```bash
ls <PROSA>/.git
```

If it lists files, the repository already exists. Update it:

```bash
git -C <PROSA> pull
```

Expected: `Already up to date.` or a list of changed files.

If you get `No such file or directory`, clone it:

```bash
git clone https://github.com/viniciuscoimbra/prosa.git <PROSA>
```

Expected: `Cloning into '<PROSA>'...` and no line starting with `fatal`. Then check:

```bash
ls <PROSA>/skills/prosa/SKILL.md
```

Expected: the file path.

## Step 3. Install in the tool

### If TOOL = claude-code

```bash
mkdir -p ~/.claude/skills
```

Expected: no output.

```bash
ls -la ~/.claude/skills/prosa
```

If you get `No such file or directory`, create the link:

```bash
ln -s <PROSA>/skills/prosa ~/.claude/skills/prosa
```

Expected: no output. If `ls` showed a regular folder (not a link), stop and ask the user whether you may replace the old copy.

```bash
ls ~/.claude/skills/prosa/SKILL.md
```

Expected: the file path.

### If TOOL = codex

```bash
mkdir -p ~/.codex/skills
```

Expected: no output.

```bash
ls -la ~/.codex/skills/prosa
```

If you get `No such file or directory`, create the link:

```bash
ln -s <PROSA>/skills/prosa ~/.codex/skills/prosa
```

Expected: no output. If `ls` showed a regular folder (not a link), stop and ask the user whether you may replace the old copy.

```bash
ls ~/.codex/skills/prosa/SKILL.md
```

Expected: the file path.

### If TOOL = kiro

```bash
bash <PROSA>/ferramentas/instalar-kiro.sh <PROJECT>
```

Expected: four lines starting with `steering:`, `agente:`, `skill:` and `modelos:`. The last one is `modelos:  9 de 9`. The script copies the skill, the steering file and the agent into `<PROJECT>/.kiro/`.

```bash
kiro-cli agent validate --path <PROJECT>/.kiro/agents/prosa.json
```

Expected: no error message.

## Step 4. Smoke test

This command builds the PNG of one reference model into a temporary folder. It checks Python, the icons, Chrome and the gate in one run.

```bash
python3 <PROSA>/skills/prosa/scripts/build.py <PROSA>/skills/prosa/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html --out /tmp
```

Expected: two lines starting with `OK`. The last one ends in `05-comparacao-mensageria.png`.

- `Chrome não encontrado` (Chrome not found): ask the user for the Chrome path and run the command again with `POSTER_CHROME="<path>"` in front of it.
- `Ícones AWS não encontrados` (AWS icons not found): go back to step 1 and install the `diagrams` package with the same `python3`.

## Step 5. Tell the user how to use it

Reply with the line for the user's tool:

- **claude-code:** "Open Claude Code in the project folder and describe the diagram in plain language. Start the request with 'Use the prosa skill'."
- **codex:** "Open Codex in the project folder with `codex --sandbox danger-full-access` (the default sandbox blocks the headless Chrome that the gate uses). Start the request with 'Use the prosa skill'."
- **kiro:** "Run `kiro-cli chat --agent prosa` in the project folder, or pick the `prosa` agent with `/agent`. Start the request with 'Use the prosa skill'."

Also say: "Drawing quality depends on the model. Use a frontier model. Weak models get coordinates wrong, need more gate rounds and may never pass."

In every case, show the user the nine diagram types and point them to `exemplos/<type>/prompt.md` for sample requests:

| Type | Example folder |
|---|---|
| AWS architecture poster | `exemplos/arquitetura-aws/` |
| Numbered-step flow | `exemplos/fluxo-passos/` |
| Comparison table | `exemplos/tabela-comparacao/` |
| Sequence diagram | `exemplos/sequencia/` |
| Swimlanes | `exemplos/raias/` |
| Cards catalog | `exemplos/catalogo-cards/` |
| BPMN 2.0 | `exemplos/bpmn/` |
| ER diagram per schema | `exemplos/der-schema/` |
| Schema dependency matrix | `exemplos/matriz-dependencia/` |
