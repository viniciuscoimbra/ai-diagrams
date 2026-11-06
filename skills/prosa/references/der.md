# DER por schema e matriz de dependência

Os dois geradores leem o mesmo modelo lógico. O conteúdo das caixas sai do modelo; a posição de cada tabela e o caminho de cada seta são decididos à mão no layout.

## Modelo lógico (`modelo.json`)

```json
{
  "cabecalho": "Empresa · Projeto · Cliente",
  "rodape": "Empresa · modelo lógico · AAAA-MM",
  "schemaComum": "comum",
  "schemaLeitura": null,
  "colunasControle": [],
  "schemas": { "comum": "domínios gerais", "conta": "Contas e movimentos" },
  "tabelas": {
    "conta.contas": {
      "tipo": "forte",
      "rotulo": "a conta de pagamento do cliente",
      "colunas": [
        ["conta_id", "uuid", "PK"],
        ["cliente_id", "uuid", "FK", "cadastro.clientes", true],
        ["numero", "varchar(20)", "UQ"],
        ["aberta_em", "timestamptz", ""]
      ]
    }
  }
}
```

| Campo | O que é |
|---|---|
| `cabecalho`, `rodape` | texto do cabeçalho e do rodapé de todo DER e da matriz |
| `schemaComum` | schema de domínios gerais e referências; na fronteira aparece como "usa de" |
| `schemaLeitura` | schema de views de leitura, se houver; nulo quando não existe |
| `colunasControle` | colunas extras escondidas das caixas; `criado_em`, `atualizado_em`, `versao_registro` e `deletado_em` já são escondidas |
| `schemas` | nome de cada schema; a ordem das chaves é a ordem da matriz |
| `tabelas` | chave `schema.tabela`; o nome físico é a parte depois do ponto |

Cada coluna é `[nome, tipo, chave, alvo, obrigatoria]`. `chave` é `PK`, `FK`, `UQ` ou vazio. Para `FK`, `alvo` é a tabela apontada e `obrigatoria` é `true` quando a coluna é not null: isso decide a ponta da seta (um, ou zero ou um).

Tipos de tabela e a cor candy de cada um:

| `tipo` | Rótulo | Quando usar |
|---|---|---|
| `forte` | entidade forte | existe por si; as outras apontam para ela |
| `dependente` | dependente | só existe ligada a uma entidade forte |
| `associativa` | associativa | liga duas entidades, muitos para muitos |
| `controle` | controle de processo | execução, lote, agenda |
| `fato` | fato · imutável | algo que aconteceu; gravado uma vez |
| `versionada` | versões · imutável | cada mudança é uma linha nova |
| `projecao` | projeção | estado calculado a partir dos fatos |
| `trilha` | técnica | outbox ou deduplicação de consumo |
| `dominio` | domínio | lista fechada de valores |
| `configuracao` | configuração | regra que o banco consulta, como transições permitidas |
| `referencia` | referência | lista oficial carregada de fonte externa |
| `visao` | view de leitura | view montada a partir de outros schemas |

`dominio`, `referencia` e `configuracao` são tabelas leves: não entram no desenho principal, vão para a faixa de baixo com a lista de quem usa cada uma. A coluna que aponta para elas aparece na cor de domínio, sem seta.

## Layout (`der-<schema>.layout.mjs`)

```js
export default {
  modelo: './modelo.json',
  schema: 'conta',
  titulo: 'schema conta · Contas e movimentos',
  sub: 'duas ou três frases factuais',
  canvas: { w: 1700 },
  tabelas: {
    'conta.contas': { x: 685, y: 260, desc: 'a conta de pagamento do cliente' }
  },
  arestas: [
    { de: 'conta.movimentos', coluna: 'conta_id', sai: 'L', para: 'conta.contas', chega: 'R', raia: 1200, dy: 40,
      texto: 'Uma <b>conta</b> recebe zero ou muitos <b>movimentos</b>.' }
  ]
};
```

- `tabelas`: toda tabela não leve do schema precisa estar aqui; o gerador recusa o que faltar. `w` opcional muda a largura (padrão 330).
- Cada aresta sai da linha da coluna de FK, pelo lado `sai` (`L` ou `R`) da tabela de origem.
- `chega` `L` ou `R`: a seta corre na vertical pela `raia` (x) e entra no lado da tabela de destino na altura `dy` (relativa ao topo dela; `'reto'` mantém a altura de saída). Sem `raia`, a seta é reta.
- `chega` `T` ou `B`: entra por cima ou por baixo em `dx` (relativo à esquerda da tabela), com `raia` e `yRaia` opcionais.
- `pontos`: caminho explícito quando o roteamento padrão não serve; `'x0'` e `'y0'` são o ponto de saída.
- O badge vai no meio do segmento mais longo; `seg` e `frac` escolhem outro, e `badge: [x, y]` fixa o centro.
- `semSeta`: `{ 'schema.tabela.coluna': 'motivo' }` desenha a FK sem seta, com o motivo no rótulo.
- `externas` e `leitura: true` servem ao DER de views de leitura: tabelas de outro schema desenhadas tracejadas como alvo, setas tracejadas sem cardinalidade.

Raias diferentes para setas diferentes: duas setas na mesma raia ficam colineares e o lint reprova.

## Comandos

```bash
node <skill>/der/der-montar.mjs diagramas/_src/der-conta.layout.mjs
python3 <skill>/scripts/build.py diagramas/_src/der-conta.html

node <skill>/der/der-visao-geral.mjs diagramas/_src/modelo.json
python3 <skill>/scripts/build.py diagramas/_src/der-visao-geral.html
```

A altura do build se ajusta até o rodapé aparecer inteiro no PNG.
