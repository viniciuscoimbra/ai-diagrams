# Fluxo em raias e diagramas conceituais

Diagramas sem AWS: quem faz o quê, em que ordem, entre times ou papéis. Usam `assets/estilo-conceitual.css` (fundo off-white com grid, painéis brancos, faixa preta de fechamento) e o gate `scripts/conceitual.py`.

Modelos: `modelos/06-raias/` (fluxo em raias gerado de JSON) e `modelos/07-catalogo-cards/` (catálogo em cards escrito à mão), na pasta da skill.

## Fluxo em raias (`gerar_raias.py`)

Raia é linha (o ator), fase é coluna (o momento). As coordenadas são calculadas a partir do JSON; ninguém escreve pixel.

```json
{
  "titulo_pagina": "06 · Abertura de conta",
  "cabecalho": ["Empresa · Projeto", "06 · Raias"],
  "kicker": "Fluxo em raias",
  "h1": "Abertura de conta: do pedido à conta ativa",
  "sub": "uma ou duas frases factuais",
  "raias": [{"nome": "Cliente", "sub": "pelo app"}, {"nome": "Onboarding", "sub": ""}],
  "fases": ["Pedir", "Verificar"],
  "elementos": [
    {"raia": 0, "fase": 0, "texto": "Enviar documento"},
    {"raia": 1, "fase": 1, "texto": "Conferir documento", "chip": "em análise", "titulo": "opcional", "estilo": "foco"}
  ],
  "sequencia": [[0, 0, 1, 1]],
  "secoes": [
    {"titulo": "Situação do pedido", "tipo": "passos", "itens": [["Em análise", "o que significa"]]},
    {"titulo": "Quem recebe", "tipo": "destinos", "itens": [["Cliente", "o que recebe"]]}
  ],
  "faixa": {"f1": "a frase que fecha o diagrama", "f2": "o que ficou de fora"},
  "rodape": ["Autor", "Projeto · AAAA-MM"]
}
```

- `elementos`: um por célula raia × fase. `chip` é a situação abaixo do painel; `estilo` aceita `foco` (borda na cor de acento) e `fora` (risco, vermelho).
- `sequencia`: pares `[raia, fase, raia, fase]`. A seta anda da esquerda para a direita pelo corredor entre as fases; na mesma fase, desce ou sobe pela coluna. Um painel pode ter várias saídas (bifurcação) e várias chegadas: cada seta ganha altura de saída, altura de chegada e x de corredor próprios, e o corredor alarga com o número de setas. Seta que pula fases dobra no corredor junto da origem ou junto do destino; o gerador testa as opções e as ordens de saída e chegada e fica com o desenho de menos cruzamentos. Se a seta só passaria por cima de um painel, o gerador para com mensagem: troque a raia ou a fase de um dos painéis.
- Largura: o canvas fica em até 1320px; com muitos corredores, os painéis estreitam até 140px antes de a página crescer.
- `secoes`: `passos` vira a legenda com borda preta em cima; `destinos` vira cards com borda superior.
- Até sete fases cabem na largura de 1400px; cinco raias é o limite confortável de leitura.

```bash
python3 <skill>/scripts/gerar_raias.py diagramas/_src/NN-fluxo.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-fluxo.html
```

## Diagrama conceitual à mão (cards, painéis)

Para catálogo, anatomia de um artefato ou relação entre times sem ordem de fluxo, escreva o HTML partindo do modelo 07. Classes do CSS conceitual:

| Classe | Uso |
|---|---|
| `.grid` + `.card` (`.sid`, `.snome`, `.linha` com `.rot` e `.txt`, `.slug`) | catálogo em cards, cinco por linha |
| `.canvas` + `.painel` (`.pt`, `.ps`, `.ptag`) | painéis posicionados em absoluto, com setas em `svg.edges` |
| `.lane`, `.fase`, `.chip` | raias, títulos de fase e situação |
| `.legenda` + `.passo`, `.destinos` + `.destino` | seções abaixo do desenho |
| `.faixa` (`.f1`, `.f2`) | fechamento em faixa escura com barra na cor de acento |

### Cards: largura, grade e moldura

- A página conceitual tem 1400px e é lida exibida a 1000px; o gate reprova texto abaixo do piso nessa escala (`TEXTO-MINIMO`). Não alargue a página nem copie o CSS para o projeto: com a página mais larga, o mesmo texto fica pequeno demais e reprova.
- `.grid` tem cinco colunas fixas. Seis a dez cards quebram sozinhos em duas linhas; não mude `grid-template-columns`. Mais de dez cards: divida em dois diagramas.
- Cada card tem `.sid` (código curto), `.snome` (nome em até três palavras, para caber numa linha), até três `.linha` com `.rot` e `.txt` (uma frase curta cada) e `.slug`. Texto que não cabe reprova com `TRANSBORDA`.
- Moldura: `.hdr` com `<Projeto> · <tema>` à esquerda e `NN · <nome>` à direita; `.foot` com autor ou projeto à esquerda e `<tipo> · AAAA-MM` à direita. Rodapé não vai no cabeçalho.

## Gate (`conceitual.py`)

Mede tudo no Chrome nas mesmas condições do screenshot e reprova com exit 1:

- `TRANSBORDA`: texto maior que a caixa;
- `SOBREPOE`: duas caixas de conteúdo se cruzam;
- `FORA-DA-PAGINA`, `FORA-DO-CANVAS`: elemento sai da moldura;
- `TEXTO-MINIMO`: texto abaixo do piso de leitura na largura de exibição (`--exibicao`, padrão 1000px);
- `ROTULO-SOBRE-CAIXA`: rótulo solto cobrindo caixa alheia;
- `SETA-SOLTA`, `SETA-SOBRE-TEXTO`: ponta que não encosta em caixa, seta cruzando texto;
- `COLINEAR`: duas setas diferentes correndo na mesma linha.

Não exige passos numerados nem badge na seta: essa régua é dos posters. A altura da captura é medida sozinha (`--altura auto`, padrão). O CSS vem de `_estilo-conceitual.css` do projeto, se existir; senão, o da skill.
