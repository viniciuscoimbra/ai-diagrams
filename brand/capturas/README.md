# Capturas da revisão v2

As quatro capturas PNG da versão v1 e seu `checks.json` estão preservados. O relatório v1 registra testes concluídos a 1440 × 1000 e 390 × 844, nos temas claro e escuro. Esses arquivos mostram a identidade anterior e não validam a revisão v2.

Os JPEGs v2 e seus relatórios existentes antecedem o ajuste do Encontro com triângulo inscrito no círculo e amarelo puro na camada superior. O hash em `status.json` identifica esse HTML anterior; essas capturas não validam o símbolo atualizado. Por pedido do dono do produto, o Chrome não foi iniciado nesta revisão dentro do sandbox. As novas capturas, a interação e a revisão visual do HTML atualizado ainda precisam ser conferidas fora dele.

Na raiz do repositório, em ambiente com Chrome disponível:

```sh
node brand/src/capture.mjs
```

O script reutiliza Playwright de `../local-ui` e Sharp de `../plyngo`, já instalados. A variável `CHROME` permite indicar outro executável do Chrome. Nenhum pacote adicional é necessário neste workspace.

Arquivos produzidos:

- `brandkit-v2-desktop-light.jpg` e `brandkit-v2-desktop-dark.jpg`: página completa, viewport de teste 1440 × 1000.
- `brandkit-v2-mobile-light.jpg` e `brandkit-v2-mobile-dark.jpg`: página completa, viewport de teste 390 × 844.
- `checks-v2.json`: erros de execução, pedidos de rede, geometria, cores computadas e dimensões das capturas, com SHA-256 do HTML testado.
- `status.json`: estado da execução atual, sem substituir o relatório v1.

Os JPEGs usam qualidade 70, largura máxima de 1280 px e redução adicional quando necessária para ficar em até 300 KB. A resolução da captura não altera a largura usada nas verificações de layout.

As verificações cobrem recursos offline, tema por clique e teclado, ordem das quatro seções, overflow, Encontro como único símbolo com amostras a 16/32/64 px, todos os pares multiply da paleta, favicons a 16/32/64 px e cores neutras nos elementos principais da interface e nos botões, inclusive hover e foco.

Uma execução bem-sucedida registra `captured_pending_visual_review`. Abra os quatro JPEGs para revisar texto, leitura dos símbolos, recortes, respiro e adaptação mobile. Os testes geométricos e o hash identificam evidências; não comprovam qualidade visual nem aprovação da marca.
