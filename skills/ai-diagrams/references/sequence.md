# Sequence diagram

Who calls whom, in which order, and who waits for the reply. A participant is a column, a message is a row, time goes down. It uses `assets/style-conceptual.css` and the `scripts/conceptual.py` gate.

Template: `templates/09-sequence/`, in the skill folder.

## When to use

- calls between services, API, database, queue or external system, where the order and the waiting matter: "what happens when the app calls X";
- a protocol with a round trip (authentication, payment, partner integration);
- an alternative path or a repetition inside the same conversation (`alt`, `loop`, `opt`).

If the drawing is about where each service lives and how it connects (network, account, layer), it is a poster. If the rows are teams and the subject is who does what, it is swimlanes. If the question is the topology with numbered steps on top, it is a flow with steps.

## Spec (`build_sequence.py`)

The coordinates are computed from the JSON; nobody writes pixels.

```json
{
  "page_title": "09 · Pix de saída",
  "header": ["<Project> · <subject>", "09 · Sequência"],
  "kicker": "Diagrama de sequência",
  "h1": "Pix de saída: da chamada do app à confirmação do SPI",
  "sub": "one to three sentences: what the drawing shows, the scope and how to read it",
  "participants": [
    {"id": "app", "name": "App do cliente", "sub": "iOS e Android", "type": "actor", "icon": "aws://general/mobile-client.png"},
    {"id": "pix", "name": "Serviço Pix", "sub": "ECS Fargate", "type": "service", "icon": "aws://compute/fargate.png"},
    {"id": "spi", "name": "SPI · ICOM", "sub": "Banco Central", "type": "external"}
  ],
  "messages": [
    {"from": "app", "to": "pix", "text": "`POST /pix`", "step": "what happens in this step"},
    {"from": "pix", "to": "pix", "text": "confere limite"},
    {"note": "limite diário vem do cadastro", "over": "pix"},
    {"fragment": "alt", "branches": [
      {"guard": "score abaixo de 0,8", "messages": [
        {"from": "pix", "to": "spi", "text": "`pacs.008`", "type": "async"}
      ]},
      {"guard": "score a partir de 0,8", "messages": []}
    ]},
    {"from": "pix", "to": "app", "text": "`201`", "type": "reply"}
  ],
  "band": {"f1": "a fact about the flow", "f2": "what was left out of the drawing"},
  "footer": ["<Project>", "Diagrama de sequência · YYYY-MM"]
}
```

The sample content is in pt-BR, like the template; write it in the language the user asks for.

- `participants`: in column order, from left to right. Put whoever starts on the left and the external system on the right. `type` accepts `actor`, `service`, `database`, `queue`, `external` (dashed border) and `system`; it becomes the label above the name. `icon` is optional, in the `aws://category/file.png` format checked in the icon collection. `name` in up to three words; `sub` short (technology or role).
- `messages`: in time order.
  - `type`: `sync` (default, filled arrow), `async` (open arrow) or `reply` (dashed).
  - `text` short. A stretch between backticks becomes code: endpoint, event, field, HTTP status.
  - `from` equal to `to` draws the self-message loop.
  - `step` numbers the message: the badge goes on the arrow, and the text goes in the "Steps" section below the drawing. Number only the messages the reader needs to understand. Obvious round trips get no step.
- `note` + `over`: a dashed box over the participant's lifeline, for a rule or a piece of data that is not a message.
- `fragment`: `alt` (alternative paths, one branch per guard), `loop` (repetition, one branch with the stop condition) or `opt` (one branch that may not happen). Fragments nest. The guard is the condition in short text, without brackets.
- The "Notation" section comes out on its own, only with the arrow types used.

## What the generator decides

- **Activation bar**: a synchronous call opens the bar on the target. The first `reply` from the target to the caller closes the bar. Without a reply, the bar runs until the participant's last message. Always write the reply when the waiting matters.
- **Label**: it sits in the gap next to the source, on the side the arrow goes toward. The gap widens until the label fits; past 228px, the label wraps into lines. Text never crosses a lifeline.
- **Width**: with six participants and short labels, the canvas stays near 1300px. Above 1320, the source declares `<meta name="width">` and the page grows. Seven participants is the comfortable limit. With more than that, split the conversation into two diagrams or group participants.

## Commands

```bash
python3 <skill>/scripts/build_sequence.py diagrams/_src/NN-name.json
python3 <skill>/scripts/conceptual.py diagrams/_src/NN-name.html
```

An undeclared participant makes the generator stop with a message. The gate is the conceptual one (list in `references/swimlanes.md`), with one extra rule:

- `TEXT-OVER-LIFELINE`: a label, fragment guard or branch name on top of a lifeline or an activation bar.

If it fails, shorten the label, change the order of the participants or move the message into a step. Do not edit the generated HTML: it is rebuilt on every round.

## When reading the PNG

- every arrow touches the target's bar or lifeline;
- no activation bar stays open without a reason (missing `reply`?);
- each branch's guard fits on the line and does not touch an arrow;
- the steps tell the story without needing to look at the drawing.
