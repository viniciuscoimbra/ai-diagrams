# Changelog

## Unreleased

### Horizontal C4

- C4 views no longer come out top to bottom by default. `build_c4.py` tries left to right and top to bottom and the cost prefers a landscape page (`orientation: auto`). A long chain still goes top to bottom when the horizontal drawing would pass the page width.
- New `orientation` on the model or on a view: `auto` (default), `horizontal` (left to right only, page up to 2560 px) or `vertical` (top to bottom only, the 0.2.0 behavior).
- `ai-diagrams import` maps `autoLayout lr`/`rl` to `horizontal` and `tb`/`bt` to `vertical`.

## 0.2.0

Interface in English. Commands, flags, folder and file names, error codes, messages, theme and spec keys, markers and docs move from Portuguese to English. Diagram text does not change: a diagram generated in pt-BR stays in pt-BR, and the fixed labels in `pt-BR`, `en` and `es` are the same as in 0.1.0.

### C4 from a model

- C4 is drawn from one JSON model (`scripts/build_c4.py`): people, systems, containers, components, deployment nodes and relationships, written once. Six views come from it: landscape, context (level 1), containers (level 2), components (level 3), dynamic (numbered steps) and deployment. A relationship written at a detailed level appears in the coarser views as an implied relationship.
- Layout and routing by elkjs, already in the package; the generator tries several variants and keeps the one with the fewest crossings, then bends, length and area.
- Each arrow carries its label, with what it does and `[technology]`, instead of a badge and an item under "Relationships". Persons have a head; containers have shapes (web, database, queue, mobile); components have the UML tabs; the legend lists only what the view draws.
- Each view links the others; a system or container with a deeper view opens it.
- `ai-diagrams import` reads Structurizr DSL (`.dsl`), with `DSL-UNSUPPORTED` and `DSL-UNKNOWN` for what it does not read.
- New gate rules for C4 pages drawn from the model: `C4-REL-MISSING`, `C4-REL-INCOMPLETE`, `C4-REL-DETACHED`; `OVERLAP` and `ARROW-OVER-TEXT` also cover the labels. The template `11-c4` is now a model (`11-c4-pix.json`). A C4 page written by hand, with badges and `.passos`, still passes the gate as before.

### Compatibility

- Old command and flag names keep working until 0.3.0. Each use prints a warning on stderr, for example `ai-diagrams: --tema is deprecated; use --theme`.
- Old environment variables (`AI_DIAGRAMS_TEMA`, `AI_DIAGRAMS_IDIOMA`) are still read until 0.3.0, with the same warning.
- Theme files: version 1 files (Portuguese keys) are still read. The engine writes only version 2.
- CSS tokens: the theme `:root` still declares the old token names as aliases of the new ones until 0.3.0 (`--tinta:var(--ink)`).
- Spec JSON files: old Portuguese keys and values are still read until 0.3.0. Generators and the importer write the English keys.
- Markers in source HTML: old markers are still read.
- Error codes changed **without alias**. A script that checks for an old code must look for the new one: a script that greps for `MERMAID-NAO-SUPORTADO` must look for `MERMAID-UNSUPPORTED`. The full table is below.
- File and folder names changed without a copy under the old name. If you reference a template, script or example path, update it with the tables below.

### Commands and flags

| 0.1.x | 0.2.0 |
|---|---|
| `ai-diagrams importar` | `ai-diagrams import` |
| `--projeto` (install) | `--project` |
| `[s/N]` (replacement prompt) | `[y/N]` |
| `--tema` | `--theme` |
| `--idioma` | `--lang` |
| `--saida` | `--out` |
| `--tipo` | `--type` |
| `--somente-fonte` | `--source-only` |
| `--so-lint` | `--lint-only` |
| `--sem-chrome` | `--no-chrome` |
| `--so-bpmn` | `--bpmn-only` |
| `--gerador` (`theme.py`) | `--generator` |
| `--largura` (`conceptual.py`) | `--width` |
| `--altura` (`conceptual.py`) | `--height` |
| `--escala` (`conceptual.py`) | `--scale` |
| `--exibicao` (`conceptual.py`) | `--display` |
| `--piso` (`conceptual.py`) | `--min-text` |
| `--piso-rot` (`conceptual.py`) | `--min-label` |
| `AI_DIAGRAMS_TEMA` | `AI_DIAGRAMS_THEME` |
| `AI_DIAGRAMS_IDIOMA` | `AI_DIAGRAMS_LANG` |

Values of `import --type`:

