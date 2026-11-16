# Prompt

```text
Faça o modelo C4 do sistema de cobrança descrito em examples/c4/billing.md,
com as visões de paisagem, contexto, contêineres, componentes da API,
a emissão de um boleto (visão dinâmica) e a implantação em produção.
Salve o modelo em examples/c4/output/_src/billing-c4.json e gere as visões.
Sem cliente no cabeçalho; versão V2 e rodapé padrão.
```

Arquivo de dados que acompanha: `billing.md`. O mesmo modelo em Structurizr DSL está em `billing.dsl`:

```bash
npx ai-diagrams import examples/c4/billing.dsl --out diagrams/billing --lang pt-BR
```
