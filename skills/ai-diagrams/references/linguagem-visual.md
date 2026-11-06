# Linguagem visual dos posters

O poster é uma página editorial: moldura de texto em volta de um canvas de desenho. Tudo dentro do canvas usa `position:absolute` com coordenadas em pixels. O layout é decisão de quem desenha; não existe auto-layout.

## Moldura editorial (fora do canvas)

| Elemento | Classe | Conteúdo |
|---|---|---|
| Cabeçalho | `.hdr` | dois spans: identidade à esquerda, código do diagrama à direita |
| Kicker | `.kicker` | categoria em caps, com `<span class="sq">■</span>` na cor de acento |
| Título | `h1` | o nome técnico do fluxo ou sistema; sem tese, sem frase de efeito, termos técnicos em inglês |
| Subtítulo | `.sub` | 2 a 3 frases factuais: o que o diagrama mostra e o estado medido, com números; sem dramatização |
| Passos | `.passos` | lista numerada `.pitem` (badge `.pb` + frase); narra o fluxo na ordem de leitura |
| Rodapé | `.foot` | autor · empresa · data |

Layout do miolo: `.wrap` põe canvas e passos lado a lado (canvas 1140px). `.wrap.stack` empilha (canvas 1700px, passos em 3 colunas abaixo); usar quando o desenho precisa de largura.

## Contêineres (frames)

Todos são `<div class="frame X">` com `.flabel` dentro:

| Classe | Semântica | Traço |
|---|---|---|
| `awscloud` | fronteira da AWS; flabel leva `<img src="aws://aws.png">` | sólido preto 1.6px |
| `region` | região AWS | tracejado escuro |
| `account` | conta AWS (isolamento) | tracejado cinza |
| `zone` | agrupamento lógico dentro da conta | fundo `var(--zona)` |
| `ext` | sistema externo ou fora de controle | borda `var(--risco)` sobre `var(--risco-fundo)` |

## Caixas de conteúdo

| Classe | Uso | Anatomia |
|---|---|---|
| `.node` | serviço AWS protagonista | `<img src="aws://…">` 44px + `.nl` (nome) + `.ns` (papel) |
| `.svc` | serviço AWS compacto (linha) | ícone 24px à esquerda + `.ot` + `.os`; definir `width`/`height` |
| `.oss` | componente open source plugável | como `.svc`, ícone 28px, com selo `.tag` na cor de acento |
| `.chip` | conceito sem ícone (tópico, contrato, política) | texto centrado; `.chip.red` para risco/negativa |
| `.bchip` | referência a outro bloco da arquitetura | `.bn` (número) + `.bt` (título) + `.bs` (relação) |
| `.badge` | numeração do passo sobre o desenho | quadrado preto 20px com o número |
| `.elabel` | rótulo de aresta | texto pequeno cinza posicionado junto à seta |

## Setas

Um único `<svg class="edges">` cobre o canvas (`viewBox` = dimensões do canvas). Regras:

- Sempre ortogonais: `path` com segmentos `M`/`H`/`V` (nunca diagonais nem curvas).
- `style="stroke:var(--apoio)" stroke-width="1.6"` com `marker-end` (definir o `<marker>` em `<defs>`, com `style="fill:var(--apoio)"` na ponta). Atributo SVG `stroke` ou `fill` não aceita `var()`; por isso a cor vai em `style`.
- A ponta encosta na caixa de destino e o início sai da caixa de origem. O lint valida isso com tolerância de 6px; entre 6 e 60px o `--fix` corrige sozinho.
- Fluxo secundário ou de retorno: `style="stroke:var(--cinza)"` ou `stroke-dasharray`.


## Badges e passos sobre o desenho

- O badge do passo **nasce com a seta**: o centro fica sobre a linha (tolerância de 6px no lint), e ele pode deslizar ao longo dos segmentos ortogonais pra não competir com o rótulo da seta ou com caixas vizinhas. Badge ao lado da linha ou solto no canvas reprova (`BADGE-SOLTO`).
- Escolher o segmento onde o badge não gera ambiguidade: quando duas setas correm próximas, cada badge fica no segmento que só pertence à sua seta.
- Conexões no mesmo box: fluxos que convergem podem somar o encontro num mesmo ponto, desde que a separação dos caminhos esteja clara até ali; fluxos de caminhos diferentes entram e saem por pontos espaçados da mesma caixa.

## Receita de coordenadas

