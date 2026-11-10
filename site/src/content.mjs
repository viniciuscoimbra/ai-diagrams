// Content for the static review boards, sourced from the approved sitemap and repository docs.
export const content = {
  "types": [
    {
      "id": "aws-architecture",
      "name": "AWS architecture poster",
      "family": "architecture",
      "question": "Which services exist, and how does a request move through them?",
      "advantage": "Official icons, account and zone frames, and numbered arrows show the flow in order.",
      "summary": "Services, boundaries and the path of a request.",
      "modelType": "AWS architecture poster"
    },
    {
      "id": "step-flow",
      "name": "Numbered-step flow",
      "family": "process",
      "question": "In what order do things happen between systems?",
      "advantage": "Each arrow has a number and an adjacent label, so the story can be read without a separate legend.",
      "summary": "The order of actions across systems.",
      "modelType": "Numbered-step flow"
    },
    {
      "id": "c4",
      "name": "C4 container diagram",
      "family": "architecture",
      "question": "Who uses the system, how is it divided, and what does it depend on?",
      "advantage": "C4 level 2 notation with a fixed legend and numbered relations labeled with their technology.",
      "summary": "People, containers and system dependencies.",
      "modelType": "C4 container diagram"
    },
    {
      "id": "sequence",
      "name": "Sequence diagram",
      "family": "process",
      "question": "Who calls whom, in what order, and what comes back?",
      "advantage": "Activation bars, alt frames and loops are calculated by coordinates, without automatic layout.",
      "summary": "Calls, responses and conditional interactions.",
      "modelType": "Sequence diagram"
    },
    {
      "id": "swimlanes",
      "name": "Swimlanes",
      "family": "process",
      "question": "Who owns each step of the process?",
      "advantage": "One lane per team makes handoffs between teams visible.",
      "summary": "Steps and handoffs, organized by owner.",
      "modelType": "Swimlanes"
    },
    {
      "id": "bpmn",
      "name": "BPMN 2.0",
      "family": "process",
      "question": "What is the formal process, and can it be edited later?",
      "advantage": "Produces a .bpmn file that opens in Camunda and bpmn.io, alongside the PNG.",
      "summary": "A formal process with an editable BPMN source.",
      "modelType": "BPMN 2.0"
    },
    {
      "id": "state-machine",
      "name": "State machine",
      "family": "process",
      "question": "Which states can an entity enter, and what triggers each change?",
      "advantage": "The graph gate rejects unreachable states, non-final states without an exit, and transitions out of a final state.",
      "summary": "States, events and allowed transitions.",
      "modelType": "State machine"
    },
    {
      "id": "er-schema",
      "name": "ER diagram per schema",
      "family": "data",
      "question": "Which tables exist, and how are they related?",
      "advantage": "Starts from DDL, with crow's-foot notation, one schema per diagram, table roles in color and a fixed legend.",
      "summary": "Tables, keys and relations within a schema.",
      "modelType": "ER diagram per schema"
    },
    {
      "id": "dependency-matrix",
      "name": "Schema dependency matrix",
      "family": "data",
      "question": "Which schema depends on which?",
      "advantage": "Shows coupling between schemas without drawing hundreds of arrows.",
      "summary": "Dependencies between schemas in a single matrix.",
      "modelType": "Schema dependency matrix"
    },
    {
      "id": "comparison-table",
      "name": "Comparison table",
      "family": "comparison",
      "question": "Which option should we choose, and why?",
      "advantage": "One criterion per row, one option per column, with the recommendation marked.",
      "summary": "Options compared against the same criteria.",
      "modelType": "Comparison table"
    },
    {
      "id": "card-catalog",
      "name": "Cards catalog",
      "family": "comparison",
      "question": "What is in the inventory, and who owns it?",
      "advantage": "The same structure across every card works for APIs, events, teams and products.",
      "summary": "A consistent inventory of items and their owners.",
      "modelType": "Cards catalog"
    }
  ],
  "families": [
    {
      "id": "architecture",
      "name": "Architecture"
    },
    {
      "id": "process",
      "name": "Process"
    },
    {
      "id": "data",
      "name": "Data"
    },
    {
      "id": "comparison",
      "name": "Comparison"
    }
  ],
  "comingSoon": [
    {
      "name": "C4 context and components",
      "description": "Levels 1 and 3, building on the existing container diagram."
    },
    {
      "name": "Network and VPC",
      "description": "Subnets, routes, endpoints and connections, without the business flow of an AWS poster."
    },
    {
      "name": "Timeline and roadmap",
      "description": "Milestones, phases and dependencies for presentation."
    },
    {
      "name": "DDD context map",
      "description": "Bounded contexts and the relationships between them."
    },
    {
      "name": "Data flow diagram",
      "description": "Where data comes from, where it is stored and where it goes, with its classification."
    },
    {
      "name": "User journey",
      "description": "Stages, channels and friction points arranged in bands."
    },
    {
      "name": "Decision tree",
      "description": "Questions, answers and outcomes for business rules and triage."
    },
    {
      "name": "Organization chart and RACI",
      "description": "Responsibility shown as a tree or a matrix."
    }
  ],
  "install": [
    {
      "id": "npm",
      "label": "npm",
      "command": "npx ai-diagrams install --claude\n\n# Or install the CLI globally.\nnpm install -g ai-diagrams\nai-diagrams install --claude\nai-diagrams doctor",
      "expected": "The skill is installed for the selected CLI. doctor reports Python 3, Chrome and Node availability.",
      "usage": "Use --codex or --kiro instead of --claude. For a project installation, add --project <PROJECT>.",
      "note": "An existing installation is never replaced without confirmation. Keep the package installed while linked skills are in use."
    },
    {
      "id": "claude",
      "label": "Claude Code",
      "command": "# 1. Clone or update: run each command separately.\nls <AI_DIAGRAMS>/.git\n# If the repository exists:\ngit -C <AI_DIAGRAMS> pull\n# If ls reports No such file or directory:\ngit clone https://github.com/viniciuscoimbra/ai-diagrams.git <AI_DIAGRAMS>\nls <AI_DIAGRAMS>/skills/ai-diagrams/SKILL.md\n\n# 2. Install: inspect the destination before creating a link.\nmkdir -p ~/.claude/skills\nls -la ~/.claude/skills/ai-diagrams\n# Only if ls reports No such file or directory:\nln -s <AI_DIAGRAMS>/skills/ai-diagrams ~/.claude/skills/ai-diagrams\n\n# 3. Check the installed skill.\nls ~/.claude/skills/ai-diagrams/SKILL.md",
      "expected": "Clone: Cloning into '<AI_DIAGRAMS>'... with no fatal line. Update: Already up to date. or a list of changed files. mkdir and ln: no output. Final check: ~/.claude/skills/ai-diagrams/SKILL.md, expanded to the full path.",
      "usage": "Open Claude Code in the project folder and describe the diagram in plain language. Start the request with 'Use the ai-diagrams skill'.",
      "note": "If the destination is a regular folder, stop and ask before replacing the old copy. An existing link does not need to be created again."
    },
    {
      "id": "codex",
      "label": "Codex CLI",
      "command": "# 1. Clone or update: run each command separately.\nls <AI_DIAGRAMS>/.git\n# If the repository exists:\ngit -C <AI_DIAGRAMS> pull\n# If ls reports No such file or directory:\ngit clone https://github.com/viniciuscoimbra/ai-diagrams.git <AI_DIAGRAMS>\nls <AI_DIAGRAMS>/skills/ai-diagrams/SKILL.md\n\n# 2. Install: inspect the destination before creating a link.\nmkdir -p ~/.codex/skills\nls -la ~/.codex/skills/ai-diagrams\n# Only if ls reports No such file or directory:\nln -s <AI_DIAGRAMS>/skills/ai-diagrams ~/.codex/skills/ai-diagrams\n\n# 3. Check the installed skill.\nls ~/.codex/skills/ai-diagrams/SKILL.md",
      "expected": "Clone: Cloning into '<AI_DIAGRAMS>'... with no fatal line. Update: Already up to date. or a list of changed files. mkdir and ln: no output. Final check: ~/.codex/skills/ai-diagrams/SKILL.md, expanded to the full path.",
      "usage": "Open Codex in the project folder with `codex --sandbox danger-full-access` (the default sandbox blocks the headless Chrome that the gate uses). Start the request with 'Use the ai-diagrams skill'.",
      "note": "If the destination is a regular folder, stop and ask before replacing the old copy. An existing link does not need to be created again."
    },
    {
      "id": "kiro",
      "label": "Kiro CLI",
      "command": "# 1. Clone or update: run each command separately.\nls <AI_DIAGRAMS>/.git\n# If the repository exists:\ngit -C <AI_DIAGRAMS> pull\n# If ls reports No such file or directory:\ngit clone https://github.com/viniciuscoimbra/ai-diagrams.git <AI_DIAGRAMS>\nls <AI_DIAGRAMS>/skills/ai-diagrams/SKILL.md\n\n# 2. Install a local copy inside the project.\nbash <AI_DIAGRAMS>/tools/install-kiro.sh <PROJECT>\n\n# 3. Validate the installed agent.\nkiro-cli agent validate --path <PROJECT>/.kiro/agents/ai-diagrams.json",
      "expected": "Clone: Cloning into '<AI_DIAGRAMS>'... with no fatal line. Update: Already up to date. or a list of changed files. Install: four lines starting with steering:, agent:, skill: and templates:. The last is templates: 11 of 11. Validation: no error message.",
      "usage": "Run `kiro-cli chat --agent ai-diagrams` in the project folder, or pick the `ai-diagrams` agent with `/agent`. Start the request with 'Use the ai-diagrams skill'.",
      "note": "Kiro needs the copied skill inside <PROJECT>/.kiro/. Do not use a symlink."
    }
  ],
  "installRules": "Choose the CLI and absolute project and skill paths first. Replace <AI_DIAGRAMS> and <PROJECT> with those paths, expanding ~. Run each command separately, without pipes or extra &&. Compare each result with the expected output. If it differs, stop and inspect it. Never replace an existing regular skill folder without permission.",
  "installPrerequisites": [
    {
      "command": "git --version",
      "expected": "git version 2. followed by numbers.",
      "note": "The repository is public. No password, token or key is needed."
    },
    {
      "command": "python3 --version",
      "expected": "Python 3.9 or later.",
      "note": "Used by the generators and gates."
    },
    {
      "command": "python3 -c \"import diagrams; print('diagrams ok')\"",
      "expected": "diagrams ok",
      "note": "If the module is missing, run pip3 install diagrams and repeat. If pip reports externally-managed-environment, INSTALL.md specifies pip3 install --user --break-system-packages diagrams. The package supplies the official AWS icons."
    },
    {
      "command": "node --version",
      "expected": "v18 or later.",
      "note": "If missing, install Node LTS before continuing."
    },
    {
      "command": "ls \"/Applications/Google Chrome.app\"",
      "expected": "Contents",
      "note": "On Linux, run which google-chrome and expect a path. For another installation path, use POSTER_CHROME in the smoke test."
    },
    {
      "command": "claude --version\n# Or: codex --version\n# Or: kiro-cli --version",
      "expected": "A version number.",
      "note": "Check only the CLI you selected."
    }
  ],
  "smokeTest": {
    "command": "python3 <AI_DIAGRAMS>/skills/ai-diagrams/scripts/build.py <AI_DIAGRAMS>/skills/ai-diagrams/templates/05-comparison-table/_src/05-messaging-comparison.html --out /tmp",
    "expected": "Two lines starting with OK. The last ends in 05-messaging-comparison.png.",
    "note": "Checks Python, AWS icons, Chrome and the gate. Chrome not found: set POSTER_CHROME to the installed path. AWS icons not found: install diagrams with the same python3."
  },
  "aws": {
    "originalLabel": "Example",
    "when": "Use an AWS architecture poster when you need to show which services handle a request, the account or zone boundaries, and the numbered path through them.",
    "advantages": [
      "Official AWS service icons make the components identifiable.",
      "Account and zone frames show the boundaries of the system.",
      "Numbered arrows and a matching step list explain the order of the request."
    ],
    "avoid": "For calls and responses over time, use a sequence diagram. For a technology-neutral system decomposition, use the C4 container diagram. For a comparison of alternatives, use a comparison table.",
    "gate": [
      "Arrow ends touch a box or frame border, within a 6 px tolerance.",
      "Arrows do not cross unrelated boxes or share a collinear segment.",
      "Badges 1..N match the step list, and each badge sits on its arrow.",
      "Measured labels, icons, badges and chips do not overlap; arrows do not pass over text.",
      "Edge labels stay within 30 px of an arrow; arrowheads do not end inside a box.",
      "Nothing crosses the page width or the capture height.",
      "Colors and fonts use the selected theme tokens; the source includes its style marker."
    ],
    "gateFailure": "BADGE-SOLTO: a step badge sits away from its arrow. Move its center onto the arrow line, then run the gate again.",
    "gateLimit": "The gate measures geometry. It does not replace reading the PNG: small margin errors and confusing composition can still pass."
  },
  "bestModelsNote": "These are measured passing options, not a ranking. Most cells come from one run before the theme changed. Repeated runs and tests after the latest skill changes are still needed."
};
