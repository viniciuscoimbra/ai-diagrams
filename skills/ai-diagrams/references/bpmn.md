# BPMN 2.0

Processo em BPMN nativo, editável no Camunda Modeler ou em demo.bpmn.io. Ninguém desenha SVG nem escreve XML: o modelo é um JSON, e `bpmn/gerar_bpmn.py` calcula o layout, roteia as conexões e emite BPMN 2.0 com BPMNDI. A renderização é do bpmn-js 18.31.0, empacotado em `bpmn/vendor/` com a licença (o logo do bpmn.io fica no desenho, como a licença pede).

Modelo: `modelos/08-bpmn/`, na pasta da skill.

## Quando é BPMN e quando é raia

BPMN quando o pedido diz BPMN, processo, gateway, evento, ou quando o resultado precisa ser editável numa ferramenta de processo. Fluxo entre times sem essa exigência vai para raias (`references/raias.md`), que lê melhor num documento.

## Modelo JSON

```json
{
  "id": "contestacao",
  "title": "Contestação de pagamento",
  "subtitle": "uma ou duas frases factuais",
  "cabecalho": ["Empresa · Projeto", "08 · BPMN · V1"],
  "rodape": "Autor · Projeto · AAAA-MM",
  "lanes": [{"id": "cliente", "name": "Cliente"}, {"id": "ops", "name": "Operações"}],
  "nodes": [
    {"id": "inicio", "type": "startEvent", "name": "Cliente contesta", "lane": "cliente", "col": 0},
    {"id": "analisar", "type": "task", "name": "Analisar transação", "lane": "ops", "col": 1},
    {"id": "procede", "type": "exclusiveGateway", "name": "Procede?", "lane": "ops", "col": 2}
  ],
  "flows": [{"from": "inicio", "to": "analisar"}, {"from": "procede", "to": "fim", "name": "Sim"}]
}
```

| Campo | Regra |
|---|---|
| `type` | `startEvent`, `endEvent`, `task`, `callActivity`, `exclusiveGateway`, `parallelGateway`, `intermediateCatchEvent`, `intermediateThrowEvent` |
| `event` | opcional: `timer`, `message` ou `condition` (com `condition`) |
| `lane` | quem executa de fato a atividade |
| `col`, `row` | coluna de 0 a 6 (largura 240); `row: 1` abre uma segunda linha na mesma raia, para alternativa ou volta |
| `name` | `\n` quebra a linha dentro da tarefa |
| `doc` | opcional: texto ou objeto, vira `documentation` do elemento |
| `flows[].name` | obrigatório em todo ramo que sai de decisão |
| `flows[].via` | `top` ou `bottom` força a saída por cima ou por baixo, para voltas não atravessarem tarefas |
| `columnWidth`, `laneHeight` | opcionais, no topo do modelo |

Diagrama legível: até sete colunas, quatro a seis raias, até dezoito atividades. Todo caminho termina num `endEvent`. Dois caminhos que terminam no mesmo lugar ficam na mesma raia, em linhas diferentes, para as setas não correrem coladas.

## Gate

`gerar_bpmn.py` só grava saída com tudo em zero:

- `ESTRUTURA`: ids únicos, conexão para nó existente, nó sem entrada (exceto início) ou sem saída (exceto fim), ramo de decisão sem rótulo, tipo ou raia inexistente;
- `ALCANCE`: todo nó é alcançado a partir de um início e chega a um fim;
- `SOBREPOSICAO`: duas formas na mesma posição;
- `IMPORTACAO`: o bpmn-js importa o XML no Chrome sem erro e sem aviso.

## Comandos

```bash
python3 <skill>/bpmn/gerar_bpmn.py diagramas/_src/NN-processo.json
```

Gera `NN-processo.bpmn` (o editável, que vai para o git), `NN-processo.html` (viewer offline) e `NN-processo.png`. Olhe o PNG: seta correndo colada em outra ou rótulo longe do ramo pedem outra `col`, `row` ou `via`.
