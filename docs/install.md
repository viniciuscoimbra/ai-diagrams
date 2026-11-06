# Install

ai-diagrams runs fully inside Claude Code, Codex CLI and Kiro CLI: the AI writes the diagram source, runs the gate and builds the PNG. Claude.ai Projects and ChatGPT can use ai-diagrams as a knowledge base: the AI writes the source, and you build the PNG on your machine.

Each step has a command, the expected output and what to do if something else appears. Commands are for macOS and Linux. On Windows, use WSL.

Program output is in Portuguese. This page quotes it as printed, with a translation in parentheses.

To have an AI agent install ai-diagrams for you, give it [INSTALL.md](../INSTALL.md).

## Install with npm

The package is prepared locally and is not published yet. After publication, use:

```bash
npx ai-diagrams install --claude
```

Replace `--claude` with `--codex` for Codex. These commands create the same global skill links as the git clone route below. Add `--projeto /path/to/project` for a project-local link in `.claude/skills/` or `.codex/skills/`. Use exactly one CLI flag.

Kiro gets copies of the skill, steering file and agent:

```bash
npx ai-diagrams install --kiro --projeto /path/to/project
```

Without `--projeto`, Kiro uses the current directory. The installer asks before replacing an existing installation. In a non-interactive terminal it refuses conflicts and preserves the files. Approved replacement prints the backup locations; the originals remain in those sibling `.ai-diagrams-backup-*` folders. A failed installation restores them automatically. Repeating an identical Claude/Codex link is safe.

To keep the command installed globally:

```bash
npm install -g ai-diagrams
```

```bash
ai-diagrams install --claude
```

Installing the npm package adds the command; `install --claude`, `--codex` or `--kiro` registers the skill. The `npx` route links to npm's cache, so repeat it after clearing that cache. The global route keeps the package under npm's global prefix.

```bash
ai-diagrams doctor
```

Use `npx ai-diagrams doctor` if the command is not installed globally. Expected: `OK` for Node 18+, Python 3.9+, Chrome and AWS icons. Missing requirements report `FALHA` and exit 1. The doctor reuses the engine's Chrome/icon detection, including `POSTER_CHROME` and `POSTER_ICONBASE`, without starting Chrome. Follow the requirement instructions below for anything missing. npm does not install Python, Chrome or the Python `diagrams` package.

Existing files use the same entry point:

```bash
ai-diagrams importar process.mmd --saida diagramas --idioma en
```

See [supported import formats](importing.md). Installation does not run the PNG gates; the import command does unless `--somente-fonte` is explicitly selected.

### Test the unpublished package

From the repository root:

```bash
npm pack --pack-destination /tmp
```

```bash
bash testes/npm-smoke.sh /tmp/ai-diagrams-0.1.0.tgz
```

The smoke test installs the local archive offline in a temporary npm prefix with a temporary HOME, checks Claude/Codex links, project scope, Kiro copies, conflict preservation and importer dispatch, then removes the temporary files. Running `bash testes/npm-smoke.sh` without an archive builds one first. Neither command publishes anything or logs in to npm.

## Install with git clone

The existing route below remains available before npm publication.

## 1. Requirements (all tools that build PNGs)

| Item | Used for | Check |
|---|---|---|
| Git | cloning the repository | `git --version` |
| Python 3.9+ | gate and PNG | `python3 --version` |
| `diagrams` pip package | official AWS icons | `python3 -c "import diagrams"` |
| Node 18+ | ER diagram, dependency matrix and state machine | `node --version` |
| Google Chrome | rendering and measuring in headless mode | `ls "/Applications/Google Chrome.app"` |

### Python

```bash
python3 --version
```

**Expected:** `Python 3.9` or later, for example `Python 3.12.4`.

**If you get** `command not found`: install Python 3. On macOS, `brew install python`. On Ubuntu, `sudo apt install python3 python3-pip`.

### AWS icons

```bash
pip3 install diagrams
```

**Expected:** ends with `Successfully installed diagrams-...` or `Requirement already satisfied: diagrams`.

**If you get** `externally-managed-environment`: run `pip3 install --user --break-system-packages diagrams`. The package only provides the icon files. None of its code runs.

### Node