| 0.1.x | 0.2.0 |
|---|---|
| `der` | `er` |
| `matriz` | `matrix` |
| `raias` | `swimlanes` |
| `sequencia` | `sequence` |
| `estados` | `states` |
| `catalogo` | `catalog` |
| `comparacao` | `comparison` |
| `bpmn` | `bpmn` (unchanged) |

Other output changes:

- The import report is `<name>.import.json` (was `<name>.importacao.json`), with paths relative to the report folder.
- The default output folder of `ai-diagrams import` and of the skill in your project is `diagrams/` (was `diagramas/`), with sources in `diagrams/_src/`. A theme kept in the project goes in `diagrams/_src/theme.json`.
- Gate headers: `LINT REPROVOU` is now `LINT FAILED`, `BPMN REPROVOU` is `BPMN FAILED`, `ESTADOS REPROVOU` is `STATES FAILED`. `lint 0` and `total: N` stay.
- `ai-diagrams doctor` prints `FAIL` instead of `FALHA`.
- The importer prints `IMPORTED:` instead of `IMPORTADO:`.

### Markers in source HTML

Old markers are still read.

| 0.1.x | 0.2.0 |
|---|---|
| `<meta name="tema">` | `<meta name="theme">` |
| `<meta name="idioma">` | `<meta name="lang">` |
| `<meta name="largura">` | `<meta name="width">` |
| `/*ESTILO*/` | `/*STYLE*/` |
| local override `_style.css` / `style.css` | `_style.css` / `style.css` |
| local override `_style-conceptual.css` | `_style-conceptual.css` |

### Theme files (schema_version 2)

Theme files now use `schema_version` 2 with English keys. Version 1 files are still read; the engine writes only version 2. `python3 skills/ai-diagrams/scripts/theme.py --theme old.json --json` prints a version 1 file converted to version 2. The bundled theme `papel` is now `paper`; the old name still resolves until 0.3.0, with a warning.

| 0.1.x | 0.2.0 |
|---|---|
| `versao_schema`, `nome`, `empresa` | `schema_version`, `name`, `company` |
| `cores` | `colors` |
| `cores.tinta`, `apoio`, `cinza`, `zona`, `papel`, `acento`, `risco`, `risco_fundo` | `colors.ink`, `support`, `muted`, `zone`, `paper`, `accent`, `risk`, `risk_bg` |
| `cores_derivadas` | `derived` |
| `acento_forte`, `cinza_claro`, `c4_pessoa_tipo`, `c4_pessoa_desc`, `c4_externo`, `c4_limite` | `accent_strong`, `muted_light`, `c4_person_type`, `c4_person_desc`, `c4_external`, `c4_boundary` |
| `paleta_der` | `er_palette` |
| `der_borda`, `der_legenda`, `der_linha_par`, `der_chave`, `der_dominio`, `der_fora`, `der_copia` | `er_border`, `er_legend`, `er_row_even`, `er_key`, `er_domain`, `er_external`, `er_copy` |
| `der_forte`, `der_dependente`, `der_associativa`, `der_controle`, `der_fato`, `der_versionada` | `er_strong`, `er_dependent`, `er_associative`, `er_control`, `er_fact`, `er_versioned` |
| `der_projecao`, `der_trilha`, `der_dominio_fundo`, `der_configuracao`, `der_referencia`, `der_visao`, `der_calor` | `er_projection`, `er_trail`, `er_domain_bg`, `er_config`, `er_reference`, `er_view`, `er_heat` |
| `fontes` (`texto`, `mono`) | `fonts` (`text`, `mono`) |
| `moldura` (`cabecalho`, `rodape`, `rodape_direita`, `classificacao`, `mostrar_cliente`) | `frame` (`header`, `footer`, `footer_right`, `classification`, `show_client`) |

CSS tokens follow the key names, with `_` written as `-`: `--ink`, `--risk-bg`, `--er-row-even` and so on. The channel tokens are `--support-rgb`, `--paper-rgb`, `--risk-rgb` and `--er-heat-rgb`; the font tokens are `--font-text` and `--font-mono`. Until 0.3.0 the theme `:root` also declares the old names (`--tinta`, `--risco-fundo`, `--apoio-rgb`, `--fonte-texto` and the rest) as aliases of the new ones.

### Spec JSON keys

Spec files (swimlanes, sequence, state machine, BPMN, ER model and layout, comparison YAML) are written with English keys and values. The 0.1.x Portuguese names are still read until 0.3.0. Geometry keys (`x`, `y`, `w`, `id` and the like) did not change. The full map is in `skills/ai-diagrams/scripts/spec_keys.json`.

