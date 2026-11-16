# State machine

Which status a thing can be in and which event moves it from one to another. A state is a box, a transition is an arrow with the event written on it. It uses `assets/style-conceptual.css` and the `scripts/conceptual.py` gate.

Template: `templates/10-state-machine/`, in the skill folder.

## When to use

- lifecycle of an entity: order, payment, account, contract, ticket;
- a status stored in the database, and the question is "where can it go from where";
- a business rule that depends on the status ("only refund if it is Settled").

If the question is the order of the calls between systems, it is a sequence. If it is who does what between teams, it is swimlanes. If it is a process with tasks, gateways and BPMN events, it is BPMN.

## Spec (`build_states.py`)

The coordinates come from elkjs (`states/`, with license and origin in `states/vendor/`); the drawing belongs to this skill. Nobody writes pixels.

```json
{
  "page_title": "10 · Situação do Pix de saída",
  "header": ["ai-diagrams · <subject>", "10 · Máquina de estados"],
  "kicker": "Máquina de estados",
  "h1": "Pix de saída: situação da transferência",
  "sub": "one to three sentences: what the drawing shows and how to read it",
  "initial": "recebida",
  "states": [
    {"id": "recebida", "name": "Recebida", "desc": "o pedido chegou; nada foi debitado."},
    {"id": "analise", "name": "Em análise", "sub": "antifraude", "desc": "aguarda o score."},
    {"id": "recusada", "name": "Recusada", "final": true, "desc": "sem débito."}
  ],
  "transitions": [
    {"from": "recebida", "to": "analise", "event": "chave e limite ok", "action": "chama o antifraude"},
    {"from": "analise", "to": "recusada", "event": "score", "guard": "≥ 0,8"},
    {"from": "analise", "to": "analise", "event": "timeout", "guard": "tentativa < 3"}
  ],
  "band": {"f1": "a fact about the lifecycle", "f2": "what was left out of the drawing"},
  "footer": ["ai-diagrams", "Máquina de estados · YYYY-MM"]
}
```

The sample content is in pt-BR, like the template; write it in the language the user asks for.

- `initial`: id of the first state. The black dot points to it.
- `states`: in the order the thing's life usually moves; the layout respects that order.
  - `name` on one line, up to about 18 letters. A longer name makes the generator stop.
  - `sub`: short detail below the name (who decides, what is stored).
  - `desc`: sentence for the "States" section below the drawing. Write it for someone who will not look at the drawing.
  - `final: true`: double border. A final state has no exit.
  - `style`: `focus` (the state that matters) or `out` (error status), optional.
- `transitions`:
  - `event` is required: the fact that triggers the change. A stretch between backticks becomes code.
  - `guard`: condition without brackets; it comes out as `[condition]`.
  - `action`: what the system does on the change; it comes out as `/ action`.
  - `from` equal to `to` draws the loop (repetition in the same state).
- `direction`: `RIGHT` or `DOWN`, optional. Without it, the generator tries left to right and falls back to top-down if it goes past 1320px.
- The "Notation" section comes out on its own: initial dot, state, final state and label format.

## What the generator checks before drawing

It stops with `STATES FAILED <code>`:

- `NO-INITIAL`: `initial` is missing, or it is not in `states`;
- `UNKNOWN`: a transition names an id that is not in `states`;
- `NO-EVENT`: a transition without `event`;
- `LEAVES-FINAL`: a final state with an arrow leaving it;
- `UNREACHABLE`: no path from the initial state reaches the state;
- `NO-EXIT`: a non-final state with no exit to another state (the loop does not count). Either it is final, or the transition is missing.

## Commands

```bash
python3 <skill>/scripts/build_states.py diagrams/_src/NN-name.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-name.html
```

It needs `node` on the PATH, like the ER diagram. The drawing gate is the conceptual one (list in `references/swimlanes.md`). If it fails, shorten the label, split the guard or change the order of the states in the JSON. Do not edit the generated HTML: it is rebuilt on every round.

## When reading the PNG

- every arrow touches both states and the label sits against the right arrow;
- the final states have a double border and none has an exit;
- the happy path reads top to bottom or left to right without going back;
- the "States" section explains each status without needing the drawing.
