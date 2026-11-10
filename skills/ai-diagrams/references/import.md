# Importing existing files

Use `scripts/import_cli.py` when a diagram or data file already exists. The importer writes native sources and calls this skill's generators. It does not render through Mermaid and does not reuse the drawing from the XML. The original input is not changed.

```bash
python3 <skill>/scripts/import_cli.py file.mmd --out diagrams --lang pt-BR
python3 <skill>/scripts/import_cli.py schema.sql --type matrix --out diagrams --lang pt-BR
```

`ai-diagrams import` passes the same arguments through when the npm CLI is installed. The types are `er`, `matrix`, `catalog`, `comparison`, `bpmn`, `swimlanes`, `sequence`, `states` and `c4`, as compatible with the input format. The language changes the fixed labels; the authored text must already be in the desired language.

`--theme` accepts a theme name or path, as in the other generators. ER and matrix keep sources in `<out>/_src/<input-name>/` and deliverables in `<out>/<input-name>/`. Each input has its own report `<input-name>.import.json`, reset to pending before each attempt. `OUTPUT-CONFLICT` prevents replacing the original BPMN with the output; choose another directory. Input that is not UTF-8 returns `INPUT-INVALID`.

`--source-only` converts and generates the source without running Chrome. The output warns that the full gate and the PNG are pending. Do not present this mode as geometric approval. Without the flag, the command runs the generator and the usual gate.

## Mermaid

`.mmd` or `.mermaid` files, in UTF-8. One statement per line. Plain `%%` comments are accepted; `%%{...}%%` directives, configuration, front matter, styles and statements outside the subset fail with `MERMAID-UNSUPPORTED: line N`. Labels are plain text, without HTML.

### Flowchart and graph

Header `flowchart LR`, `flowchart TD`, `flowchart TB` or the `graph` form. The layout is recomputed; the original presentation direction is not a coordinate to preserve.

- Nodes by identifier, rectangles `A[Text]`, decisions `B{Question}` and circles `C((Text))`.
- One connection per statement: `A --> B` or `A -->|Label| B`. Nodes can be declared in the connection.
- Without `subgraph`, the output is BPMN: a rectangle becomes a task, a diamond becomes an exclusive gateway and a circle without an intermediate incoming/outgoing flow becomes a start/end.
- Roots and leaves without explicit circles get the start and end events required by the BPMN contract. The input's nodes and connections are preserved.
- With `subgraph id[Lane name]` and `end`, the output is swimlanes. Each node must belong to a lane. Only rectangular nodes, connections without labels and flows without cycles are accepted in this mode.
- It does not accept nested subgraphs, a node in two lanes, additional shapes, chained connections, dotted arrows or styles.

`subgraph` stands for an actor's responsibility. If the file uses it only for technical grouping, adapt the input before importing it as swimlanes. BPMN and swimlanes are the importer's representation choices, with no conversion to a free-form drawing.

### Sequence

Header `sequenceDiagram`. It accepts `participant id as Name`, `actor id as Name` and participants implied by the messages. Messages `A->>B: Text` are synchronous, `B-->>A: Text` are replies and `A-)B: Text` are asynchronous.

It accepts `Note over A: Text`, fragments `alt condition` / `else condition` / `end`, `loop condition` and `opt condition`, nested ones included. Explicit activation, `par`, `critical`, `break`, notes over several participants and other arrow forms fail. The generator decides the activation bars through the native contract.

### States

Header `stateDiagram-v2`. It accepts `state "Name" as id`, `[*] --> initial`, `A --> B: event`, `final --> [*]` and `direction LR` or `direction TB`. There is exactly one initial entry. Transitions between states require an event; final states have no exit.

Composite states, concurrency, history, notes, choices, guards and actions in additional syntax are not part of this subset. The native gate still checks reachability and exits.

### ER

Header `erDiagram`. Entities in `ENTITY { ... }` blocks, with `type name` attributes and an optional `PK`, `FK` or `UK` key. The entity must be declared; repeated attributes and entities fail. Quoted attribute comments also fail, because the columns of the native ER diagram have no display field for that text.

Accepted relationships: `PARENT ||..o{ CHILD : label` or `PARENT |o..o{ CHILD : label`. They are non-identifying relationships, with exactly one or zero/one parent, and zero/many children. An unambiguous `FK` column in the child entity must match the relationship. The inference uses the PK name or the entity name followed by the PK; if only one FK is available, it uses that column.

Other cardinalities, the identifying relationship `--`, composite keys and ambiguous relationships fail instead of getting an approximate cardinality. The models stay in the `public` schema.

## BPMN 2.0 XML

A `.bpmn` file with the namespace `http://www.omg.org/spec/BPMN/20100524/MODEL`, exactly one descriptive process (`isExecutable="false"` or omitted), optional lanes and an optional pool pointing to that process. The BPMNDI layout is replaced by the native layout.