| Spec | Keys (0.1.x → 0.2.0) | Values (0.1.x → 0.2.0) |
|---|---|---|
| All types | `cabecalho` → `header`, `rodape` → `footer`, `titulo_pagina` → `page_title`, `faixa` → `band`, `idioma` → `lang`, `titulo` → `title`, `subtitulo` → `subtitle`, `nome` → `name`, `tipo` → `type`, `texto` → `text`, `estilo` → `style` |  |
| Swimlanes | `raias` → `lanes`, `raia` → `lane`, `fases` → `phases`, `fase` → `phase`, `elementos` → `elements`, `sequencia` → `sequence`, `secoes` → `sections`, `itens` → `items`, `opcoes` → `options`, `entrada` → `entry`, `saida` → `exit` | `type`: `coluna` → `column`, `lateral` → `side`, `destinos` → `targets`, `passos` → `steps`; `style`: `foco` → `focus`, `fora` → `out` |
| Sequence | `participantes` → `participants`, `mensagens` → `messages`, `de` → `from`, `para` → `to`, `passo` → `step`, `fragmento` → `fragment`, `guarda` → `guard`, `ramos` → `branches`, `ramo` → `branch`, `icone` → `icon`, `nota` → `note`, `sobre` → `over`, `abre` → `opens`, `nivel` → `level`, `linhas` → `lines` | `type`: `ator` → `actor`, `banco` → `database`, `servico` → `service`, `externo` → `external`, `fila` → `queue`, `sistema` → `system`, `resposta` → `reply`, `assincrona` → `async`, `sincrona` → `sync` |
| State machine | `estados` → `states`, `transicoes` → `transitions`, `inicial` → `initial`, `evento` → `event`, `acao` → `action`, `de` → `from`, `para` → `to`, `guarda` → `guard`, `direcao` → `direction`, `largura` → `width` | `style`: `foco` → `focus`, `fora` → `out` |
| BPMN | `cabecalho` → `header`, `rodape` → `footer` |  |
| ER model (`model.json`) | `schemaComum` → `commonSchema`, `schemaLeitura` → `readSchema`, `colunasControle` → `controlColumns`, `tabelas` → `tables`, `rotulo` → `label`, `colunas` → `columns` | `type`: `forte` → `strong`, `dependente` → `dependent`, `associativa` → `associative`, `controle` → `control`, `fato` → `fact`, `versionada` → `versioned`, `projecao` → `projection`, `trilha` → `trail`, `dominio` → `domain`, `configuracao` → `config`, `referencia` → `reference`, `visao` → `view` |
| ER layout (`*.layout.mjs`) | `modelo` → `model`, `tabelas` → `tables`, `arestas` → `edges`, `de` → `from`, `para` → `to`, `coluna` → `column`, `sai` → `exit`, `chega` → `enter`, `raia` → `lane`, `pontos` → `points`, `yRaia` → `laneY`, `semSeta` → `noArrow`, `externas` → `external`, `leitura` → `readView` | `dy`: `reto` → `straight` |
| Comparison YAML (importer input) | `opcoes` → `options`, `criterios` → `criteria`, `valores` → `values` |  |

### Error codes

Codes changed without alias.