Conta feita antes de escrever o fonte. Com ela o lint passa na primeira rodada.

**Caixa sólida de cada elemento** (é nela que a seta encosta):

| Elemento | Escrito como | Caixa sólida |
|---|---|---|
| `.node` | `left:L;top:T` (largura 110) | só o ícone: x de `L+33` a `L+77`, y de `T` a `T+44`; centro em `(L+55, T+22)` |
| `.svc`, `.oss`, `.chip`, `.bchip` | `left`, `top`, `width`, `height` | a caixa inteira |

O nome (`.nl`) e o papel (`.ns`) de um `.node` ficam embaixo do ícone, de `T+50` até uns `T+95`, numa faixa de 110px (`L` a `L+110`). Nenhuma seta passa por essa faixa.

**Setas entre nós:**

- Mesma linha: horizontal na altura do centro do ícone. De `A` para `B` à direita: `M(LA+77),(TA+22) H(LB+33)`.
- Para cima: sai do topo do ícone, `M(L+55),T V...`.
- Para baixo: nunca sai pela base do ícone (atravessaria o nome). Sai pela lateral, `M(L+77),(T+22) H(corredor)`, desce pelo corredor e entra na caixa de destino.
- Para um `.svc`: a ponta encosta na borda da caixa (`left`, `left+width`, `top` ou `top+height`).

**Corredores:** são os x livres entre as colunas da grade, a pelo menos 10px de qualquer caixa e de qualquer faixa de nome (`L` a `L+110`). Cada seta tem o seu x, a pelo menos 14px do x de outra seta que corre no mesmo trecho. O mesmo vale para os y das horizontais.

**Badge:** o centro fica no meio do segmento mais longo da própria seta. Num segmento de `(x1,y)` a `(x2,y)`, o badge é `left:((x1+x2)/2 - 10)px;top:(y - 10)px`. Num vertical de `(x,y1)` a `(x,y2)`, é `left:(x - 10)px;top:((y1+y2)/2 - 10)px`. O segmento precisa ter pelo menos 40px.

**Ordem de trabalho:**

1. Escreva o fonte com a conta acima.
2. Rode `poster_lint.py --fix`: ele encosta pontas a até 60px da caixa (para a frente ou recuando, se a seta passou da borda) e leva cada badge solto para a seta mais próxima. As linhas `FIXADO` dizem o que mudou.
3. Rode o `poster_lint.py` de novo, sem `--fix`. `SOLTA` diz a borda da caixa mais próxima; `SETA-SOBRE-TEXTO` diz a faixa de x ou de y que a seta precisa evitar. Corrija o fonte com esses números.
4. Repita o passo 3 até `total: 0`. Só então rode o `build.py`.

## Ícones AWS

Referência no HTML: `aws://categoria/arquivo.png`. O build embute em base64 a partir do acervo do pacote pip `diagrams` (`<site-packages>/resources/aws/`). Categorias mais usadas: `compute`, `database`, `network`, `analytics`, `integration`, `security`, `storage`, `ml`, `management`, `general`. Para achar o nome exato de um ícone:

```bash
python3 -c "import diagrams,os;print(os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)),'resources','aws'))"
ls <caminho>/database/ | grep -i aurora
```

O build falha com lista clara se um `aws://` não existir; corrigir o nome e rodar de novo.

## Paleta

A cor vem do tema, nunca de literal no fonte. Tokens: `--tinta` (texto principal), `--apoio` (texto de apoio e setas), `--cinza`, `--zona` (fundo de zona), `--papel`, `--acento` (cor de acento, nunca cor de texto), `--risco` sobre `--risco-fundo`. Os valores do tema estão em `temas/ai-diagrams.json`; o `:root` de `assets/estilo.css` os declara. Hexadecimal ou `rgb()` no fonte reprova com `COR-FORA-DO-TEMA`, inclusive em estilo local. Fontes: IBM Plex Sans (texto) e IBM Plex Mono (rótulos técnicos, caps com letter-spacing).

## Convenções de nome

| Padrão | O que é |
|---|---|
| `NN-nome.html` | poster do bloco NN |
| `NN.M-descritivo.html` | poster de detalhe (satélite do bloco NN) |
| `NN.M-descritivo-topologia.html` | topologia de aterrissagem AWS do detalhe |
| `NN-nome-N-parte.html` | bloco decomposto em partes |

Fonte em `_src/`, entregáveis (HTML self-contained + PNG) na pasta pai.
