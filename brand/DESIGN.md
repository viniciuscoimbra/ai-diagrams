# Design do brandkit v2

## Fontes de verdade

- Símbolos e peças: src/build-assets.py e assets/.
- Paleta e contrastes: paleta.json, gerado junto dos assets.
- Interface: @refy/ui 0.4.0 instalado no plyngo, prototipo/ui/tokens.css e design-system/plyngo-tokens.css do plyngo.
- Proposta de tema de diagramas: tema-vivo.json. O tema instalado em skills/ não muda.

## Direção

A pessoa consulta o guia ao lado do editor e verifica as peças também no telefone. Os modos claro e escuro preservam a hierarquia. O entorno é neutro; as cores pertencem às formas e ao conteúdo do diagrama. A energia vem da geometria, da paleta e da linguagem: “Documentos ganham vida.”

Quatro seções: 01 Assinatura, 02 Cor e tipografia, 03 Tom de voz, 04 Aplicações. Propostas lado a lado no desktop e em coluna abaixo de 760 px. O kit preserva os controles e superfícies do sistema compartilhado.

## Identidade

Encontro forma o D de diagrams: haste retangular ciano à esquerda e círculo coral com a mesma altura total, de y=4 a y=60. A haste ocupa x=4 a x=32; o círculo tem centro (32,32) e raio 28. O triângulo amarelo, com vértices (20,16), (48,32) e (20,48), fica inteiramente dentro do círculo. A silhueta tem lateral esquerda reta e bojo direito contínuo, sem perna. Mosaico usa quatro formas; Órbita combina círculo, meia-lua e quadrado. Todas ocupam um campo quadrado. Interseções opacas com multiply em sRGB, sem dependência de CSS blend. Os SVGs incluem paths e clipPaths nativos.

Ciano #24C8F5, Coral #FF5B59, Amarelo #FFD23F e Violeta #9868F5. Texto #171717 nas quatro cores; preto ou branco nos seis cruzamentos conforme paleta.json. Não colocar texto nas interseções do símbolo. Versões de uma tinta usam contornos.

Assinatura em Inter Semibold convertida em curvas. Nome sempre minúsculo. Área livre de ¼ da largura do símbolo. Símbolo mínimo de 16 px, assinatura mínima de 160 px.

## Interface

Button, Card, SectionHeader e Segmented de @refy/ui 0.4.0. React e ReactDOM 19.2.4. O build incorpora diretamente os dois arquivos de tokens do plyngo, adaptando somente seus seletores ao escopo do guia. Inter e JetBrains Mono do plyngo são embutidas. Não há preset refySiteTheme nem design system paralelo.

Claro: fundo #FAFAFA, superfície #FFFFFF, texto #171717, secundário #737373, borda #E5E5E5. Escuro: fundo #171717, superfície #111111, texto #EDEDED, secundário #A3A3A3, borda #333333. Botões, hover, seleção e foco neutros. Raios e alvos mobile vêm do tema compartilhado.

CSS local define composição, espaçamento e responsividade. A identidade colorida só entra em SVGs, PNGs e espécimes de cor. A assinatura SVG usa imagem direta porque o BrandLogo desta versão aceita somente as marcas internas do pacote.

## Entrega e verificação

HTML com SSR, hidratação React, CSS, três faces de fonte e assets embutidos. Social preview em SVG/PNG 1280 × 640. Favicons SVG/PNG 16, 32 e 64. Diagrama vetorial 1280 × 856. Exemplo visual sem alegação de execução do gate.

Build, verificações estáticas e renderização librsvg sem Chrome. Capturas v1 preservadas. capture.mjs preparado para validar o HTML v2 fora do sandbox a 1440 e 390 px, claro e escuro, gerando JPEGs de QA até 1280 px e 300 KB. Aprovação visual do HTML continua pendente.
