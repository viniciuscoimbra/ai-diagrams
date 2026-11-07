# ai-diagrams · Brandkit v2

Abra `brandkit.html` diretamente no navegador. O guia contém as quatro seções, seletor Claro / Escuro, downloads, fontes e imagens embutidos. Funciona offline. A composição se adapta ao mobile.

## Direção

Documentos ganham vida. A marca representa a diversidade de diagramas e pôsteres com formas geométricas vivas e sobrepostas. O nome continua `ai-diagrams`, sempre em minúsculas. A interface ao redor usa preto, branco e cinza, com a base e a camada de tema compartilhadas.

A paleta da identidade é independente do tema de diagramas instalado. Nenhum arquivo em `skills/` foi alterado. `tema-vivo.json` é somente uma proposta local, não instalada nem homologada pelo gate de diagramas.

## Símbolo escolhido: Encontro

A seção 01 Assinatura mostra somente o Encontro, com amostras em 16, 32 e 64 px.

O Encontro combina a haste ciano à esquerda e o bojo coral à direita com um triângulo equilátero amarelo voltado para cima. A leitura pretendida é D com um A dentro.

No campo de 64 × 64, a haste vai de (4,4) a (32,60) e o círculo tem centro (32,32) e raio 28. Ambos têm 56 unidades de altura. O triângulo é equilátero e inteiramente inscrito no círculo, sem recuo: ponta em (32,4) e vértices da base em (32 − 14√3,46) e (32 + 14√3,46), serializados no SVG como (7.7513,46) e (56.2487,46). Os três vértices pertencem à circunferência, dentro da precisão de serialização; o lado mede 28√3, aproximadamente 48,4974 unidades. O eixo coincide com o diâmetro vertical x=32. O triângulo ocupa a camada superior em amarelo puro #FFE600, opaco, sem multiply sobre a haste ou o círculo. O multiply permanece somente entre haste e círculo, em #244756. Os favicons de 16, 32 e 64 px preservam essa geometria e essas camadas.

As assinaturas usam Inter Semibold convertida em curvas. Área livre mínima: ¼ da largura do símbolo em cada lado. Símbolo a partir de 16 px; assinatura a partir de 160 px. Preserve proporções, cores e interseções. As versões em uma tinta usam contornos para manter as formas distinguíveis.

## Paleta e multiply

`paleta.json` contém os quatro tons, todos os seis pares, a tinta indicada e o contraste. Os mesmos dados alimentam o HTML.

| Cor | Hex | Texto | Contraste |
| --- | --- | --- | --- |
| Ciano | `#24C8F5` | `#171717` | 9,10:1 |
| Coral | `#FF5B59` | `#171717` | 5,88:1 |
| Amarelo | `#FFE600` | `#171717` | 14,15:1 |
| Violeta | `#9868F5` | `#171717` | 4,81:1 |

| Par | Multiply | Texto | Contraste |
| --- | --- | --- | --- |
| Ciano + Coral | `#244756` | Branco | 9,95:1 |
| Ciano + Amarelo | `#24B400` | Preto | 6,49:1 |
| Ciano + Violeta | `#1552EB` | Branco | 6,11:1 |
| Coral + Amarelo | `#FF5200` | Preto | 5,51:1 |
| Coral + Violeta | `#982556` | Branco | 7,68:1 |
| Amarelo + Violeta | `#985E00` | Branco | 5,34:1 |

Preto significa `#171717`; branco, `#FFFFFF`. Todos esses pares de texto e fundo superam 4,5:1. Os rótulos do exemplo usam a tinta aprovada sobre as quatro cores. A cor também tem legenda textual; não comunica sozinha a estrutura.

Multiply usa os canais sRGB codificados: `round(A × B / 255)` por canal. Os seis pares são amostras da paleta para diagramas; no símbolo, somente haste e círculo usam multiply. O triângulo amarelo cobre ambos com sua cor pura. As interseções exportadas usam paths opacos recortados com `clipPath`. Não há dependência de `mix-blend-mode`, filtro, transparência ou fonte externa. As cores se preservam no librsvg e em leitores SVG com recorte vetorial, inclusive sobre fundos escuros.

## Interface compartilhada

- Componentes reais `Button`, `Card`, `SectionHeader` e `Segmented`, de `@refy/ui 0.4.0`. React e ReactDOM 19.2.4. Nenhuma dependência adicionada ao ai-diagrams.
- O build lê o pacote instalado em `../plyngo/node_modules/@refy/ui`, a base `../plyngo/prototipo/ui/tokens.css` e a ponte `../plyngo/design-system/plyngo-tokens.css`. Só adapta os seletores ao escopo `.brandkit`. Não mantém uma cópia paralela do tema.
- Fontes da interface: Inter e JetBrains Mono, embutidas a partir dos arquivos locais compartilhados. Controles com raio de 8 px, cards com 12 px e alvos de 44 px no mobile vêm dessa ponte.
- Claro: superfícies `#FFFFFF` / `#FAFAFA`, texto `#171717`. Escuro: superfícies `#111111` / `#171717`, texto `#EDEDED`. Botões, links, seleção e foco são neutros. A cor viva aparece nos símbolos, nos espécimes da paleta e nas peças de diagrama.
- A versão 0.4.0 não tem `ThemeProvider` nem aceita uma marca arbitrária no `BrandLogo`. O guia usa o escopo de tokens compartilhado e as assinaturas SVG próprias; não recria componentes.

