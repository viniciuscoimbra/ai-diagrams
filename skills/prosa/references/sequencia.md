# Diagrama de sequência

Quem chama quem, em que ordem, e quem espera a resposta. Participante é coluna, mensagem é linha, o tempo desce. Usa `assets/estilo-conceitual.css` e o gate `scripts/conceitual.py`.

Modelo: `modelos/09-sequencia/`, na pasta da skill.

## Quando usar

- chamada entre serviços, API, banco, fila ou sistema externo, e a ordem e a espera importam: "o que acontece quando o app chama X";
- protocolo com ida e volta (autenticação, pagamento, integração com parceiro);
- caminho alternativo ou repetição dentro da mesma conversa (`alt`, `loop`, `opt`).

Se o desenho é sobre onde cada serviço fica e como se liga (rede, conta, camada), é poster. Se as linhas são times e o assunto é quem faz o quê, é raias. Se a pergunta é a topologia com passos numerados em cima, é fluxo com passos.

## Spec (`gerar_sequencia.py`)

As coordenadas são calculadas a partir do JSON; ninguém escreve pixel.

```json
{
  "titulo_pagina": "09 · Pix de saída",
  "cabecalho": ["<Projeto> · <tema>", "09 · Sequência"],
  "kicker": "Diagrama de sequência",
  "h1": "Pix de saída: da chamada do app à confirmação do SPI",
  "sub": "uma a três frases: o que o desenho mostra, o recorte e como ler",
  "participantes": [
    {"id": "app", "nome": "App do cliente", "sub": "iOS e Android", "tipo": "ator", "icone": "aws://general/mobile-client.png"},
    {"id": "pix", "nome": "Serviço Pix", "sub": "ECS Fargate", "tipo": "servico", "icone": "aws://compute/fargate.png"},
    {"id": "spi", "nome": "SPI · ICOM", "sub": "Banco Central", "tipo": "externo"}
  ],
  "mensagens": [
    {"de": "app", "para": "pix", "texto": "`POST /pix`", "passo": "o que acontece neste passo"},
    {"de": "pix", "para": "pix", "texto": "confere limite"},
    {"nota": "limite diário vem do cadastro", "sobre": "pix"},
    {"fragmento": "alt", "ramos": [
      {"guarda": "score abaixo de 0,8", "mensagens": [
        {"de": "pix", "para": "spi", "texto": "`pacs.008`", "tipo": "assincrona"}
      ]},
      {"guarda": "score a partir de 0,8", "mensagens": []}
    ]},
    {"de": "pix", "para": "app", "texto": "`201`", "tipo": "resposta"}
  ],
  "faixa": {"f1": "um fato do fluxo", "f2": "o que ficou fora do desenho"},
  "rodape": ["<Projeto>", "Diagrama de sequência · AAAA-MM"]
}
```

- `participantes`: na ordem das colunas, da esquerda para a direita. Ponha quem inicia à esquerda e o sistema externo à direita. `tipo` aceita `ator`, `servico`, `banco`, `fila`, `externo` (borda tracejada) e `sistema`; vira o rótulo em cima do nome. `icone` é opcional, no formato `aws://categoria/arquivo.png` conferido no acervo. `nome` em até três palavras; `sub` curto (tecnologia ou papel).
- `mensagens`: na ordem do tempo.
  - `tipo`: `sincrona` (padrão, seta cheia), `assincrona` (seta aberta) ou `resposta` (tracejada).
  - `texto` curto. Trecho entre crases vira código: endpoint, evento, campo, status HTTP.
  - `de` igual a `para` desenha o laço de mensagem para si mesmo.
  - `passo` numera a mensagem: o badge vai na seta, e o texto vai na seção "Passos" abaixo do desenho. Numere só as mensagens que o leitor precisa entender. Ida e volta óbvias ficam sem passo.
- `nota` + `sobre`: caixa tracejada sobre a linha de vida do participante, para uma regra ou um dado que não é mensagem.
- `fragmento`: `alt` (caminhos alternativos, um ramo por guarda), `loop` (repetição, um ramo com a condição de parada) ou `opt` (um ramo que pode não acontecer). Fragmentos aninham. A guarda é a condição em texto curto, sem colchetes.
- A seção "Notação" sai sozinha, só com os tipos de seta usados.

## O que o gerador decide

- **Barra de ativação**: chamada síncrona abre a barra no destino. A primeira `resposta` do destino para quem chamou fecha a barra. Sem resposta, a barra vai até a última mensagem do participante. Escreva a resposta sempre que a espera importa.
- **Rótulo**: fica no vão vizinho da origem, do lado para onde a seta anda. O vão alarga até o rótulo caber; passou de 228px, o rótulo quebra em linhas. Texto nunca cruza linha de vida.
- **Largura**: com seis participantes e rótulos curtos, o canvas fica perto de 1300px. Acima de 1320, o fonte declara `<meta name="largura">` e a página cresce. Sete participantes é o limite confortável. Com mais que isso, divida a conversa em dois diagramas ou agrupe participantes.

## Comandos

```bash
python3 <skill>/scripts/gerar_sequencia.py diagramas/_src/NN-nome.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-nome.html
```

Participante não declarado faz o gerador parar com mensagem. O gate é o do conceitual (lista em `references/raias.md`), com uma régua a mais:

- `TEXTO-SOBRE-VIDA`: rótulo, guarda de fragmento ou nome de ramo em cima de uma linha de vida ou de uma barra de ativação.

Se reprovar, encurte o rótulo, troque a ordem dos participantes ou mova a mensagem para um passo. Não edite o HTML gerado: ele é refeito a cada rodada.

## Na leitura do PNG

- toda seta encosta na barra ou na linha de vida do destino;
- nenhuma barra de ativação fica aberta sem motivo (falta `resposta`?);
- a guarda de cada ramo cabe na linha e não encosta em seta;
- os passos contam a história sem precisar olhar o desenho.