```bash
node --version
```

**Expected:** `v18` or later, for example `v22.11.0`.

**If you get an error:** install Node LTS from nodejs.org or with `brew install node`.

### Chrome

```bash
ls "/Applications/Google Chrome.app"
```

**Expected:** `Contents`.

**If you get** `No such file or directory`: install Google Chrome. If Chrome is installed in another location, or on Linux under another name, point the scripts to it:

```bash
export POSTER_CHROME="/path/to/chrome"
```

### Clone the repository

Go to the folder where you want to keep ai-diagrams and clone it there:

```bash
git clone https://github.com/viniciuscoimbra/ai-diagrams.git
```

**Expected:** `Cloning into 'ai-diagrams'...` and no error line.

The next commands use two variables. If you open a new terminal, set them again:

```bash
export AI_DIAGRAMS="$PWD/ai-diagrams"
```

```bash
export PROJECT="/path/to/your/project"
```

Replace `/path/to/your/project` with your project folder.

### Smoke test

This builds the PNG of one reference model into a temporary folder. It checks Python, the icons, Chrome and the gate in one run.

```bash
python3 "$AI_DIAGRAMS"/skills/ai-diagrams/scripts/build.py "$AI_DIAGRAMS"/skills/ai-diagrams/modelos/05-tabela-comparacao/_src/05-comparacao-mensageria.html --out /tmp
```

**Expected:** two lines starting with `OK`. The last one ends in `05-comparacao-mensageria.png`.

**If you get** `Chrome não encontrado` (Chrome not found): set `POSTER_CHROME` as shown above. **If you get** `Ícones AWS não encontrados` (AWS icons not found): the `diagrams` package is not installed for this `python3`. Run `python3 -m pip install diagrams`.

## 2. Claude Code

### Link the skill

```bash
mkdir -p ~/.claude/skills && ln -s "$AI_DIAGRAMS"/skills/ai-diagrams ~/.claude/skills/ai-diagrams
```

**Expected:** no output.

**If you get** `File exists`: a skill with this name is already installed. If it is an old copy, remove it with `rm -rf ~/.claude/skills/ai-diagrams` and repeat.

### Check the link

```bash
ls ~/.claude/skills/ai-diagrams/SKILL.md
```

**Expected:** the file path.

**If you get** `No such file or directory`: `$AI_DIAGRAMS` was not set when you created the link. Remove the link with `rm ~/.claude/skills/ai-diagrams`, set `AI_DIAGRAMS` and repeat the previous step.

### First diagram

```bash
cd "$PROJECT" && claude
```

**Expected:** Claude Code opens. Start the request with "Use the ai-diagrams skill", then paste a prompt from `exemplos/<type>/prompt.md` together with the data file in the same folder.

**Result:** Claude writes the source in `diagramas/_src/`, runs the gate until it passes, opens the PNG to check it and delivers `diagramas/<name>.png`. If the gate does not pass after five rounds, it delivers the source and the gate output and says the gate failed.

**If Claude does not use the skill:** start the request with "Use the ai-diagrams skill". If Claude says it does not know the skill, exit with `/exit` and open it again. The skill list is read at startup.

## 3. Codex CLI

### Check Codex

```bash
codex --version
```

**Expected:** `codex-cli` followed by a version.

**If you get an error:** install it with `npm install -g @openai/codex` and log in with `codex login`.

### Link the skill

```bash
mkdir -p ~/.codex/skills && ln -s "$AI_DIAGRAMS"/skills/ai-diagrams ~/.codex/skills/ai-diagrams
```

**Expected:** no output.

**If you get** `File exists`: if it is an old copy, remove it with `rm -rf ~/.codex/skills/ai-diagrams` and repeat.

```bash
ls ~/.codex/skills/ai-diagrams/SKILL.md
```

**Expected:** the file path.

### First diagram

The gate starts headless Chrome. The default `workspace-write` sandbox blocks Chrome, and the gate ends with `MEDICAO-FALHOU` (measurement failed). Run Codex with full access:

```bash
cd "$PROJECT" && codex --sandbox danger-full-access
```

**Expected:** Codex opens. Start the request with "Use the ai-diagrams skill" and paste a prompt from `exemplos/<type>/prompt.md` with its data file.