| 0.1.x | 0.2.0 |
|---|---|
| `ATRAVESSA` | `CROSSES` |
| `COLINEAR`, `COLINEAR-V`, `COLINEAR-H` | `COLLINEAR`, `COLLINEAR-V`, `COLLINEAR-H` |
| `SEM-BADGES` | `NO-BADGES` |
| `SEM-PASSOS` | `NO-STEPS` |
| `PASSOS-DIVERGEM` | `STEPS-MISMATCH` |
| `BADGE-SOLTO` | `BADGE-DETACHED` |
| `SOBREPOE` | `OVERLAP` |
| `SOBREPOSICAO` | `OVERLAP` |
| `SETA-SOBRE-TEXTO` | `ARROW-OVER-TEXT` |
| `SETA-NA-BORDA` | `ARROW-ON-EDGE` |
| `SETA-SOLTA` | `ARROW-DETACHED` |
| `ROTULO-SOLTO` | `LABEL-DETACHED` |
| `ROTULO-SOBRE-CAIXA` | `LABEL-OVER-BOX` |
| `PONTA-DENTRO` | `ARROWHEAD-INSIDE` |
| `TRANSBORDA`, `TRANSBORDA-X`, `TRANSBORDA-Y`, `TRANSBORDA-PAGINA` | `OVERFLOW`, `OVERFLOW-X`, `OVERFLOW-Y`, `OVERFLOW-PAGE` |
| `TEXTO-MARKETING` | `MARKETING-COPY` |
| `C4-SEM-TIPO` | `C4-NO-TYPE` |
| `C4-SEM-LEGENDA` | `C4-NO-LEGEND` |
| `SEM-TIPO` | `NO-TYPE` |
| `SEM-LEGENDA` | `NO-LEGEND` |
| `COR-FORA-DO-TEMA` | `COLOR-OUTSIDE-THEME` |
| `FONTE-FORA-DO-TEMA` | `FONT-OUTSIDE-THEME` |
| `FIXADO` | `FIXED` |
| `SOLTA` | `DETACHED` |
| `AJUSTAVEL` | `ADJUSTABLE` |
| `FIXADO-INICIO` | `FIXED-START` |
| `SOLTA-INICIO` | `DETACHED-START` |
| `AJUSTAVEL-INICIO` | `ADJUSTABLE-START` |
| `FIXADO-BADGE` | `FIXED-BADGE` |
| `DENTRO-DA-CAIXA` | `INSIDE-BOX` |
| `TEXTO-SOBRE-BORDA` | `TEXT-OVER-EDGE` |
| `TEXTO-SOBRE-VIDA` | `TEXT-OVER-LIFELINE` |
| `TEXTO-MINIMO` | `TEXT-TOO-SMALL` |
| `SEM-CHROME` | `NO-CHROME` |
| `MEDICAO-FALHOU`, `MEDIÇÃO FALHOU` | `MEASURE-FAILED` |
| `CORTADO` | `CROPPED` |
| `SEM-ESTILO` | `NO-STYLE` |
| `TOKEN-DIVERGE` | `TOKEN-MISMATCH` |
| `TEMA-INEXISTENTE` | `THEME-NOT-FOUND` |
| `TEMA-INVALIDO` | `THEME-INVALID` |
| `TEMA-INCOMPLETO` | `THEME-INCOMPLETE` |
| `IDIOMA-INEXISTENTE` | `LANG-NOT-FOUND` |
| `IDIOMA-INCOMPLETO` | `LANG-INCOMPLETE` |
| `SEM-INICIAL` | `NO-INITIAL` |
| `DESCONHECIDO` | `UNKNOWN` |
| `SEM-EVENTO` | `NO-EVENT` |
| `SAI-DO-FINAL` | `LEAVES-FINAL` |
| `INALCANCAVEL` | `UNREACHABLE` |
| `SEM-SAIDA` | `NO-EXIT` |
| `LARGURA-INVALIDA` | `WIDTH-INVALID` |
| `FORA-DA-PAGINA` | `OFF-PAGE` |
| `FORA-DO-CANVAS` | `OFF-CANVAS` |
| `SEM-ALVOS` | `NO-TARGETS` |
| `ESTRUTURA` | `STRUCTURE` |
| `ALCANCE` | `REACHABILITY` |
| `IMPORTACAO` | `IMPORT-FAILED` |
| `MERMAID-NAO-SUPORTADO` | `MERMAID-UNSUPPORTED` |
| `BPMN-NAO-SUPORTADO` | `BPMN-UNSUPPORTED` |
| `CSV-NAO-SUPORTADO` | `CSV-UNSUPPORTED` |
| `SQL-NAO-SUPORTADO` | `SQL-UNSUPPORTED` |
| `YAML-NAO-SUPORTADO` | `YAML-UNSUPPORTED` |
| `FORMATO-NAO-SUPORTADO` | `FORMAT-UNSUPPORTED` |
| `TIPO-INCOMPATIVEL` | `TYPE-MISMATCH` |
| `ENTRADA-INVALIDA` | `INPUT-INVALID` |
| `SAIDA-CONFLITA` | `OUTPUT-CONFLICT` |
| `LINT REPROVOU` | `LINT FAILED` |
| `BPMN REPROVOU` | `BPMN FAILED` |
| `ESTADOS REPROVOU` | `STATES FAILED` |

New in 0.2.0: `NAME-TOO-LONG` (state machine), a state name that does not fit on one line.

### Files and folders

Repository folders:

