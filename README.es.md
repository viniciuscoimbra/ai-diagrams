# Prosa

**Descríbelo con palabras. Recibe un diagrama que pasa la revisión.**

[English](README.md) · [Português](README.pt-BR.md)

Prosa es una skill para CLIs de IA (Claude Code, Codex CLI, Kiro CLI). Describes el diagrama en lenguaje natural, o señalas un documento, un DDL o la descripción de un proceso, y la IA escribe la fuente del diagrama, ejecuta un gate geométrico y genera el PNG. El gate rechaza:
- texto superpuesto;
- flechas sueltas o que cruzan cajas;
- badges fuera de la flecha;
- contenido cortado en el borde de la página;
- texto por debajo del tamaño mínimo.

La IA corrige la fuente hasta que el gate pasa, y solo entonces entrega.

La fuente queda en tu repositorio, en texto, y cualquiera puede editarla y volver a generar el PNG.

## Tipos de diagrama

| Tipo | Ejemplo de pedido | Ejemplo |
|---|---|---|
| Póster de arquitectura AWS | "Póster de arquitectura de la API de pagos: API Gateway, Lambda, Aurora y EventBridge." | [prompt y resultado](exemplos/arquitetura-aws/) |
| Flujo con pasos numerados | "Flujo con pasos del outbox al consumidor, con Debezium y MSK." | [prompt y resultado](exemplos/fluxo-passos/) |
| Diagrama de secuencia | "Diagrama de secuencia de la autorización de compra con tarjeta: terminal, red de tarjetas, autorizador, antifraude y ledger." | [prompt y resultado](exemplos/sequencia/) |
| Carriles (swimlanes) | "Flujo en carriles de la apertura de cuenta entre cliente, onboarding, riesgo y operaciones." | [prompt y resultado](exemplos/raias/) |
| BPMN 2.0 (editable en Camunda o bpmn.io) | "BPMN del proceso de disputa de pago." | [prompt y resultado](exemplos/bpmn/) |
| Tabla comparativa | "Tabla que compare SQS, Kinesis y MSK para eventos entre dominios." | [prompt y resultado](exemplos/tabela-comparacao/) |
| Catálogo en tarjetas | "Catálogo en tarjetas de las APIs de la plataforma, con responsable y contrato." | [prompt y resultado](exemplos/catalogo-cards/) |
| Diagrama ER por schema | "Diagrama ER del schema de cobros a partir de este DDL." | [prompt y resultado](exemplos/der-schema/) |
| Matriz de dependencias entre schemas | "Matriz de dependencias entre los schemas de este DDL." | [prompt y resultado](exemplos/matriz-dependencia/) |

![Póster de arquitectura AWS](exemplos/arquitetura-aws/resultado/antifraude-transferencias.png)

## Requisitos

| Elemento | Para qué | Comprobar |
|---|---|---|
| Python 3.9 o superior | gate y PNG | `python3 --version` |
| Paquete `diagrams` | iconos oficiales de AWS | `python3 -c "import diagrams"` |
| Node 18 o superior | diagrama ER y matriz | `node --version` |
| Google Chrome | genera el PNG (headless) | `ls "/Applications/Google Chrome.app"` |
| una CLI de IA | Claude Code, Codex CLI o Kiro CLI | `claude --version`, `codex --version` o `kiro-cli --version` |

Instala los iconos con `pip3 install diagrams`. Si Chrome está en otra ruta, indícala en `POSTER_CHROME`.

## Instalación

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

Ejecuta Codex con `codex --sandbox danger-full-access`. El sandbox por defecto bloquea Chrome headless, y sin él el gate no se ejecuta.

**Kiro CLI**

```bash
bash "$PROSA"/ferramentas/instalar-kiro.sh /ruta/de/tu/proyecto
```

Después, dentro del proyecto, ejecuta `kiro-cli chat --agent prosa`.

Las instrucciones paso a paso están en [docs/install.md](docs/install.md), en inglés. Incluyen el uso sin CLI (Proyectos de Claude.ai, ChatGPT).

## Cómo pedir

Empieza el pedido con "Usa la skill prosa", para que la IA no responda en texto:

```text
Usa la skill prosa. Lee docs/decision-antifraude.md y haz el póster de arquitectura AWS
del antifraude en tiempo real, con pasos numerados.
```

La IA elige el tipo y pregunta antes de dibujar cuando el pedido es ambiguo. Después escribe la fuente en `diagramas/_src/`, ejecuta el gate hasta que pase y guarda el PNG en `diagramas/`.

## Modelos

La calidad del diagrama depende del modelo. Un modelo débil se equivoca en las coordenadas, necesita más rondas del gate y puede no llegar a cero. Usa un modelo de primera línea. Los resultados medidos en este repositorio están en [docs/models.md](docs/models.md).

## Licencia

MIT, ver [LICENSE](LICENSE). Las partes de terceros, que son los iconos de AWS, bpmn-js y las fuentes IBM Plex, siguen sus propios términos, listados en el [README en inglés](README.md#license).
