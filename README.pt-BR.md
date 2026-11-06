# Prosa

**Descreva em palavras. Receba um diagrama que passa na revisão.**

[English](README.md) · [Español](README.es.md)

Prosa é uma skill para CLIs de IA (Claude Code, Codex CLI, Kiro CLI). Você descreve o diagrama em linguagem natural, ou aponta um documento, um DDL ou a descrição de um processo, e a IA escreve o fonte do diagrama, roda um gate geométrico e gera o PNG. O gate reprova:
- texto sobreposto;
- seta solta ou atravessando caixa;
- badge fora da seta;
- conteúdo cortado na borda da página;
- texto abaixo do tamanho mínimo.

A IA corrige o fonte até o gate passar e só então entrega.

O fonte fica no seu repositório, em texto, e qualquer pessoa edita e gera o PNG de novo depois.

## Tipos de diagrama

| Tipo | Exemplo de pedido | Exemplo |
|---|---|---|
| Poster de arquitetura AWS | "Poster de arquitetura da API de pagamentos: API Gateway, Lambda, Aurora e EventBridge." | [prompt e resultado](exemplos/arquitetura-aws/) |
| Fluxo com passos numerados | "Fluxo com passos do outbox até o consumidor, com Debezium e MSK." | [prompt e resultado](exemplos/fluxo-passos/) |
| Diagrama de sequência | "Diagrama de sequência da autorização de compra no cartão: terminal, bandeira, autorizador, antifraude e ledger." | [prompt e resultado](exemplos/sequencia/) |
| Fluxo em raias | "Fluxo em raias da abertura de conta entre cliente, onboarding, risco e operações." | [prompt e resultado](exemplos/raias/) |
| BPMN 2.0 (editável no Camunda ou no bpmn.io) | "BPMN do processo de contestação de pagamento." | [prompt e resultado](exemplos/bpmn/) |
| Tabela de comparação | "Tabela comparando SQS, Kinesis e MSK para eventos entre domínios." | [prompt e resultado](exemplos/tabela-comparacao/) |
| Catálogo em cards | "Catálogo em cards das APIs da plataforma, com dono e contrato." | [prompt e resultado](exemplos/catalogo-cards/) |
| DER por schema | "DER do schema de cobrança a partir deste DDL." | [prompt e resultado](exemplos/der-schema/) |
| Matriz de dependência entre schemas | "Matriz de dependência entre os schemas deste DDL." | [prompt e resultado](exemplos/matriz-dependencia/) |

![Poster de arquitetura AWS](exemplos/arquitetura-aws/resultado/antifraude-transferencias.png)

## Pré-requisitos

| Item | Para quê | Verificar |
|---|---|---|
| Python 3.9 ou mais novo | gate e PNG | `python3 --version` |
| Pacote `diagrams` | ícones oficiais da AWS | `python3 -c "import diagrams"` |
| Node 18 ou mais novo | DER e matriz | `node --version` |
| Google Chrome | gera o PNG (headless) | `ls "/Applications/Google Chrome.app"` |
| uma CLI de IA | Claude Code, Codex CLI ou Kiro CLI | `claude --version`, `codex --version` ou `kiro-cli --version` |

Instale os ícones com `pip3 install diagrams`. Se o Chrome estiver em outro lugar, aponte o caminho em `POSTER_CHROME`.

## Instalação

```bash
git clone https://github.com/viniciuscoimbra/prosa.git
```

```bash
export PROSA="$PWD/prosa"
```

**Claude Code**

```bash
mkdir -p ~/.claude/skills && ln -s "$PROSA"/skills/prosa ~/.claude/skills/prosa
```

**Codex CLI**

```bash
mkdir -p ~/.codex/skills && ln -s "$PROSA"/skills/prosa ~/.codex/skills/prosa
```

Rode o Codex com `codex --sandbox danger-full-access`. O sandbox padrão bloqueia o Chrome headless, e sem ele o gate não roda.

**Kiro CLI**

```bash
bash "$PROSA"/ferramentas/instalar-kiro.sh /caminho/do/seu/projeto
```

Depois, dentro do projeto, rode `kiro-cli chat --agent prosa`.

O passo a passo completo está em [docs/install.md](docs/install.md), em inglês. Ele inclui o uso sem CLI (Projetos do Claude.ai, ChatGPT).

## Como pedir

Comece o pedido com "Use a skill prosa", para a IA não responder em texto:

```text
Use a skill prosa. Leia docs/decisao-antifraude.md e faça o poster de arquitetura AWS
do antifraude em tempo real, com passos numerados.
```

A IA escolhe o tipo e pergunta antes de desenhar quando o pedido é ambíguo. Depois grava o fonte em `diagramas/_src/`, roda o gate até passar e salva o PNG em `diagramas/`.

## Modelos

A qualidade do desenho depende do modelo. Modelo fraco erra coordenadas, gasta mais voltas do gate e pode não zerar. Use um modelo de linha principal. O resultado medido neste repositório está em [docs/models.md](docs/models.md).

## Licença

MIT, ver [LICENSE](LICENSE). As partes de terceiros, que são os ícones AWS, o bpmn-js e as fontes IBM Plex, seguem os próprios termos, listados no [README em inglês](README.md#license).
