# Importar arquivos existentes

Use `scripts/importar.py` quando já existe um arquivo de diagrama ou dados. O importador escreve fontes nativos e chama os geradores desta skill. Não renderiza por Mermaid e não reaproveita o desenho do XML. A entrada original não é alterada.

```bash
python3 <skill>/scripts/importar.py arquivo.mmd --saida diagramas --idioma pt-BR
python3 <skill>/scripts/importar.py schema.sql --tipo matriz --saida diagramas --idioma pt-BR
```

`ai-diagrams importar` repassa os mesmos argumentos quando a CLI npm está instalada. Os tipos são `der`, `matriz`, `catalogo`, `comparacao`, `bpmn`, `raias`, `sequencia` e `estados`, compatíveis com o formato da entrada. O idioma muda os rótulos fixos; o texto autoral deve estar no idioma desejado.

`--tema` aceita nome ou caminho do tema, como nos demais geradores. DER e matriz mantêm fontes em `<saida>/_src/<nome-da-entrada>/` e entregáveis em `<saida>/<nome-da-entrada>/`. Cada entrada tem seu relatório `<nome-da-entrada>.importacao.json`, reiniciado como pendente antes de cada tentativa. `SAIDA-CONFLITA` impede substituir o BPMN original pela saída; escolha outro diretório. Entrada que não é UTF-8 retorna `ENTRADA-INVALIDA`.

`--somente-fonte` converte e gera o fonte sem executar o Chrome. A saída avisa que o gate completo e o PNG estão pendentes. Não declare esse modo como aprovação geométrica. Sem a flag, o comando executa o gerador e o gate de sempre.

## Mermaid

Arquivos `.mmd` ou `.mermaid`, em UTF-8. Uma declaração por linha. Comentários `%%` comuns são aceitos; diretivas `%%{...}%%`, configurações, front matter, estilos e instruções fora do subconjunto reprovam com `MERMAID-NAO-SUPORTADO: linha N`. Rótulos são texto simples, sem HTML.

### Flowchart e graph

Cabeçalho `flowchart LR`, `flowchart TD`, `flowchart TB` ou a forma com `graph`. O layout é recalculado; a direção de apresentação original não é uma coordenada a preservar.

- Nós por identificador, retângulos `A[Texto]`, decisões `B{Pergunta}` e círculos `C((Texto))`.
- Uma conexão por declaração: `A --> B` ou `A -->|Rótulo| B`. Nós podem ser declarados na conexão.
- Sem `subgraph`, a saída é BPMN: retângulo vira tarefa, losango vira gateway exclusivo e círculo sem entrada/saída intermediária vira início/fim.
- Raízes e folhas sem círculos explícitos ganham os eventos de início e fim necessários ao contrato BPMN. Os nós e conexões da entrada são preservados.
- Com `subgraph id[Nome da raia]` e `end`, a saída é raias. Cada nó precisa pertencer a uma raia. Somente nós retangulares, conexões sem rótulo e fluxo sem ciclos são aceitos nesse modo.
- Não aceita subgraphs aninhados, um nó em duas raias, formas adicionais, conexões encadeadas, setas pontilhadas ou estilos.

`subgraph` representa responsabilidade de um ator. Se o arquivo usa esse recurso apenas para agrupamento técnico, adapte a entrada antes de importar para raias. BPMN e raias são escolhas de representação do importador, sem conversão para desenho livre.

### Sequência

Cabeçalho `sequenceDiagram`. Aceita `participant id as Nome`, `actor id as Nome` e participantes implícitos nas mensagens. Mensagens `A->>B: Texto` são síncronas, `B-->>A: Texto` são respostas e `A-)B: Texto` são assíncronas.

Aceita `Note over A: Texto`, fragmentos `alt condição` / `else condição` / `end`, `loop condição` e `opt condição`, inclusive aninhados. Ativação explícita, `par`, `critical`, `break`, notas sobre vários participantes e outras formas de seta reprovam. O gerador decide as barras de ativação pelo contrato nativo.

### Estados

Cabeçalho `stateDiagram-v2`. Aceita `state "Nome" as id`, `[*] --> inicial`, `A --> B: evento`, `final --> [*]` e `direction LR` ou `direction TB`. Há exatamente uma entrada inicial. Transições entre estados exigem evento; estados finais não têm saída.

Estados compostos, concorrência, histórico, notas, escolhas, guardas e ações em sintaxe adicional não fazem parte deste subconjunto. O gate nativo continua validando alcance e saídas.

### ER

Cabeçalho `erDiagram`. Entidades em blocos `ENTITY { ... }`, com atributos `tipo nome` e chave opcional `PK`, `FK` ou `UK`. A entidade precisa ser declarada; atributos e entidades repetidos reprovam. Comentários de atributos entre aspas também reprovam porque as colunas do DER nativo não têm campo de exibição para esse texto.