Accepted nodes: `task`, `callActivity`, `startEvent`, `endEvent`, `exclusiveGateway`, `parallelGateway`, `intermediateCatchEvent` and `intermediateThrowEvent`. Connections are `sequenceFlow`; `incoming`, `outgoing` and `flowNodeRef`, when present, must point to the right elements. Plain-text documentation of the process and of the nodes is preserved.

Accepted events: message marker without `messageRef`, timer marker without a duration and condition with text in `conditionalEventDefinition/condition`. Timer and condition apply to a start or an intermediate catch. The engine is not a process executor.

It returns `BPMN-UNSUPPORTED` with the line for elements and attributes without a native equivalent. This includes specialized tasks (`userTask`, `serviceTask`, `scriptTask`), executable processes, subprocesses, boundary events, message flows, multiple pools, Camunda/Zeebe extensions, sequence flow conditions, `default` branch, timer duration, `calledElement`, lane/flow documentation and execution semantics. DTD, entities and XML processing instructions also fail. Do not remove these elements automatically to get an import that only looks successful.

The generated BPMN has its own IDs and coordinates. It is a new editable descriptive document, not a file to deploy to a workflow runtime.

## SQL DDL

A `.sql` file, with `CREATE SCHEMA` and `CREATE TABLE`. Simple identifiers, with an optional schema; without a schema, it uses `public`. It accepts simple types with optional precision, single-column PK and UNIQUE, `NOT NULL`, inline references or single-column `FOREIGN KEY`. FKs must point to tables present in the file. Simple default values stay in the converted model.

`--type er` is the default; `--type matrix` generates the matrix. Quoted identifiers, ALTER, indexes, checks, composite keys and other unsupported constructs return `SQL-UNSUPPORTED`. The automatic layout accepts up to 16 internal FKs per schema. FKs between schemas use the boundary and the native labels. The visual model does not replace the DDL for migrations.

## Catalog CSV

A comma-separated `.csv` file, with a header, two to five columns and one to ten data rows. The first column identifies the card; the others become its fields. The column names are visible text, so they must be translated. Quoted CSV fields are accepted. Repeated headers, empty fields or rows with a different number of columns return `CSV-UNSUPPORTED`.

## Comparison YAML

A `.yaml` or `.yml` file with this contract:

```yaml
title: Filas de mensagens
subtitle: Características operacionais
options:
  - SQS
  - Kinesis
criteria:
  - name: Consumo
    values: ["Fila", "Stream"]
```

Two to four options; each criterion has a `name` and one text value per option. `subtitle` is optional. Quoted strings and lists use JSON syntax. A complete JSON object with the same fields is also accepted, since it is a subset of YAML. Anchors, tags, multiline blocks, tabs, additional fields and other formats fail with `YAML-UNSUPPORTED`.

## Structurizr DSL

A `.dsl` file becomes the C4 model of `build_c4.py` and one page per view (see `references/c4.md`). Read: `workspace`, `model`, `views`, `group`, `enterprise`, `person`, `softwareSystem`, `container`, `component` (with `identifier =`, positional name, description, technology and tags, or the same fields as statements in the block), relationships `a -> b "description" "technology"` (also `-> b` and `this -> b` inside an element), `deploymentEnvironment`, `deploymentNode`, `infrastructureNode`, `containerInstance`, the views `systemLandscape`, `systemContext`, `container`, `component`, `dynamic`, `deployment` and `filtered` (with `include *` or identifiers, `exclude`, `title`, `description`, `autoLayout`), and `shape` in `styles` (`Cylinder`, `WebBrowser`, `Pipe`, `MobileDevicePortrait`, `MobileDeviceLandscape`). `!identifiers` (flat or hierarchical) and `!impliedRelationships` are accepted. Colors, `theme`, `branding`, `terminology`, `properties`, `perspectives` and `configuration` are read and ignored. `!include`, `!script`, `!docs`, `!adrs`, `softwareSystemInstance`, `custom` and `image` views, include expressions (`->a->`, `element.tag==`) and parallel blocks in dynamic views fail with `DSL-UNSUPPORTED` and the line. A reference to an identifier not declared before fails with `DSL-UNKNOWN`. The model rules still apply: a container, component or relationship without technology fails with `C4-NO-TECHNOLOGY`.

## Format references

The subset above is a decision of this importer. The full specifications have additional features: [Mermaid flowchart](https://mermaid.js.org/syntax/flowchart.html), [sequence](https://mermaid.js.org/syntax/sequenceDiagram.html), [states](https://mermaid.js.org/syntax/stateDiagram.html), [ER](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) [Camunda BPMN](https://docs.camunda.org/manual/latest/reference/bpmn20/) and [Structurizr DSL](https://docs.structurizr.com/dsl/language).