To keep the sandbox, open plain `codex` and approve each `python3` or `node` command from the skill when Codex asks to run it outside the sandbox.

Non-interactive run:

```bash
codex exec --sandbox danger-full-access -C "$PROJECT" "Use the ai-diagrams skill. Comparison table of SQS, Kinesis and MSK. No client name in the header."
```

**If you get** `MEDICAO-FALHOU` or Chrome does not respond: the sandbox blocked Chrome. Use `--sandbox danger-full-access` or approve the command outside the sandbox.

**If a source file in `_src/` is hundreds of KB:** Codex embedded fonts or icons in the source. Ask it to go back to the `/*ESTILO*/` marker, `aws://` icon references and the Google Fonts link, as `SKILL.md` requires.

## 4. Kiro CLI

Kiro does not read files outside the project through a symlink. The install script copies the skill, a steering file and the `ai-diagrams` agent into the project.

### Check Kiro

```bash
kiro-cli --version
```

**Expected:** `kiro-cli` followed by a version.

**If you get an error:** install Kiro from kiro.dev. If you only use the Kiro IDE, skip this check.

### Copy the skill into the project

```bash
bash "$AI_DIAGRAMS"/ferramentas/instalar-kiro.sh "$PROJECT"
```

**Expected:** four lines:

```text
steering: <PROJECT>/.kiro/steering/ai-diagrams.md
agente:   <PROJECT>/.kiro/agents/ai-diagrams.json
skill:    <PROJECT>/.kiro/skills/<skill folder>
modelos:  11 de 11
```

The script creates the project folder if it does not exist. It copies real files, not symlinks. The steering file tells Kiro to use the skill for every diagram request and not to write helper scripts. The `ai-diagrams` agent can read files, write to `diagramas/` and run the skill's `python3` and `node` commands.

**If you get** `No such file or directory` from `cp`: the skill path in the script does not match the repository. Run `git -C "$AI_DIAGRAMS" pull` and repeat.

### Validate the agent

```bash
kiro-cli agent validate --path "$PROJECT"/.kiro/agents/ai-diagrams.json
```

**Expected:** no error message.

### First diagram

```bash
cd "$PROJECT" && kiro-cli chat --agent ai-diagrams
```

**Expected:** the Kiro chat opens with the `ai-diagrams` agent. In the IDE, open the project folder and pick the `ai-diagrams` agent with `/agent`.

Start the request with "Use the ai-diagrams skill" and attach the data file with `#File`:

```text
Use the ai-diagrams skill. Comparison table of Aurora PostgreSQL, DynamoDB and DocumentDB for the account statement, from #File criterios.yaml. No client name in the header.
```

Non-interactive run:

```bash
kiro-cli chat --agent ai-diagrams --no-interactive --trust-workspace "Use the ai-diagrams skill. Comparison table of SQS, Kinesis and MSK. No client name in the header."
```

Pick the model with `/model` in the chat or `--model` on the command line.

| Symptom | What to do |
|---|---|
| Kiro answers in markdown instead of drawing | check that the skill was copied, not linked, and start the request with "Use the ai-diagrams skill" |
| `[denied] tool permission` when reading `SKILL.md` | the skill is a symlink; run `instalar-kiro.sh` again |
| a command with a pipe or `2>&1` is denied | the agent only allows the plain command; ask Kiro to run it without a pipe |
| Kiro created `run-build.py`, `build-*.sh` or another script | delete it and repeat the request; the right command is in `SKILL.md` |
| `The request was throttled by the service` | wait a minute and repeat the same request |

## 5. Without a CLI: Claude.ai Projects and ChatGPT

Claude.ai Projects and ChatGPT (Custom GPT or Project) use ai-diagrams as a knowledge base. The AI only writes the diagram source. It cannot run the gate or build the PNG, because those environments have no Chrome and no AWS icon set. You build the PNG on your machine.

### Build the package

```bash
bash "$AI_DIAGRAMS"/ferramentas/empacotar.sh
```

**Expected:** two lines listing `ai-diagrams-kb.zip` and `ai-diagrams-skill.zip`, then `arquivos na KB: 24` (24 files in the knowledge base). The files are in `"$AI_DIAGRAMS"/dist/`. The folder `dist/kb/` has the 24 files unpacked.