| 0.1.x | 0.2.0 |
|---|---|
| `examples/` | `examples/` |
| `examples/*/output/` | `examples/*/output/` |
| `examples/import/` | `examples/import/` |
| `tests/` | `tests/` |
| `tests/negative/` | `tests/negative/` |
| `tools/` | `tools/` |
| `kb/INSTRUCTIONS.md` | `kb/INSTRUCTIONS.md` |
| `skills/ai-diagrams/templates/` | `skills/ai-diagrams/templates/` |
| `skills/ai-diagrams/themes/` | `skills/ai-diagrams/themes/` |
| `skills/ai-diagrams/themes/paper.json` | `skills/ai-diagrams/themes/paper.json` |
| `skills/ai-diagrams/er/` | `skills/ai-diagrams/er/` |
| `skills/ai-diagrams/states/` | `skills/ai-diagrams/states/` |

Skill scripts and engine:

| 0.1.x | 0.2.0 |
|---|---|
| `skills/ai-diagrams/assets/style-conceptual.css` | `skills/ai-diagrams/assets/style-conceptual.css` |
| `skills/ai-diagrams/assets/style.css` | `skills/ai-diagrams/assets/style.css` |
| `skills/ai-diagrams/bpmn/build_bpmn.py` | `skills/ai-diagrams/bpmn/build_bpmn.py` |
| `skills/ai-diagrams/er/er-build.mjs` | `skills/ai-diagrams/er/er-build.mjs` |
| `skills/ai-diagrams/er/er-tables.mjs` | `skills/ai-diagrams/er/er-tables.mjs` |
| `skills/ai-diagrams/er/er-overview.mjs` | `skills/ai-diagrams/er/er-overview.mjs` |
| `skills/ai-diagrams/er/lang.mjs` | `skills/ai-diagrams/er/lang.mjs` |
| `skills/ai-diagrams/er/lang.test.mjs` | `skills/ai-diagrams/er/lang.test.mjs` |
| `skills/ai-diagrams/states/elk-layout.cjs` | `skills/ai-diagrams/states/elk-layout.cjs` |
| `skills/ai-diagrams/i18n/test_lang.py` | `skills/ai-diagrams/i18n/test_lang.py` |
| `skills/ai-diagrams/references/er.md` | `skills/ai-diagrams/references/er.md` |
| `skills/ai-diagrams/references/states.md` | `skills/ai-diagrams/references/states.md` |
| `skills/ai-diagrams/references/import.md` | `skills/ai-diagrams/references/import.md` |
| `skills/ai-diagrams/references/visual-language.md` | `skills/ai-diagrams/references/visual-language.md` |
| `skills/ai-diagrams/references/swimlanes.md` | `skills/ai-diagrams/references/swimlanes.md` |
| `skills/ai-diagrams/references/sequence.md` | `skills/ai-diagrams/references/sequence.md` |
| `skills/ai-diagrams/references/table.md` | `skills/ai-diagrams/references/table.md` |
| `skills/ai-diagrams/scripts/conceptual.py` | `skills/ai-diagrams/scripts/conceptual.py` |
| `skills/ai-diagrams/scripts/check_theme.py` | `skills/ai-diagrams/scripts/check_theme.py` |
| `skills/ai-diagrams/scripts/theme_color.py` | `skills/ai-diagrams/scripts/theme_color.py` |
| `skills/ai-diagrams/scripts/build_states.py` | `skills/ai-diagrams/scripts/build_states.py` |
| `skills/ai-diagrams/scripts/build_swimlanes.py` | `skills/ai-diagrams/scripts/build_swimlanes.py` |
| `skills/ai-diagrams/scripts/build_sequence.py` | `skills/ai-diagrams/scripts/build_sequence.py` |
| `skills/ai-diagrams/scripts/lang.py` | `skills/ai-diagrams/scripts/lang.py` |
| `skills/ai-diagrams/scripts/import_cli.py` | `skills/ai-diagrams/scripts/import_cli.py` |
| `skills/ai-diagrams/scripts/import_data.py` | `skills/ai-diagrams/scripts/import_data.py` |
| `skills/ai-diagrams/scripts/import_mermaid.py` | `skills/ai-diagrams/scripts/import_mermaid.py` |
| `skills/ai-diagrams/scripts/theme.py` | `skills/ai-diagrams/scripts/theme.py` |
| `skills/ai-diagrams/scripts/technical_text.py` | `skills/ai-diagrams/scripts/technical_text.py` |

Templates:

| 0.1.x | 0.2.0 |
|---|---|
| `skills/ai-diagrams/templates/01-aws-architecture/01-payments-api.png` | `skills/ai-diagrams/templates/01-aws-architecture/01-payments-api.png` |
| `skills/ai-diagrams/templates/01-aws-architecture/_src/01-payments-api.html` | `skills/ai-diagrams/templates/01-aws-architecture/_src/01-payments-api.html` |
| `skills/ai-diagrams/templates/02-step-flow/02-event-outbox.png` | `skills/ai-diagrams/templates/02-step-flow/02-event-outbox.png` |
| `skills/ai-diagrams/templates/02-step-flow/_src/02-event-outbox.html` | `skills/ai-diagrams/templates/02-step-flow/_src/02-event-outbox.html` |
| `skills/ai-diagrams/templates/03-er-schema/_src/er-account.html` | `skills/ai-diagrams/templates/03-er-schema/_src/er-account.html` |
| `skills/ai-diagrams/templates/03-er-schema/_src/er-account.layout.mjs` | `skills/ai-diagrams/templates/03-er-schema/_src/er-account.layout.mjs` |
| `skills/ai-diagrams/templates/03-er-schema/_src/model.json` | `skills/ai-diagrams/templates/03-er-schema/_src/model.json` |
| `skills/ai-diagrams/templates/03-er-schema/er-account.png` | `skills/ai-diagrams/templates/03-er-schema/er-account.png` |
| `skills/ai-diagrams/templates/04-dependency-matrix/_src/er-overview.html` | `skills/ai-diagrams/templates/04-dependency-matrix/_src/er-overview.html` |
| `skills/ai-diagrams/templates/04-dependency-matrix/er-overview.png` | `skills/ai-diagrams/templates/04-dependency-matrix/er-overview.png` |
| `skills/ai-diagrams/templates/05-comparison-table/05-messaging-comparison.png` | `skills/ai-diagrams/templates/05-comparison-table/05-messaging-comparison.png` |
| `skills/ai-diagrams/templates/05-comparison-table/_src/05-messaging-comparison.html` | `skills/ai-diagrams/templates/05-comparison-table/_src/05-messaging-comparison.html` |
| `skills/ai-diagrams/templates/06-swimlanes/06-account-opening.png` | `skills/ai-diagrams/templates/06-swimlanes/06-account-opening.png` |
| `skills/ai-diagrams/templates/06-swimlanes/_src/06-account-opening.html` | `skills/ai-diagrams/templates/06-swimlanes/_src/06-account-opening.html` |
| `skills/ai-diagrams/templates/06-swimlanes/_src/06-account-opening.json` | `skills/ai-diagrams/templates/06-swimlanes/_src/06-account-opening.json` |
| `skills/ai-diagrams/templates/07-card-catalog/07-api-catalog.png` | `skills/ai-diagrams/templates/07-card-catalog/07-api-catalog.png` |
| `skills/ai-diagrams/templates/07-card-catalog/_src/07-api-catalog.html` | `skills/ai-diagrams/templates/07-card-catalog/_src/07-api-catalog.html` |
| `skills/ai-diagrams/templates/08-bpmn/08-payment-dispute.bpmn` | `skills/ai-diagrams/templates/08-bpmn/08-payment-dispute.bpmn` |
| `skills/ai-diagrams/templates/08-bpmn/08-payment-dispute.png` | `skills/ai-diagrams/templates/08-bpmn/08-payment-dispute.png` |
| `skills/ai-diagrams/templates/08-bpmn/_src/08-payment-dispute.json` | `skills/ai-diagrams/templates/08-bpmn/_src/08-payment-dispute.json` |
| `skills/ai-diagrams/templates/09-sequence/09-pix-outbound.png` | `skills/ai-diagrams/templates/09-sequence/09-pix-outbound.png` |
| `skills/ai-diagrams/templates/09-sequence/_src/09-pix-outbound.html` | `skills/ai-diagrams/templates/09-sequence/_src/09-pix-outbound.html` |
| `skills/ai-diagrams/templates/09-sequence/_src/09-pix-outbound.json` | `skills/ai-diagrams/templates/09-sequence/_src/09-pix-outbound.json` |
| `skills/ai-diagrams/templates/10-state-machine/10-pix-states.png` | `skills/ai-diagrams/templates/10-state-machine/10-pix-states.png` |
| `skills/ai-diagrams/templates/10-state-machine/_src/10-pix-states.html` | `skills/ai-diagrams/templates/10-state-machine/_src/10-pix-states.html` |
| `skills/ai-diagrams/templates/10-state-machine/_src/10-pix-states.json` | `skills/ai-diagrams/templates/10-state-machine/_src/10-pix-states.json` |
| `skills/ai-diagrams/templates/11-c4/11-c4-pix.png` | `skills/ai-diagrams/templates/11-c4/11-c4-pix.png` |
| `skills/ai-diagrams/templates/11-c4/_src/11-c4-pix.html` | `skills/ai-diagrams/templates/11-c4/_src/11-c4-pix.html` |
| `skills/ai-diagrams/templates/build-all.sh` | `skills/ai-diagrams/templates/build-all.sh` |

