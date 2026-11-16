# Grafo de contexto

Contexto desenhado como grafo, com duas vistas no mesmo gerador (`scripts/gerar_grafo.py`). Usa `assets/estilo-conceitual.css` e o gate `scripts/conceitual.py`. As coordenadas vêm do elkjs (`estados/`); o desenho é desta skill.

Modelos: `modelos/12-grafo-afirmacoes/` e `modelos/13-mapa-produtos/`, na pasta da skill. Os dois usam o mesmo caso (o endereço de Ana) para que um leia o outro.

## Qual vista

| Vista | Pergunta que responde | Nó | Aresta |
|---|---|---|---|
| `afirmacoes` | o que cada área afirma sobre uma entidade, quem afirmou e quando | entidade (por área) e valor | fato, regra declarada, relação, elo de identidade |
| `produtos` | quais produtos de contexto existem, quem compõe ou traduz quem, que versão o harness consulta e quem decide | produto, tradução, harness, quem age | compõe, traduz, consulta, evento, decide, revisa |

Se a pergunta é como um valor mudou ao longo do tempo numa área só, a tabela de versões (`tabela.md`) mostra melhor. Se é a ordem das chamadas entre sistemas, é sequência. Se é o ciclo de vida de uma afirmação, é máquina de estados.

## Vista `afirmacoes`

A unidade do grafo é a afirmação (a aresta). Toda afirmação tem entidade (o nó de origem), observador, tempo válido e tempo de gravação. O gerador escreve esse carimbo no rótulo da aresta, em mono, embaixo do que se afirma.

```json
{
  "titulo_pagina": "12 · Afirmações sobre Ana",
  "cabecalho": ["<Projeto> · <tema>", "12 · Grafo de afirmações"],
  "vista": "afirmacoes",
  "h1": "Endereço de Ana: afirmações por área",
  "sub": "uma a três frases: o que o desenho mostra e como ler",
  "grupos": [{"id": "cadastro", "nome": "Área · Cadastro"}],
  "observadores": [{"id": "Cadastro", "autoridade": ["endereço"]}],
  "definicoes": ["cliente_ativo"],
  "nos": [
    {"id": "ana", "tipo": "entidade", "nome": "`cliente:ana`", "grupo": "cadastro", "desc": "frase da seção Nós"},
    {"id": "rua_b", "tipo": "valor", "nome": "Rua B"}
  ],
  "arestas": [
    {"de": "ana", "para": "rua_b", "tipo": "fato", "atributo": "endereço",
     "observador": "Cadastro", "valido": ["2026-06-01", null], "gravado": "2026-06-05"}
  ],
  "faixa": {"f1": "um fato do grafo", "f2": "o que ficou fora"},
  "rodape": ["<Projeto>", "Grafo de afirmações · AAAA-MM"]
}
```

- `grupos`: as áreas (Cadastro, Faturamento, CRM). Cada uma vira uma moldura; não há modelo canônico único.
- `observadores`: cada produto de contexto que afirma algo, com os tipos de fato sobre os quais tem autoridade.
- `definicoes`: os termos que têm definição declarada no contexto.
- `nos`:
  - `entidade`: de quem se fala; `nome` entre crases sai em mono (`cliente:ana`).
  - `valor`: o valor de um fato ou a consequência de uma regra. Desenhado como pílula.
  - `desc`: frase da seção "Nós", para quem não vai olhar o desenho. `largura` muda a largura padrão.
- `arestas`, por `tipo`:
  - `fato`: entidade → valor. `atributo` é o tipo de fato. Seta cheia.
  - `regra`: regra declarada, entidade → valor ou entidade. `atributo`, `condicao` e `termos` (os termos da condição). Seta tracejada; o rótulo diz "se <condição>".
  - `relacao`: entidade → entidade, com `rotulo` (titular, controla, responsável). Seta fina.
  - `identidade`: entidade → entidade de outra área, com `confianca` entre 0 e 1. Linha pontilhada, sem ponta. Não pede `valido`.
  - todas pedem `observador` e `gravado`; `fato`, `regra` e `relacao` pedem `valido: [início, fim ou null]`. Datas em `AAAA-MM-DD`.
- Afirmação de observador sem autoridade sobre o `atributo` sai em vermelho com "sem autoridade: desconhecido". Não é erro: é o que o modelo diz desse fato.
- Regra com `"derivada": true` sai em vermelho com "regra derivada: fica no harness".

## Vista `produtos`

A fronteira entre contexto e harness é desenhada sempre: o gerador põe produto e tradução na moldura Contexto e o harness na moldura Harness. Quem age fica fora das duas.