**If you get** `zip: command not found`: install zip (`sudo apt install zip`; macOS ships with it).

| File in `dist/kb/` | Content |
|---|---|
| `00-INSTRUCOES.md` | instructions for the AI. Goes in the instructions field, not the knowledge files |
| `01-roteador-SKILL.md` | the router and the cycle of each type |
| `02` to `09-ref-*.md` | the visual language and one reference per type |
| `10` to `12` | the two CSS files and the poster template |
| `20` to `30-modelo-*` | one working source per type |

The bpmn-js bundle and the PNGs are left out. The AI does not need them. `dist/` is generated and is not tracked by git. Run the command again after each `git pull`.

### Upload

| Tool | Instructions | Files |
|---|---|---|
| Claude.ai Project | paste `00-INSTRUCOES.md` into the Project instructions | upload the other 23 files to the Project knowledge |
| ChatGPT Custom GPT | Configure, Instructions: paste `00-INSTRUCOES.md` | Configure, Knowledge: upload the other 23 files; turn on code execution |
| ChatGPT Project | paste `00-INSTRUCOES.md` into the Project instructions | upload the other 23 files to the Project files |

Claude.ai also accepts `dist/ai-diagrams-skill.zip` as an uploaded skill, on plans with code execution. The package shortens the skill description to the 200-character limit of Claude.ai. Upload the zip from `dist/`, not one you built by hand: the zip must have the skill folder at its root with `SKILL.md` inside.

**If upload fails on file count:** limits depend on the plan. Upload `01-roteador-SKILL.md`, the references and the models of the types you use most.

### Request a diagram

Start the request with "Use the ai-diagrams skill", paste a prompt from `exemplos/<type>/prompt.md` and attach the data file from the same folder.

**Expected:** the AI returns the source file and the command that builds the PNG.

### Build the PNG on your machine

Complete section 1 first. You do not need a CLI.

1. Save the source file in `diagramas/_src/` inside your project.
2. Run the command the AI gave you. For a comparison table:

```bash
python3 "$AI_DIAGRAMS"/skills/ai-diagrams/scripts/build.py "$PROJECT"/diagramas/_src/05-comparacao.html
```

**Expected:** two lines starting with `OK`. The last one is the PNG path in `"$PROJECT"/diagramas/`.

**If the gate fails:** paste the output into the chat. The AI fixes the source and you run the command again.

**If the AI says it generated the PNG:** it did not. Ask for the source and the command, and build it on your machine.

## Errors in every tool

| Message or symptom | What to do |
|---|---|
| the AI answers in plain text, markdown or Mermaid | start the request with "Use the ai-diagrams skill" |
| `Ícones AWS não encontrados` (AWS icons not found) | `diagrams` is not installed for the same Python; run `python3 -m pip install diagrams` |
| `Chrome não encontrado` (Chrome not found) | install Chrome or export `POSTER_CHROME` with its path |
| `O Chrome não respondeu a tempo` (Chrome timed out) | check the network (fonts load from Google Fonts) and close stuck headless Chrome processes |
| `node: command not found` | install Node 18 or later |
| `LINT REPROVOU`, `BPMN REPROVOU` or `TRANSBORDA` | the gate found a defect in the drawing; the AI fixes the source and runs it again. If it stops, paste the output into the chat |

## Update

For the global npm package, run `npm install -g ai-diagrams@latest`, then repeat the `ai-diagrams install` command for your tool. For `npx`, repeat `npx ai-diagrams@latest install` with the same tool and project options. Confirm replacement in an interactive terminal if prompted; Kiro needs its copied files refreshed.

For a git clone:

```bash
git -C "$AI_DIAGRAMS" pull
```

**Expected:** `Already up to date.` or a list of changed files.

- Claude Code and Codex: the symlink picks up the update.
- Kiro: run `bash "$AI_DIAGRAMS"/ferramentas/instalar-kiro.sh "$PROJECT"` again. It replaces the old copy.
- Knowledge base: run `bash "$AI_DIAGRAMS"/ferramentas/empacotar.sh` again and replace the uploaded files.