Referências da interface: capturas locais nos modos claro, escuro e mobile, fontes do tema e as capturas v1 deste diretório.

## Arquivos

| Arquivo | Uso |
| --- | --- |
| `brandkit.html` | Guia autônomo com as quatro seções |
| `assets/proposta-encontro.svg` | Encontro, o símbolo escolhido |
| `assets/logo-solid.svg`, `logo-solid-reverse.svg` | Encontro com nome preto ou branco |
| `assets/logo-mono-dark.svg`, `logo-mono-light.svg` | Assinaturas em uma tinta |
| `assets/symbol-*.svg` | Encontro, colorido e em uma tinta |
| `assets/favicon.svg` | Favicon vetorial principal |
| `assets/favicon-{16,32,64}.{svg,png}` | Favicons nos três tamanhos |
| `assets/social-preview.{svg,png}` | Social preview, 1280 × 640 |
| `assets/exemplo-diagrama.svg` | Diagrama com a paleta proposta, 1280 × 856 |
| `paleta.json` | Cores, interseções e contrastes |
| `tema-vivo.json` | Proposta de tema, sem alteração do tema instalado |
| `src/` | Fontes, geração e verificações |
| `PRODUCT.md`, `DESIGN.md` | Contexto e decisões atualizados |
| `capturas/` | Histórico v1 e situação da validação v2 |
| `licenses/` | OFL das fontes, MIT do React e aviso da origem do pacote Refy |

## Verificações e limites

O build faz bundle e renderização estática com os componentes reais. `check.py` verifica a estrutura, os recursos offline, os assets embutidos, o Encontro como único símbolo, os seis pares, os contrastes, os SVGs, as dimensões PNG e a preservação do tema instalado. Com Pillow, também compara o canal alfa dos favicons de 16, 32 e 64 px à união esperada das formas, a interseção multiply de haste e círculo e o amarelo puro do triângulo, inclusive onde ele cobre ambas. A geometria confere a ponta em (32,4), a base em y=46, o eixo x=32, os três lados iguais e os três vértices sobre a circunferência dentro da precisão de serialização. O gerador confere XML, largura dos textos, multiply, contraste e alinhamento dos badges aos conectores.

Os vetores e os PNGs são renderizados com librsvg, sem Chrome. As verificações de geometria e das peças exportadas não substituem a inspeção do HTML no navegador.

As capturas PNG da v1, os JPEGs v2 e seus relatórios foram preservados como histórico. Todos antecedem este ajuste do Encontro e não validam o símbolo atualizado; o hash em `capturas/status.json` identifica o HTML da captura anterior. Nenhuma tentativa de iniciar o Chrome foi feita nesta revisão. Interação, overflow e aparência do HTML atualizado em desktop/mobile ainda dependem da execução externa abaixo e da leitura das novas capturas.

## Regeneração

Para reconstruir o HTML e executar as verificações estáticas, com as dependências locais disponíveis e Python com Pillow:

```sh
node brand/src/build.mjs
python3 brand/src/check.py
```

Para reconstruir também os vetores e PNGs, use um Python com `fontTools`, Node e `rsvg-convert` instalado. O gerador lê as fontes locais da pasta indicada em `BRAND_FONTS`. Não inicia navegador.

```sh
python3 brand/src/build-assets.py
node brand/src/build.mjs
python3 brand/src/check.py
```

Fora do sandbox, com Playwright no projeto indicado em `PLAYWRIGHT_FROM`, Sharp de `../plyngo` e Chrome disponível:

```sh
node brand/src/capture.mjs
```

O caminho padrão é o Chrome do macOS; `CHROME=/caminho/do/chrome` permite outro executável. O script testa temas por clique e teclado, recursos offline, geometria, a apresentação do Encontro, tamanhos dos favicons e neutralidade da interface. Registra o SHA-256 do HTML e o resultado em `capturas/checks-v2.json`.

As novas imagens usam nomes `brandkit-v2-*.jpg`, qualidade 70, largura de até 1280 px e limite de 300 KB por imagem. Não sobrescrevem os PNGs históricos. O status após a captura continua com revisão visual pendente até as imagens serem examinadas.

Este ajuste atualiza a assinatura e suas variantes, a seção Assinatura, os cabeçalhos, os favicons, o social preview SVG/PNG e o diagrama de exemplo com o triângulo inscrito no círculo, em amarelo `#FFE600` na camada superior. As versões em uma tinta preservam os mesmos vértices em contorno. O Encontro é o único símbolo do brandkit. Não houve commit nem push.