Relações aceitas: `PARENT ||..o{ CHILD : rótulo` ou `PARENT |o..o{ CHILD : rótulo`. São relações não identificadoras, com exatamente um ou zero/um pai, e zero/muitos filhos. Uma coluna `FK` não ambígua na entidade filha precisa corresponder à relação. A inferência usa o nome da PK ou o nome da entidade seguido da PK; se só houver uma FK disponível, usa essa coluna.

Outras cardinalidades, relação identificadora `--`, chaves combinadas e relações ambíguas reprovam em vez de receber uma cardinalidade aproximada. Os modelos ficam no schema `public`.

## BPMN 2.0 XML

Arquivo `.bpmn` com namespace `http://www.omg.org/spec/BPMN/20100524/MODEL`, exatamente um processo descritivo (`isExecutable="false"` ou omitido), raias opcionais e uma pool opcional apontando para esse processo. O layout BPMNDI é substituído pelo layout nativo.

Nós aceitos: `task`, `callActivity`, `startEvent`, `endEvent`, `exclusiveGateway`, `parallelGateway`, `intermediateCatchEvent` e `intermediateThrowEvent`. Conexões são `sequenceFlow`; `incoming`, `outgoing` e `flowNodeRef`, quando presentes, precisam apontar para os elementos corretos. Documentação em texto simples do processo e dos nós é preservada.

Eventos aceitos: marcador de mensagem sem `messageRef`, marcador de timer sem duração e condição com texto em `conditionalEventDefinition/condition`. Timer e condição se aplicam a início ou captura intermediária. O motor não é um executor de processos.

Retorna `BPMN-NAO-SUPORTADO` com a linha para elementos e atributos sem equivalente nativo. Isso inclui tarefas especializadas (`userTask`, `serviceTask`, `scriptTask`), processos executáveis, subprocessos, boundary events, message flows, múltiplas pools, extensões Camunda/Zeebe, condições de sequence flow, ramo `default`, duração de timer, `calledElement`, documentação de raia/fluxo e semântica de execução. DTD, entidades e instruções de processamento XML também reprovam. Não remova esses elementos automaticamente para obter uma importação aparentemente bem-sucedida.

O BPMN gerado contém IDs e coordenadas próprios. É um novo documento descritivo editável, não um arquivo para implantar em um runtime de workflow.

## SQL DDL

Arquivo `.sql`, com `CREATE SCHEMA` e `CREATE TABLE`. Identificadores simples, com schema opcional; sem schema, usa `public`. Aceita tipos simples com precisão opcional, PK e UNIQUE de uma coluna, `NOT NULL`, referências inline ou `FOREIGN KEY` de uma coluna. FKs precisam apontar para tabelas presentes no arquivo. Valores default simples ficam no modelo convertido.

`--tipo der` é o padrão; `--tipo matriz` gera a matriz. Identificadores entre aspas, ALTER, índices, checks, chaves compostas e outras construções não suportadas retornam `SQL-NAO-SUPORTADO`. O layout automático aceita até 16 FKs internas por schema. FKs entre schemas usam a fronteira e os rótulos nativos. O modelo visual não substitui o DDL para migrations.

## CSV de catálogo

Arquivo `.csv` separado por vírgulas, com cabeçalho, de duas a cinco colunas e de uma a dez linhas de dados. A primeira coluna identifica o card; as demais viram seus campos. Os nomes de coluna são textos visíveis, portanto devem estar traduzidos. Campos CSV entre aspas são aceitos. Cabeçalhos repetidos, campos vazios ou linhas com outra quantidade de colunas retornam `CSV-NAO-SUPORTADO`.

## YAML de comparação

Arquivo `.yaml` ou `.yml` com este contrato:

```yaml
titulo: Filas de mensagens
subtitulo: Características operacionais
opcoes:
  - SQS
  - Kinesis
criterios:
  - nome: Consumo
    valores: ["Fila", "Stream"]
```

De duas a quatro opções; cada critério tem um `nome` e um valor textual por opção. `subtitulo` é opcional. Strings e listas entre aspas usam a sintaxe JSON. Um objeto JSON completo com os mesmos campos também é aceito, por ser um subconjunto de YAML. Âncoras, tags, blocos multilinha, tabs, campos adicionais e outros formatos reprovam com `YAML-NAO-SUPORTADO`.

## Referências de formato

O subconjunto acima é uma decisão deste importador. As especificações completas têm recursos adicionais: [Mermaid flowchart](https://mermaid.js.org/syntax/flowchart.html), [sequência](https://mermaid.js.org/syntax/sequenceDiagram.html), [estados](https://mermaid.js.org/syntax/stateDiagram.html), [ER](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) e [BPMN da Camunda](https://docs.camunda.org/manual/latest/reference/bpmn20/).
