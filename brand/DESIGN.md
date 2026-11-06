# Design do brandkit v2

## Fontes de verdade

- Símbolos e peças: src/build-assets.py e assets/.
- Paleta e contrastes: paleta.json, gerado junto dos assets.
- Interface: @refy/ui 0.4.0 e os arquivos compartilhados `../plyngo/prototipo/ui/tokens.css` e `../plyngo/design-system/plyngo-tokens.css`.
- Proposta de tema de diagramas: tema-vivo.json. O tema instalado em skills/ não muda.

## Direção

A pessoa consulta o guia ao lado do editor e verifica as peças também no telefone. Os modos claro e escuro preservam a hierarquia. O entorno é neutro; as cores pertencem às formas e ao conteúdo do diagrama. A energia vem da geometria, da paleta e da linguagem: “Documentos ganham vida.”

Quatro seções: 01 Assinatura, 02 Cor e tipografia, 03 Tom de voz, 04 Aplicações. A seção Assinatura mostra somente o Encontro, com amostras em 16, 32 e 64 px. O kit preserva os controles e superfícies do sistema compartilhado.

## Identidade

Encontro é o símbolo escolhido: D com um A dentro. A haste retangular ciano fica à esquerda e o círculo coral forma o bojo à direita; ambos têm altura de y=4 a y=60. A haste ocupa x=4 a x=32; o círculo tem centro (32,32) e raio 28. O triângulo amarelo aponta para cima e é equilátero, inscrito no círculo sem recuo: ponta em (32,4), base em (32 − 14√3,46) e (32 + 14√3,46), serializada como (7.7513,46) e (56.2487,46). Seu lado mede 28√3, aproximadamente 48,4974 unidades; o eixo coincide com o diâmetro vertical x=32 e os três vértices tocam a circunferência. O triângulo está na camada superior, opaco e sem multiply. Apenas a interseção entre haste e círculo usa multiply em sRGB, com resultado #244756. Os SVGs incluem paths e clipPaths nativos, sem dependência de CSS blend.

Ciano #24C8F5, Coral #FF5B59, Amarelo #FFE600 e Violeta #9868F5. O amarelo permanece puro sobre toda a área do triângulo. Os seis cruzamentos multiply continuam como amostras da paleta para diagramas, calculados nos canais sRGB codificados e arredondados uma vez no final. Texto #171717 nas quatro cores, com contraste 14,15:1 sobre o amarelo; preto ou branco nos seis cruzamentos conforme paleta.json, sempre acima de 4,5:1. Não colocar texto nas interseções do símbolo. Versões de uma tinta usam contornos com os mesmos vértices do triângulo inscrito.

Assinatura em Inter Semibold convertida em curvas. Nome sempre minúsculo. Área livre de ¼ da largura do símbolo. Símbolo mínimo de 16 px, assinatura mínima de 160 px.

## Interface

Button, Card, SectionHeader e Segmented de @refy/ui 0.4.0. React e ReactDOM 19.2.4. O build incorpora diretamente os dois arquivos de tokens compartilhados, adaptando somente seus seletores ao escopo do guia. Inter e JetBrains Mono são embutidas. Não há preset refySiteTheme nem design system paralelo.

Claro: fundo #FAFAFA, superfície #FFFFFF, texto #171717, secundário #737373, borda #E5E5E5. Escuro: fundo #171717, superfície #111111, texto #EDEDED, secundário #A3A3A3, borda #333333. Botões, hover, seleção e foco neutros. Raios e alvos mobile vêm do tema compartilhado.

CSS local define composição, espaçamento e responsividade. A identidade colorida só entra em SVGs, PNGs e espécimes de cor. A assinatura SVG usa imagem direta porque o BrandLogo desta versão aceita somente as marcas internas do pacote.

## Entrega e verificação

HTML com SSR, hidratação React, CSS, três faces de fonte e assets embutidos. Social preview em SVG/PNG 1280 × 640. Favicons SVG/PNG 16, 32 e 64. Diagrama vetorial 1280 × 856. Exemplo visual sem alegação de execução do gate.

Build, verificações estáticas e renderização librsvg sem Chrome. Os checks geométricos conferem o triângulo equilátero, ponta em (32,4), base em y=46, eixo x=32 e seus três vértices na circunferência; os favicons de 16, 32 e 64 px são comparados à união das formas, ao multiply entre haste e círculo e ao amarelo puro sobre ambos. Capturas v1 e v2 preservadas como histórico: antecedem este ajuste e não o validam. capture.mjs preparado para validar o HTML fora do sandbox a 1440 e 390 px, claro e escuro, gerando JPEGs de QA até 1280 px e 300 KB. Aprovação visual do HTML atualizado continua pendente.
