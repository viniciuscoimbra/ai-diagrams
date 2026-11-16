# ER diagram per schema and dependency matrix

Both generators read the same logical model. The content of the boxes comes from the model; the position of each table and the path of each arrow are decided by hand in the layout.

## Logical model (`model.json`)

```json
{
  "header": "Company · Project · Client",
  "footer": "Company · logical model · YYYY-MM",
  "commonSchema": "comum",
  "readSchema": null,
  "controlColumns": [],
  "schemas": { "comum": "domínios gerais", "conta": "Contas e movimentos" },
  "tables": {
    "conta.contas": {
      "type": "strong",
      "label": "a conta de pagamento do cliente",
      "columns": [
        ["conta_id", "uuid", "PK"],
        ["cliente_id", "uuid", "FK", "cadastro.clientes", true],
        ["numero", "varchar(20)", "UQ"],
        ["aberta_em", "timestamptz", ""]
      ]
    }
  }
}
```

The sample content is in pt-BR, like the template; write it in the language the user asks for.

| Field | What it is |
|---|---|
| `header`, `footer` | header and footer text of every ER diagram and of the matrix |
| `commonSchema` | schema of general domains and references; at the boundary it appears as "uses from" |
| `readSchema` | schema of read views, if there is one; null when it does not exist |
| `controlColumns` | extra columns hidden from the boxes; `criado_em`, `atualizado_em`, `versao_registro` and `deletado_em` are already hidden |
| `schemas` | name of each schema; the order of the keys is the order of the matrix |
| `tables` | key `schema.table`; the physical name is the part after the dot |

Each column is `[name, type, key, target, required]`. `key` is `PK`, `FK`, `UQ` or empty. For `FK`, `target` is the referenced table and `required` is `true` when the column is not null: this decides the arrowhead (one, or zero or one).

Table types and the candy color of each:

| `type` | Label | When to use |
|---|---|---|
| `strong` | strong entity | exists on its own; the others point to it |
| `dependent` | dependent | only exists linked to a strong entity |
| `associative` | associative | links two entities, many to many |
| `control` | process control | run, batch, schedule |
| `fact` | fact · immutable | something that happened; recorded once |
| `versioned` | versions · immutable | each change is a new row |
| `projection` | projection | state computed from the facts |
| `trail` | technical | outbox or consumer deduplication |
| `domain` | domain | closed list of values |
| `config` | configuration | rule the database checks, such as allowed transitions |
| `reference` | reference | official list loaded from an external source |
| `view` | read view | view built from other schemas |

The labels above are the `en` ones; the diagram shows them in the selected language (`--lang`).

`domain`, `reference` and `config` are light tables: they do not go into the main drawing, they go to the bottom band with the list of who uses each one. The column that points to them appears in the domain color, without an arrow.

## Layout (`er-<schema>.layout.mjs`)

```js
export default {
  model: './model.json',
  schema: 'conta',
  title: 'schema conta · Contas e movimentos',
  sub: 'two or three factual sentences',
  canvas: { w: 1700 },
  tables: {
    'conta.contas': { x: 685, y: 260, desc: 'a conta de pagamento do cliente' }
  },
  edges: [
    { from: 'conta.movimentos', column: 'conta_id', exit: 'L', to: 'conta.contas', enter: 'R', lane: 1200, dy: 40,
      text: 'Uma <b>conta</b> recebe zero ou muitos <b>movimentos</b>.' }
  ]
};
```

- `tables`: every non-light table of the schema must be here; the generator rejects what is missing. Optional `w` changes the width (default 330).
- Each edge leaves from the row of the FK column, on the `exit` side (`L` or `R`) of the source table.
- `enter` `L` or `R`: the arrow runs vertically along the `lane` (x) and enters the side of the target table at height `dy` (relative to its top; `'straight'` keeps the exit height). Without `lane`, the arrow is straight.
- `enter` `T` or `B`: enters from the top or the bottom at `dx` (relative to the table's left), with optional `lane` and `laneY`.
- `points`: explicit path when the default routing does not work; `'x0'` and `'y0'` are the exit point.
- The badge goes in the middle of the longest segment; `seg` and `frac` pick another, and `badge: [x, y]` fixes the center.
- `noArrow`: `{ 'schema.table.column': 'reason' }` draws the FK without an arrow, with the reason in the label.
- `external` and `readView: true` serve the read-view ER diagram: tables from another schema drawn dashed as targets, dashed arrows without cardinality.

Different lanes for different arrows: two arrows on the same lane are collinear and the lint fails.

## Commands

```bash
node <skill>/er/er-build.mjs diagrams/_src/er-account.layout.mjs
python3 <skill>/scripts/build.py diagrams/_src/er-account.html

node <skill>/er/er-overview.mjs diagrams/_src/model.json
python3 <skill>/scripts/build.py diagrams/_src/er-overview.html
```

The build height adjusts until the footer appears whole in the PNG.