Examples:

| 0.1.x | 0.2.0 |
|---|---|
| `examples/README.md` | `examples/README.md` |
| `examples/aws-architecture/antifraud-decision.md` | `examples/aws-architecture/antifraud-decision.md` |
| `examples/aws-architecture/prompt.md` | `examples/aws-architecture/prompt.md` |
| `examples/aws-architecture/output/_src/transfer-antifraud.html` | `examples/aws-architecture/output/_src/transfer-antifraud.html` |
| `examples/aws-architecture/output/transfer-antifraud.png` | `examples/aws-architecture/output/transfer-antifraud.png` |
| `examples/bpmn/process.md` | `examples/bpmn/process.md` |
| `examples/bpmn/prompt.md` | `examples/bpmn/prompt.md` |
| `examples/bpmn/output/_src/access-recovery.json` | `examples/bpmn/output/_src/access-recovery.json` |
| `examples/bpmn/output/access-recovery.bpmn` | `examples/bpmn/output/access-recovery.bpmn` |
| `examples/bpmn/output/access-recovery.png` | `examples/bpmn/output/access-recovery.png` |
| `examples/c4/billing.md` | `examples/c4/billing.md` |
| `examples/c4/prompt.md` | `examples/c4/prompt.md` |
| `examples/c4/output/_src/billing-c4.html` | `examples/c4/output/_src/billing-c4.html` |
| `examples/c4/output/billing-c4.png` | `examples/c4/output/billing-c4.png` |
| `examples/card-catalog/events.csv` | `examples/card-catalog/events.csv` |
| `examples/card-catalog/prompt.md` | `examples/card-catalog/prompt.md` |
| `examples/card-catalog/output/_src/event-catalog.html` | `examples/card-catalog/output/_src/event-catalog.html` |
| `examples/card-catalog/output/event-catalog.png` | `examples/card-catalog/output/event-catalog.png` |
| `examples/er-schema/ddl.sql` | `examples/er-schema/ddl.sql` |
| `examples/er-schema/prompt.md` | `examples/er-schema/prompt.md` |
| `examples/er-schema/output/_src/er-billing.html` | `examples/er-schema/output/_src/er-billing.html` |
| `examples/er-schema/output/_src/er-billing.layout.mjs` | `examples/er-schema/output/_src/er-billing.layout.mjs` |
| `examples/er-schema/output/_src/model.json` | `examples/er-schema/output/_src/model.json` |
| `examples/er-schema/output/er-billing.png` | `examples/er-schema/output/er-billing.png` |
| `examples/step-flow/reconciliation.md` | `examples/step-flow/reconciliation.md` |
| `examples/step-flow/prompt.md` | `examples/step-flow/prompt.md` |
| `examples/step-flow/output/_src/payment-reconciliation.html` | `examples/step-flow/output/_src/payment-reconciliation.html` |
| `examples/step-flow/output/payment-reconciliation.png` | `examples/step-flow/output/payment-reconciliation.png` |
| `examples/build-all.sh` | `examples/build-all.sh` |
| `examples/import/build-all.sh` | `examples/import/build-all.sh` |
| `examples/state-machine/card-lifecycle.md` | `examples/state-machine/card-lifecycle.md` |
| `examples/state-machine/prompt.md` | `examples/state-machine/prompt.md` |
| `examples/state-machine/output/_src/card-lifecycle.html` | `examples/state-machine/output/_src/card-lifecycle.html` |
| `examples/state-machine/output/_src/card-lifecycle.json` | `examples/state-machine/output/_src/card-lifecycle.json` |
| `examples/state-machine/output/card-lifecycle.png` | `examples/state-machine/output/card-lifecycle.png` |
| `examples/dependency-matrix/ddl.sql` | `examples/dependency-matrix/ddl.sql` |
| `examples/dependency-matrix/prompt.md` | `examples/dependency-matrix/prompt.md` |
| `examples/dependency-matrix/output/_src/er-overview.html` | `examples/dependency-matrix/output/_src/er-overview.html` |
| `examples/dependency-matrix/output/_src/model.json` | `examples/dependency-matrix/output/_src/model.json` |
| `examples/dependency-matrix/output/er-overview.png` | `examples/dependency-matrix/output/er-overview.png` |
| `examples/swimlanes/process.md` | `examples/swimlanes/process.md` |
| `examples/swimlanes/prompt.md` | `examples/swimlanes/prompt.md` |
| `examples/swimlanes/output/_src/limit-increase.html` | `examples/swimlanes/output/_src/limit-increase.html` |
| `examples/swimlanes/output/_src/limit-increase.json` | `examples/swimlanes/output/_src/limit-increase.json` |
| `examples/swimlanes/output/limit-increase.png` | `examples/swimlanes/output/limit-increase.png` |
| `examples/sequence/authorization.md` | `examples/sequence/authorization.md` |
| `examples/sequence/prompt.md` | `examples/sequence/prompt.md` |
| `examples/sequence/output/_src/purchase-authorization.html` | `examples/sequence/output/_src/purchase-authorization.html` |
| `examples/sequence/output/_src/purchase-authorization.json` | `examples/sequence/output/_src/purchase-authorization.json` |
| `examples/sequence/output/purchase-authorization.png` | `examples/sequence/output/purchase-authorization.png` |
| `examples/comparison-table/criteria.yaml` | `examples/comparison-table/criteria.yaml` |
| `examples/comparison-table/prompt.md` | `examples/comparison-table/prompt.md` |
| `examples/comparison-table/output/_src/statement-comparison.html` | `examples/comparison-table/output/_src/statement-comparison.html` |
| `examples/comparison-table/output/statement-comparison.png` | `examples/comparison-table/output/statement-comparison.png` |

