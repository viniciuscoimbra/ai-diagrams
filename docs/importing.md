# Import existing diagrams and data

The importer converts an existing file into the native source format, then calls the same generator and gate as a diagram written from scratch. It does not use Mermaid to render a separate style. Original coordinates in BPMN XML are replaced by the engine layout.

```bash
python3 skills/ai-diagrams/scripts/importar.py exemplos/importar/en/sequence.mmd --saida diagramas --idioma en
```

With the npm CLI installed:

```bash
ai-diagrams importar process.bpmn --saida diagramas --idioma en
ai-diagrams importar schema.sql --tipo der --saida diagramas --idioma en
ai-diagrams importar schema.sql --tipo matriz --saida diagramas --idioma en
```

The npm package is not published yet. Use the local tarball described in [install.md](install.md), or invoke the Python entry point from a clone.

## Inputs and native outputs

| Input | Native output | Generator and gate |
| --- | --- | --- |
| Mermaid `flowchart` or `graph` without `subgraph` | BPMN JSON | `bpmn/gerar_bpmn.py` |
| Mermaid `flowchart` or `graph` with lane `subgraph` blocks | Swimlane JSON | `gerar_raias.py`, then `conceitual.py` |
| Mermaid `sequenceDiagram` | Sequence JSON | `gerar_sequencia.py`, then `conceitual.py` |
| Mermaid `stateDiagram-v2` | State machine JSON | `gerar_estados.py`, then `conceitual.py` |
| Mermaid `erDiagram` | Logical model JSON and DER layout | `der-montar.mjs`, then `build.py` |
| BPMN 2.0 `.bpmn` XML | BPMN JSON | `bpmn/gerar_bpmn.py` |
| SQL DDL | Logical model JSON and DER layout, or matrix | `der-montar.mjs` or `der-visao-geral.mjs`, then `build.py` |
| CSV catalog | Native catalog HTML | `conceitual.py` |
| YAML comparison | Native comparison HTML | `build.py` |

`--tipo` selects `der`, `matriz`, `catalogo`, `comparacao`, `bpmn`, `raias`, `sequencia` or `estados`; it must match the input. For SQL, the default is `der`. `--saida` selects the output directory. `--idioma` selects fixed labels in `pt-BR`, `en` or `es`, with `AI_DIAGRAMS_IDIOMA` and then `pt-BR` as fallbacks. It does not translate names or descriptions in the input. Sources for all three languages are in [exemplos/importar](../exemplos/importar/).

The exact accepted syntax and rejected cases are documented in the packaged [import reference](../skills/ai-diagrams/references/importar.md). These are explicit subsets of each format. Unsupported Mermaid syntax returns `MERMAID-NAO-SUPORTADO` with its source line; unsupported BPMN elements return `BPMN-NAO-SUPORTADO`. Adapt the input instead of deleting rejected content without reviewing its meaning.

DER and matrix sources go to `<output>/_src/<input-name>/`; their final HTML and PNG go to `<output>/<input-name>/`. Each input has a separate `<input-name>.importacao.json` report, reset to pending before a retry. A BPMN output that would overwrite its original input fails with `SAIDA-CONFLITA`. Use a different `--saida` directory. The common `--tema` option is also supported.

## Generate sources without Chrome

```bash
python3 skills/ai-diagrams/scripts/importar.py exemplos/importar/en/sequence.mmd --saida /tmp/import-preview --idioma en --somente-fonte
```

`--somente-fonte` runs conversion and native source generation, with the structural checks available in those generators. It does not run the Chrome geometry gate or produce an approved PNG. The command explicitly reports the remaining gate. Run again without the flag on a machine with the requirements in [install.md](install.md), then inspect the PNG.

The existing examples from before the importer are preserved. New importer fixtures, translated input text and generated sources live under `exemplos/importar/`.

## Verify the importer

```bash
python3 -m unittest discover -s testes -p 'test_importar*.py'
bash exemplos/importar/gerar.sh --somente-fonte
```

The sample script runs the tests before generating all 30 imports: nine inputs in each language, plus SQL as a dependency matrix. Its manifest distinguishes passing conversion tests from the pending browser gate. To run the full gates and generate PNGs, run `bash exemplos/importar/gerar.sh` without the source-only flag on a machine where Chrome can start. The test suite is also included in `bash testes/rodar.sh`.
