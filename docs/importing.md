# Import existing diagrams and data

The importer converts an existing file into the native source format, then calls the same generator and gate as a diagram written from scratch. It does not use Mermaid to render a separate style. Original coordinates in BPMN XML are replaced by the engine layout.

```bash
python3 skills/ai-diagrams/scripts/import_cli.py examples/import/en/sequence.mmd --out diagrams --lang en
```

With the npm CLI installed:

```bash
ai-diagrams import process.bpmn --out diagrams --lang en
ai-diagrams import schema.sql --type er --out diagrams --lang en
ai-diagrams import schema.sql --type matrix --out diagrams --lang en
```

Without npm, invoke the Python entry point from a clone. `ai-diagrams import --help` lists every option.

## Inputs and native outputs

| Input | Native output | Generator and gate |
| --- | --- | --- |
| Mermaid `flowchart` or `graph` without `subgraph` | BPMN JSON | `bpmn/build_bpmn.py` |
| Mermaid `flowchart` or `graph` with lane `subgraph` blocks | Swimlane JSON | `build_swimlanes.py`, then `conceptual.py` |
| Mermaid `sequenceDiagram` | Sequence JSON | `build_sequence.py`, then `conceptual.py` |
| Mermaid `stateDiagram-v2` | State machine JSON | `build_states.py`, then `conceptual.py` |
| Mermaid `erDiagram` | Logical model JSON and ER layout | `er-build.mjs`, then `build.py` |
| BPMN 2.0 `.bpmn` XML | BPMN JSON | `bpmn/build_bpmn.py` |
| SQL DDL | Logical model JSON and ER layout, or matrix | `er-build.mjs` or `er-overview.mjs`, then `build.py` |
| CSV catalog | Native catalog HTML | `conceptual.py` |
| YAML comparison | Native comparison HTML | `build.py` |
| Structurizr DSL `workspace.dsl` | C4 model JSON, one page per view | `build_c4.py`, then `build.py` per view |

`--type` selects `er`, `matrix`, `catalog`, `comparison`, `bpmn`, `swimlanes`, `sequence`, `states` or `c4`; it must match the input, or the import fails with `TYPE-MISMATCH`. For SQL, the default is `er`. `--out` selects the output directory. `--lang` selects fixed labels in `pt-BR`, `en` or `es`, with `AI_DIAGRAMS_LANG` and then `pt-BR` as fallbacks. It does not translate names or descriptions in the input. Sources for all three languages are in [examples/import](../examples/import/).

The exact accepted syntax and rejected cases are documented in the packaged [import reference](../skills/ai-diagrams/references/import.md). These are explicit subsets of each format. Unsupported Mermaid syntax returns `MERMAID-UNSUPPORTED` with its source line; unsupported BPMN elements return `BPMN-UNSUPPORTED`, and the same applies to `SQL-UNSUPPORTED`, `CSV-UNSUPPORTED`, `YAML-UNSUPPORTED` and `DSL-UNSUPPORTED`. A file extension the importer does not know fails with `FORMAT-UNSUPPORTED`, and a file that is not UTF-8 with `INPUT-INVALID`. Adapt the input instead of deleting rejected content without reviewing its meaning.

ER and matrix sources go to `<output>/_src/<input-name>/`; their final HTML and PNG go to `<output>/<input-name>/`. Each input has a separate `<input-name>.import.json` report, with paths relative to the report folder, reset to pending before a retry. A BPMN output that would overwrite its original input fails with `OUTPUT-CONFLICT`. Use a different `--out` directory. The common `--theme` option is also supported.

## Generate sources without Chrome

```bash
python3 skills/ai-diagrams/scripts/import_cli.py examples/import/en/sequence.mmd --out /tmp/import-preview --lang en --source-only
```

`--source-only` runs conversion and native source generation, with the structural checks available in those generators. It does not run the Chrome geometry gate or produce an approved PNG. The command explicitly reports the remaining gate. Run again without the flag on a machine with the requirements in [install.md](install.md), then inspect the PNG.

The existing examples from before the importer are preserved. New importer fixtures, translated input text and generated sources live under `examples/import/`.

## Verify the importer

```bash
python3 -m unittest discover -s tests -p 'test_import*.py'
bash examples/import/build-all.sh --source-only
```

The sample script runs the tests before generating all 30 imports: nine inputs in each language, plus SQL as a dependency matrix. Its manifest distinguishes passing conversion tests from the pending browser gate. To run the full gates and generate PNGs, run `bash examples/import/build-all.sh` without the source-only flag on a machine where Chrome can start. The test suite is also included in `bash tests/run.sh`.