Tests and tools:

| 0.1.x | 0.2.0 |
|---|---|
| `tools/check-secrets.sh` | `tools/check-secrets.sh` |
| `tools/package.sh` | `tools/package.sh` |
| `tools/install-kiro.sh` | `tools/install-kiro.sh` |
| `tests/negative/c4-no-legend.html` | `tests/negative/c4-no-legend.html` |
| `tests/negative/c4-no-type.html` | `tests/negative/c4-no-type.html` |
| `tests/negative/c4-arrows.html` | `tests/negative/c4-arrows.html` |
| `tests/negative/collinear-conceptual.html` | `tests/negative/collinear-conceptual.html` |
| `tests/negative/inside-and-edge.html` | `tests/negative/inside-and-edge.html` |
| `tests/negative/states-unknown.json` | `tests/negative/states-unknown.json` |
| `tests/negative/states-unreachable.json` | `tests/negative/states-unreachable.json` |
| `tests/negative/states-leaves-final.json` | `tests/negative/states-leaves-final.json` |
| `tests/negative/states-no-event.json` | `tests/negative/states-no-event.json` |
| `tests/negative/states-no-initial.json` | `tests/negative/states-no-initial.json` |
| `tests/negative/states-no-exit.json` | `tests/negative/states-no-exit.json` |
| `tests/negative/marketing.html` | `tests/negative/marketing.html` |
| `tests/negative/text-over-lifeline-conceptual.html` | `tests/negative/text-over-lifeline-conceptual.html` |
| `tests/negative/overflow.html` | `tests/negative/overflow.html` |
| `tests/npm-cli.test.mjs` | `tests/npm-cli.test.mjs` |
| `tests/npm-smoke.sh` | `tests/npm-smoke.sh` |
| `tests/npm-tty.py` | `tests/npm-tty.py` |
| `tests/run.sh` | `tests/run.sh` |
| `tests/test_import.py` | `tests/test_import.py` |
| `tests/test_import_bpmn.py` | `tests/test_import_bpmn.py` |

Importer fixtures: `examples/import/<lang>/swimlanes.mmd` is now `examples/import/<lang>/swimlanes.mmd`, and each `output/` folder under `examples/import/<lang>/` is now `output/`.

## 0.1.0 (2026-11-07)

First npm release.

- `ai-diagrams install --claude|--codex|--kiro`, `ai-diagrams doctor` and `ai-diagrams importar`.
- Eleven diagram types with their gates: AWS architecture poster, numbered-step flow, C4, comparison table, sequence, swimlanes, cards catalog, BPMN 2.0, state machine, ER diagram per schema and schema dependency matrix.
- Themes in a JSON file (`ai-diagrams` and `papel`), selected with `--tema`, `<meta name="tema">` or `AI_DIAGRAMS_TEMA`.
- Fixed labels in `pt-BR`, `en` and `es`.
- Importer for Mermaid, BPMN 2.0 XML, SQL DDL, CSV catalogs and YAML comparisons.