```json
{
  "vista": "produtos",
  "nos": [
    {"id": "cadastro", "tipo": "produto", "nome": "Cadastro de clientes", "versao": 14,
     "dono": "Time de Cadastro", "autoridade": ["endereço"], "camada": "estrutural"},
    {"id": "ident", "tipo": "traducao", "nome": "Resolução de identidade", "versao": 5,
     "dono": "Time de Dados", "autoridade": ["identidade"]},
    {"id": "harness", "tipo": "harness", "nome": "Harness de entregas", "dono": "Harness Designer",
     "desde": "2026-05-20", "politicas": ["endereço com menos de 7 dias pede confirmação"]},
    {"id": "agente", "tipo": "consumidor", "nome": "Agente de entregas", "sub": "recebe a decisão"}
  ],
  "arestas": [
    {"de": "ident", "para": "cadastro", "tipo": "traduz"},
    {"de": "harness", "para": "cadastro", "tipo": "consulta", "versao": 14},
    {"de": "cadastro", "para": "harness", "tipo": "evento", "rotulo": "endereço mudou"},
    {"de": "harness", "para": "agente", "tipo": "decide", "rotulo": "pede confirmação"}
  ]
}
```

Os campos de página (`titulo_pagina`, `cabecalho`, `h1`, `sub`, `faixa`, `rodape`) são os mesmos da outra vista.

- `produto` e `traducao`: `versao`, `dono`, `autoridade` (lista) e `camada` (semântica, comportamental, estrutural, arquitetural), opcional. `area` separa autoridade por área.
- `harness`: `politicas` (lista), `dono` (quem definiu) e `desde`.
- `consumidor`: quem age com a decisão (agente, sistema, AI Operator). `sub` é opcional.
- `arestas`, por `tipo`, com o sentido aceito:
  - `compoe`: produto → produto, com `versao` do componente;
  - `traduz`: tradução → produto, pontilhada;
  - `consulta`: harness → produto, com `versao`;
  - `evento`: produto → harness, com `rotulo` (dividiu, fundiu, nova versão), tracejada;
  - `decide`: harness → quem age, `rotulo` opcional;
  - `revisa`: quem age → harness, tracejada (revisão humana da política).
- `consulta` e `revisa` entram invertidas no layout, para o desenho correr de contexto para harness e de harness para quem age. A ponta continua no sentido declarado.

## O que o gerador confere antes de desenhar

Para com `GRAFO REPROVOU <código>`.

Nas duas vistas:

- `VISTA-INVALIDA`, `TIPO-INVALIDO`, `NO-INCOMPLETO`, `DUPLICADO`, `VAZIO`, `LACO`;
- `DESCONHECIDO`: aresta ou nó cita um id ou grupo que não existe;
- `FRONTEIRA`: o tipo da aresta não liga esses tipos de nó (um produto de contexto não decide; o harness não compõe contexto);
- `MOLDURA-SEM-LUGAR`: toda a borda de uma área é cruzada por setas e o nome não tem onde ficar.

Na vista `afirmacoes`:

- `SEM-OBSERVADORES`: falta a lista `observadores`;
- `SEM-CARIMBO`: afirmação sem `observador`, `gravado` ou `valido`;
- `OBSERVADOR-DESCONHECIDO`: o observador não está em `observadores`;
- `DATA-INVALIDA`: data fora de `AAAA-MM-DD`, ou tempo válido que termina antes de começar;
- `SEM-ATRIBUTO`, `REGRA-SEM-CONDICAO`, `SEM-ROTULO`;
- `TERMO-SEM-DEFINICAO`: regra declarada usa termo sem definição em `definicoes`. É a regra de fechamento: declare a definição ou marque `"derivada": true`;
- `IDENTIDADE-SEM-CONFIANCA`: elo de identidade sem `confianca` entre 0 e 1;
- `IDENTIDADE-MESMA-AREA`: elo de identidade entre duas entidades da mesma área;
- `VALOR-SOLTO`: valor que nenhuma afirmação aponta.

Na vista `produtos`:

- `SEM-DONO`, `SEM-VERSAO`: dono e versão são propriedades do produto;
- `AUTORIDADE-DUPLICADA`: dois produtos com autoridade sobre o mesmo tipo de fato na mesma área;
- `HARNESS-SEM-POLITICA`, `POLITICA-SEM-AUTOR`: o harness lista as políticas, quem as definiu e desde quando;
- `REFERENCIA-SEM-VERSAO`: `compoe` ou `consulta` sem `versao`. Produtos se referem por número de versão, não por relógio;
- `CICLO-COMPOSICAO`: a composição volta para um produto já visitado.

## Comandos

```bash
python3 <skill>/scripts/gerar_grafo.py diagramas/_src/NN-nome.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-nome.html
```

Precisa de `node` no PATH. O gate de desenho é o do conceitual (lista em `references/raias.md`). Se reprovar, encurte rótulos, divida o grafo em dois ou fixe `"direcao": "DOWN"`. Não edite o HTML gerado.

## Na leitura do PNG

- cada rótulo fica colado na sua aresta e o carimbo se lê inteiro;
- as molduras separam as áreas (ou contexto e harness) sem nó cortado;
- o vermelho aparece só em afirmação sem autoridade ou regra derivada;
- a seção "Nós" explica cada entidade sem precisar do desenho.
