# Tabela de comparação

Página editorial com uma ou mais tabelas `table.comp`. Usa o mesmo `estilo.css` e o mesmo `build.py` dos posters. Sem canvas e sem setas: o lint isenta badges e passos porque o documento não tem `<svg class="edges">`.

Modelo: `modelos/05-tabela-comparacao/`, na pasta da skill.

## Anatomia

| Elemento | Classe | Conteúdo |
|---|---|---|
| Moldura | `.hdr`, `.kicker`, `h1`, `.sub`, `.foot` | igual ao poster; o `h1` nomeia o que se compara |
| Título de seção | `.sec` | uma por tabela, em caps |
| Tabela | `table.comp` | primeira linha com `th`; primeira coluna é o critério, em negrito |
| Linha de decisão | `tr.escolha` (CSS local do modelo) | a opção adotada e a condição para rever, numa célula com `colspan` |
| Nota | `.nota` (CSS local) | uma frase de leitura abaixo da tabela |

## Regras

- Critério na linha, opção na coluna. Até quatro opções por tabela; mais do que isso vira duas tabelas.
- Célula curta, sem ponto final, em registro técnico. Termo de mercado em inglês (shard, consumer group, replay).
- A última linha registra a escolha quando a tabela sustenta uma decisão. Comparação sem escolha não leva essa linha.
- Custo entra como forma (o que cobra) e nunca como valor inventado: número vem de medição ou calculadora.

## Largura: a tabela tem que caber

A página tem 1760px e o conteúdo, entre as margens, 1664px. A captura corta o que passar disso, e o gate reprova com `TRANSBORDA`.

- `table.comp` já vem com `width:100%` e `table-layout:fixed`: a largura das colunas sai da primeira linha (`th`), não do texto das células. Não troque para `table-layout:auto`.
- A primeira coluna (critério) tem 220px; as outras dividem o resto por igual. Para outra divisão, dê `width` aos `th` no `<style>` local, somando até 1664px. Por exemplo, critério e três opções: `table.comp th:first-child{width:220px}` e as três opções sem largura (1444px divididos por três).
- Nunca use `white-space:nowrap` em célula de texto: a célula quebra linha, a tabela não estica.
- Até quatro opções por tabela. Com mais, divida em duas tabelas ou declare uma página mais larga com `<meta name="largura" content="N">` no `<head>`; o build captura nessa largura.
- Célula longa quebra em muitas linhas: encurte o texto em vez de alargar a coluna.

## Comandos

```bash
python3 <skill>/scripts/build.py diagramas/_src/NN-comparacao.html
```

O build mede a altura da página sozinho. Olhe o PNG: célula quebrando em muitas linhas pede texto mais curto, não coluna mais larga.
