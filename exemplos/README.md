# Exemplos por tipo

Cada pasta tem três coisas:

1. `prompt.md`: o prompt exato que foi colado no Claude Code;
2. o arquivo de dados que acompanha o prompt;
3. `resultado/`: o que a skill produziu ao executar esse prompt, com o fonte em `resultado/_src/` e o PNG em `resultado/` (no BPMN, também o `.bpmn`).

`bash exemplos/gerar.sh` regenera os onze resultados a partir dos fontes, pelo gate de cada tipo.

Os resultados foram gerados em 2026-11-04 (o de sequência em 2026-11-05 e o de máquina de estados em 2026-11-06) por sessões do Claude Code com a skill deste repositório, uma por tipo, a partir da raiz do repositório. Cada sessão rodou o gate do tipo até zero e leu o PNG antes de entregar. Os prompts apontam caminhos de `exemplos/`; no seu projeto, troque pelo caminho do seu arquivo de dados e omita a pasta de saída (o padrão da skill é `diagramas/`).

| Pasta | Tipo | Dados | Gate |
|---|---|---|---|
| `arquitetura-aws/` | poster de arquitetura AWS | `decisao-antifraude.md` | `poster_lint.py` via `build.py` |
| `fluxo-passos/` | fluxo com passos numerados | `conciliacao.md` | `poster_lint.py` via `build.py` |
| `der-schema/` | DER por schema | `ddl.sql` | `poster_lint.py` via `build.py` |
| `matriz-dependencia/` | matriz de dependência | `ddl.sql` | `poster_lint.py` via `build.py` |
| `tabela-comparacao/` | tabela de comparação | `criterios.yaml` | `poster_lint.py` via `build.py` |
| `raias/` | fluxo em raias | `processo.md` | `conceitual.py` |
| `catalogo-cards/` | conceitual em cards | `eventos.csv` | `conceitual.py` |
| `bpmn/` | BPMN 2.0 | `processo.md` | `gerar_bpmn.py` |
| `sequencia/` | diagrama de sequência | `autorizacao.md` | `conceitual.py` |
| `maquina-estados/` | máquina de estados | `ciclo-cartao.md` | `gerar_estados.py` e `conceitual.py` |
| `c4/` | C4 de contêineres | `cobranca.md` | `poster_lint.py` via `build.py` (resultado com Opus 5.5, ver abaixo) |

Nas ferramentas sem execução (Claude.ai sem a skill instalada, ChatGPT, Bedrock), o mesmo prompt devolve só o fonte; o PNG sai com o comando do tipo na sua máquina. Veja o guia em `docs/install.md`.

O resultado do C4 (`c4/`) foi gerado em 2026-11-06 com Claude Opus 5.5, não com o Sonnet 4.5 dos outros tipos: a rodada do Sonnet 4.5 passou no gate e reprovou na leitura do PNG.
