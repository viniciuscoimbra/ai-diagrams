# BPMN 2.0

A process in native BPMN, editable in Camunda Modeler or at demo.bpmn.io. Nobody draws SVG or writes XML: the model is a JSON file, and `bpmn/build_bpmn.py` computes the layout, routes the connections and emits BPMN 2.0 with BPMNDI. The rendering is done by bpmn-js 18.31.0, bundled in `bpmn/vendor/` with its license (the bpmn.io logo stays on the drawing, as the license requires).

Template: `templates/08-bpmn/`, in the skill folder.

## When it is BPMN and when it is swimlanes

BPMN when the request says BPMN, process, gateway, event, or when the result needs to be editable in a process tool. A flow between teams without that requirement goes to swimlanes (`references/swimlanes.md`), which reads better in a document.

## JSON model

```json
{
  "id": "contestacao",
  "title": "Contestação de pagamento",
  "subtitle": "one or two factual sentences",
  "header": ["Company · Project", "08 · BPMN · V1"],
  "footer": "Author · Project · YYYY-MM",
  "lanes": [{"id": "cliente", "name": "Cliente"}, {"id": "ops", "name": "Operações"}],
  "nodes": [
    {"id": "inicio", "type": "startEvent", "name": "Cliente contesta", "lane": "cliente", "col": 0},
    {"id": "analisar", "type": "task", "name": "Analisar transação", "lane": "ops", "col": 1},
    {"id": "procede", "type": "exclusiveGateway", "name": "Procede?", "lane": "ops", "col": 2}
  ],
  "flows": [{"from": "inicio", "to": "analisar"}, {"from": "procede", "to": "fim", "name": "Sim"}]
}
```

The sample content is in pt-BR, like the template; write it in the language the user asks for.

| Field | Rule |
|---|---|
| `type` | `startEvent`, `endEvent`, `task`, `callActivity`, `exclusiveGateway`, `parallelGateway`, `intermediateCatchEvent`, `intermediateThrowEvent` |
| `event` | optional: `timer`, `message` or `condition` (with `condition`) |
| `lane` | who actually performs the activity |
| `col`, `row` | column from 0 to 6 (width 240); `row: 1` opens a second row in the same lane, for an alternative or a return |
| `name` | `\n` breaks the line inside the task |
| `doc` | optional: text or object, becomes the element's `documentation` |
| `flows[].name` | required on every branch that leaves a decision |
| `flows[].via` | `top` or `bottom` forces the exit from the top or the bottom, so returns do not cross tasks |
| `columnWidth`, `laneHeight` | optional, at the top level of the model |

Legible diagram: up to seven columns, four to six lanes, up to eighteen activities. Every path ends in an `endEvent`. Two paths that end in the same place stay in the same lane, on different rows, so the arrows do not run stuck together.

## Gate

`build_bpmn.py` only writes output with everything at zero:

- `STRUCTURE`: unique ids, connection to an existing node, node without an incoming flow (except start) or without an outgoing flow (except end), decision branch without a label, nonexistent type or lane;
- `REACHABILITY`: every node is reached from a start and reaches an end;
- `OVERLAP`: two shapes in the same position;
- `IMPORT-FAILED`: bpmn-js imports the XML in Chrome with no error and no warning.

## Commands

```bash
python3 <skill>/bpmn/build_bpmn.py diagrams/_src/NN-process.json
```

It generates `NN-process.bpmn` (the editable file, which goes into git), `NN-process.html` (offline viewer) and `NN-process.png`. Look at the PNG: an arrow running stuck to another or a label far from its branch calls for another `col`, `row` or `via`.
