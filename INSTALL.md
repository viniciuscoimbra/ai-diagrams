# INSTALL: installing ai-diagrams with an AI agent

This file is for an AI agent (Claude Code, Codex CLI or Kiro CLI) that installs the ai-diagrams skill for a user. Choose the npm route or the git clone route below. Run each command on its own, without pipes and without extra `&&`. After each command, compare the output with the expected output. If the output differs, stop, show the user the command and its output, and do not continue.

For a manual install, see [docs/install.md](docs/install.md).

## npm route

The npm package is prepared locally and has not been published. These registry commands become available after publication. Until then, use the git clone route or test the tarball with `bash testes/npm-smoke.sh` from a checkout.

Use the tool and project already named by the user; ask only for missing choices. With Node 18+ and npm installed, run the command for that tool:

```bash
npx ai-diagrams install --claude
```

```bash
npx ai-diagrams install --codex
```

```bash
npx ai-diagrams install --kiro --projeto <PROJECT>
```

Claude Code and Codex receive the same global links as the git route, in `~/.claude/skills/ai-diagrams` and `~/.codex/skills/ai-diagrams`. For a project-local link, add `--projeto <PROJECT>`. Kiro always receives real copies of the skill, steering and agent in the project; without `--projeto`, it uses the current directory. Choose exactly one CLI flag.

Expected: `skill:` with the link path, or the four Kiro lines described in step 3. Existing files are preserved unless the user confirms replacement in an interactive terminal. Approved replacement keeps a backup next to each replaced path and prints `Backup preservado:` with its location. If installation fails, the originals are restored. Non-interactive conflicts fail without changing the installation; an identical Claude/Codex link reports `Já instalado` (already installed).

For a persistent global package and the `ai-diagrams` command:

```bash
npm install -g ai-diagrams
```

```bash
ai-diagrams install --claude
```

The global npm install adds the command; the second command registers the skill with the chosen tool. `npx` links point into npm's cache. If that cache is cleared, repeat the `npx` installation or use the global package.

Check the requirements:

```bash
npx ai-diagrams doctor
```

Expected: `OK` lines for Node 18+, Python 3.9+, Chrome and AWS icons. A missing requirement reports `FALHA` and exits with status 1. The doctor detects Chrome using the same `POSTER_CHROME` override and search paths as the engine; it does not launch Chrome or claim that a rendering gate passed. Install missing requirements with step 1 below, then follow the tool-specific first-use instructions in [docs/install.md](docs/install.md). Import existing sources with `ai-diagrams importar <file> --saida diagramas`; see [the import guide](docs/importing.md).

## git clone route

The following steps remain available without npm publication.

## Rules

- Never ask for, accept, write or store a password, token or key. The repository is public and the install needs no credential. If a command asks for one, stop and tell the user.
- Do not edit files outside the project folder and the folder the user picks for the skill.
- In every command below, replace `<AI_DIAGRAMS>` and `<PROJECT>` with the absolute paths from step 0. Do not use environment variables: each command can run in a new shell.
- Do not use a symlink for Kiro. Kiro does not read files outside the project.
- Program output is in Portuguese. Match it exactly as written below.

## Step 0. Ask the user

Ask the three questions in one message and wait for the answer:

1. "Which CLI will you use with the skill: Claude Code, Codex or Kiro?"
2. "Which project folder should the diagrams go in?"
3. "Which folder can I keep the skill in? (If you have no preference, I will use the current folder.)"

Store the answers as `TOOL` (one of `claude-code`, `codex`, `kiro`), `<PROJECT>` (absolute path of the project folder) and `<AI_DIAGRAMS>` (absolute path of the folder from answer 3, followed by `/ai-diagrams`). Expand `~` to the full home path.

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
ls <AI_DIAGRAMS>/.git
```

If it lists files, the repository already exists. Update it:

```bash
git -C <AI_DIAGRAMS> pull
```

Expected: `Already up to date.` or a list of changed files.

If you get `No such file or directory`, clone it:

```bash
git clone https://github.com/viniciuscoimbra/ai-diagrams.git <AI_DIAGRAMS>
```

Expected: `Cloning into '<AI_DIAGRAMS>'...` and no line starting with `fatal`. Then check:

```bash
ls <AI_DIAGRAMS>/skills/ai-diagrams/SKILL.md
```

Expected: the file path.

## Step 3. Install in the tool

### If TOOL = claude-code

```bash
mkdir -p ~/.claude/skills
```

Expected: no output.

```bash
ls -la ~/.claude/skills/ai-diagrams
```

If you get `No such file or directory`, create the link:

```bash
ln -s <AI_DIAGRAMS>/skills/ai-diagrams ~/.claude/skills/ai-diagrams
```

Expected: no output. If `ls` showed a regular folder (not a link), stop and ask the user whether you may replace the old copy.

```bash
ls ~/.claude/skills/ai-diagrams/SKILL.md
```

Expected: the file path.

### If TOOL = codex

```bash
mkdir -p ~/.codex/skills
```

Expected: no output.

```bash
ls -la ~/.codex/skills/ai-diagrams
```

If you get `No such file or directory`, create the link:

```bash
ln -s <AI_DIAGRAMS>/skills/ai-diagrams ~/.codex/skills/ai-diagrams
```

Expected: no output. If `ls` showed a regular folder (not a link), stop and ask the user whether you may replace the old copy.

```bash
ls ~/.codex/skills/ai-diagrams/SKILL.md
```

Expected: the file path.

### If TOOL = kiro

```bash
bash <AI_DIAGRAMS>/ferramentas/instalar-kiro.sh <PROJECT>
```

Expected: four lines starting with `steering:`, `agente:`, `skill:` and `modelos:`. The last one is `modelos:  11 de 11`. The script copies the skill, the steering file and the agent into `<PROJECT>/.kiro/`.

```bash
kiro-cli agent validate --path <PROJECT>/.kiro/agents/ai-diagrams.json
```

Expected: no error message.

## Step 4. Smoke test

This command builds the PNG of one reference model into a temporary folder. It checks Python, the icons, Chrome and the gate in one run.

```bash
python3 <AI_DIAGRAMS>/skills/ai-diagrams/scripts/build.py <AI_DIAGRAMS>/skills/ai-diagrams/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html --out /tmp
```

Expected: two lines starting with `OK`. The last one ends in `05-comparacao-mensageria.png`.

- `Chrome não encontrado` (Chrome not found): ask the user for the Chrome path and run the command again with `POSTER_CHROME="<path>"` in front of it.
- `Ícones AWS não encontrados` (AWS icons not found): go back to step 1 and install the `diagrams` package with the same `python3`.

## Step 5. Tell the user how to use it

Reply with the line for the user's tool:

- **claude-code:** "Open Claude Code in the project folder and describe the diagram in plain language. Start the request with 'Use the ai-diagrams skill'."
- **codex:** "Open Codex in the project folder with `codex --sandbox danger-full-access` (the default sandbox blocks the headless Chrome that the gate uses). Start the request with 'Use the ai-diagrams skill'."
- **kiro:** "Run `kiro-cli chat --agent ai-diagrams` in the project folder, or pick the `ai-diagrams` agent with `/agent`. Start the request with 'Use the ai-diagrams skill'."

Also say: "Drawing quality depends on the model. Use a frontier model. Weak models get coordinates wrong, need more gate rounds and may never pass."

In every case, show the user the eleven diagram types and point them to `exemplos/<type>/prompt.md` for sample requests:

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
| State machine | `exemplos/maquina-estados/` |
| C4 container diagram | `exemplos/c4/` |
