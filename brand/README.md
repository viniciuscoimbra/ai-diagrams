# ai-diagrams · Brandkit v2

Abra `brandkit.html` diretamente no navegador. O guia contém as quatro seções, seletor Claro / Escuro, downloads, fontes e imagens embutidos. Funciona offline. A composição se adapta ao mobile.

## Direção

Documentos ganham vida. A marca representa a diversidade de diagramas e pôsteres com formas geométricas vivas e sobrepostas. O nome continua `ai-diagrams`, sempre em minúsculas. A interface ao redor usa preto, branco e cinza, com a mesma base e a mesma camada de tema do plyngo.

A paleta da identidade é independente do tema de diagramas instalado. Nenhum arquivo em `skills/` foi alterado. `tema-vivo.json` é somente uma proposta local, não instalada nem homologada pelo gate de diagramas.

## Três propostas de símbolo

As propostas aparecem lado a lado na seção 01 Assinatura, cada uma com amostras em 16, 32 e 64 px. No mobile, ficam em coluna.

| Proposta | Composição | Avaliação |
| --- | --- | --- |
| **Encontro, recomendada** | Haste retangular ciano, círculo coral da mesma altura e triângulo amarelo interno | A junção forma o D de diagrams, com lateral esquerda reta e bojo direito contínuo. É usada nas demais aplicações. |
| Mosaico | Quatro formas e quatro cores em uma grade | Reforça a variedade de pôsteres, com mais fragmentos e interseções em escala pequena. |
| Órbita | Círculo, meia-lua e quadrado | Mais movimento e curvas. A leitura circular tem menos presença de pôster que Encontro. |

Encontro foi escolhido pelo dono do produto com a condição de ler como D. No campo de 64 × 64, a haste vai de (4,4) a (32,60) e o círculo tem centro (32,32) e raio 28. Ambos têm 56 unidades de altura. O triângulo tem vértices (20,16), (48,32) e (20,48), inteiramente dentro do círculo: não há perna nem extensão para baixo ou à direita. A silhueta foi revista em 16, 32 e 64 px. A paleta e o cálculo multiply permanecem iguais; o amarelo interno aparece pelas cores resultantes da sobreposição.

As assinaturas usam Inter Semibold convertida em curvas. Área livre mínima: ¼ da largura do símbolo em cada lado. Símbolo a partir de 16 px; assinatura a partir de 160 px. Preserve proporções, cores e interseções. As versões em uma tinta usam contornos para manter as formas distinguíveis.

## Paleta e multiply

`paleta.json` contém os quatro tons, todos os seis pares, a tinta indicada e o contraste. Os mesmos dados alimentam o HTML.

| Cor | Hex | Texto | Contraste |
| --- | --- | --- | --- |
| Ciano | `#24C8F5` | `#171717` | 9,10:1 |
| Coral | `#FF5B59` | `#171717` | 5,88:1 |
| Amarelo | `#FFD23F` | `#171717` | 12,41:1 |
| Violeta | `#9868F5` | `#171717` | 4,81:1 |

| Par | Multiply | Texto | Contraste |
| --- | --- | --- | --- |
| Ciano + Coral | `#244756` | Branco | 9,95:1 |
| Ciano + Amarelo | `#24A53D` | Preto | 5,57:1 |
| Ciano + Violeta | `#1552EB` | Branco | 6,11:1 |
| Coral + Amarelo | `#FF4B16` | Preto | 5,35:1 |
| Coral + Violeta | `#982556` | Branco | 7,68:1 |
| Amarelo + Violeta | `#98563D` | Branco | 5,62:1 |

Preto significa `#171717`; branco, `#FFFFFF`. Todos esses pares de texto e fundo superam 4,5:1. Os rótulos do exemplo usam a tinta aprovada sobre as quatro cores. A cor também tem legenda textual; não comunica sozinha a estrutura.

Multiply usa os canais sRGB codificados: `round(A × B / 255)` por canal. Em cruzamentos de três ou quatro formas, o produto usa todos os canais e arredonda uma vez no final. As interseções são paths opacos recortados com `clipPath`, inclusive as triplas. Não há dependência de `mix-blend-mode`, filtro, transparência ou fonte externa. As cores se preservam no librsvg e em leitores SVG com recorte vetorial, inclusive sobre fundos escuros.

## Interface compartilhada

- Componentes reais `Button`, `Card`, `SectionHeader` e `Segmented`, de `@refy/ui 0.4.0`, a versão usada por plyngo e mimmu. React e ReactDOM 19.2.4. Nenhuma dependência adicionada ao ai-diagrams.
- O build lê o pacote instalado em `../plyngo/node_modules/@refy/ui`, a base `../plyngo/prototipo/ui/tokens.css` e a ponte `../plyngo/design-system/plyngo-tokens.css`. Só adapta os seletores ao escopo `.brandkit`. Não mantém uma cópia paralela do tema.
- Fontes da interface: Inter e JetBrains Mono, embutidas a partir dos arquivos usados pelo plyngo. Controles com raio de 8 px, cards com 12 px e alvos de 44 px no mobile vêm dessa ponte.
- Claro: superfícies `#FFFFFF` / `#FAFAFA`, texto `#171717`. Escuro: superfícies `#111111` / `#171717`, texto `#EDEDED`. Botões, links, seleção e foco são neutros. A cor viva aparece nos símbolos, nos espécimes da paleta e nas peças de diagrama.
- A versão 0.4.0 não tem `ThemeProvider` nem aceita uma marca arbitrária no `BrandLogo`. O guia usa o escopo de tokens do plyngo e as assinaturas SVG próprias; não recria componentes.

Referências consultadas: `../plyngo/qa/brandkit-v19-desktop.png`, capturas claras, escuras e mobile de `../plyngo/qa/aura-consistency/`, fontes do tema e as capturas v1 deste diretório.

## Arquivos

| Arquivo | Uso |
| --- | --- |
| `brandkit.html` | Guia autônomo com as quatro seções |
| `assets/proposta-{encontro,mosaico,orbita}.svg` | Três propostas de símbolo |
| `assets/logo-solid.svg`, `logo-solid-reverse.svg` | Encontro com nome preto ou branco |
| `assets/logo-mono-dark.svg`, `logo-mono-light.svg` | Assinaturas em uma tinta |
| `assets/symbol-*.svg` | Símbolo recomendado, colorido e em uma tinta |
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

O build faz bundle e renderização estática com os componentes reais. `check.py` verifica a estrutura, os recursos offline, os assets embutidos, as três propostas, a recomendação, os seis pares, os contrastes, os SVGs, as dimensões PNG e a preservação do tema instalado. Com Pillow, também compara o canal alfa dos favicons de 16, 32 e 64 px à silhueta esperada do D, detectando haste incompleta e formas que saem do bojo. O gerador confere XML, largura dos textos, multiply, contraste e alinhamento dos badges aos conectores.

Os vetores e os PNGs foram renderizados com librsvg, sem Chrome. A comparação visual usa contatos reduzidos das propostas, dos favicons e das aplicações. Isso permite revisar a geometria e as peças exportadas, mas não substitui a inspeção do HTML no navegador.

As capturas PNG da v1, os JPEGs v2 e seus relatórios foram preservados como histórico. Todos antecedem esta correção do Encontro e não validam o D atualizado; o hash em `capturas/status.json` identifica o HTML da captura anterior. Nenhuma tentativa de iniciar o Chrome foi feita nesta revisão. Interação, overflow e aparência do HTML atualizado em desktop/mobile ainda dependem da execução externa abaixo e da leitura das novas capturas.

## Regeneração

Para reconstruir o HTML e executar as verificações estáticas, com as instalações locais de plyngo e das fontes disponíveis e Python com Pillow:

```sh
node brand/src/build.mjs
python3 brand/src/check.py
```

Para reconstruir também os vetores e PNGs, use um Python com `fontTools`, Node e `rsvg-convert` instalado. O gerador lê as fontes locais de `../local-ui/src/assets/fonts/`. Não inicia navegador.

```sh
python3 brand/src/build-assets.py
node brand/src/build.mjs
python3 brand/src/check.py
```

Fora do sandbox, com Playwright de `../local-ui`, Sharp de `../plyngo` e Chrome disponível:

```sh
node brand/src/capture.mjs
```

O caminho padrão é o Google Chrome do macOS; `CHROME=/caminho/do/chrome` permite outro executável. O script testa temas por clique e teclado, recursos offline, geometria, as propostas lado a lado ou em coluna, tamanhos dos favicons e neutralidade da interface. Registra o SHA-256 do HTML e o resultado em `capturas/checks-v2.json`.

As novas imagens usam nomes `brandkit-v2-*.jpg`, qualidade 70, largura de até 1280 px e limite de 300 KB por imagem. Não sobrescrevem os PNGs históricos. O status após a captura continua com revisão visual pendente até as imagens serem examinadas.

Esta correção atualiza a assinatura e suas variantes, a proposta 01, os cabeçalhos, os favicons, o social preview SVG/PNG e o diagrama de exemplo. Mosaico e Órbita permanecem idênticos, assim como a paleta, a tipografia e a interface. Não houve commit nem push.
