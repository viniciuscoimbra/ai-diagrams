# Máquina de estados

Em que situação uma coisa pode estar e que evento a muda de uma para outra. Estado é caixa, transição é seta com o evento escrito. Usa `assets/estilo-conceitual.css` e o gate `scripts/conceitual.py`.

Modelo: `modelos/10-maquina-estados/`, na pasta da skill.

## Quando usar

- ciclo de vida de uma entidade: pedido, pagamento, conta, contrato, chamado;
- status gravado em banco e a pergunta é "de onde para onde ele pode ir";
- regra de negócio que depende da situação ("só estorna se estiver Liquidada").

Se a pergunta é a ordem das chamadas entre sistemas, é sequência. Se é quem faz o quê entre times, é raias. Se é um processo com tarefas, gateways e eventos BPMN, é BPMN.

## Spec (`gerar_estados.py`)

As coordenadas vêm do elkjs (`estados/`, com licença e origem em `estados/vendor/`); o desenho é desta skill. Ninguém escreve pixel.

```json
{
  "titulo_pagina": "10 · Situação do Pix de saída",
  "cabecalho": ["ai-diagrams · <tema>", "10 · Máquina de estados"],
  "kicker": "Máquina de estados",
  "h1": "Pix de saída: situação da transferência",
  "sub": "uma a três frases: o que o desenho mostra e como ler",
  "inicial": "recebida",
  "estados": [
    {"id": "recebida", "nome": "Recebida", "desc": "o pedido chegou; nada foi debitado."},
    {"id": "analise", "nome": "Em análise", "sub": "antifraude", "desc": "aguarda o score."},
    {"id": "recusada", "nome": "Recusada", "final": true, "desc": "sem débito."}
  ],
  "transicoes": [
    {"de": "recebida", "para": "analise", "evento": "chave e limite ok", "acao": "chama o antifraude"},
    {"de": "analise", "para": "recusada", "evento": "score", "guarda": "≥ 0,8"},
    {"de": "analise", "para": "analise", "evento": "timeout", "guarda": "tentativa < 3"}
  ],
  "faixa": {"f1": "um fato do ciclo de vida", "f2": "o que ficou fora do desenho"},
  "rodape": ["ai-diagrams", "Máquina de estados · AAAA-MM"]
}
```

- `inicial`: id do primeiro estado. O ponto preto aponta para ele.
- `estados`: na ordem em que a vida da coisa costuma andar; o layout respeita essa ordem.
  - `nome` em uma linha, até umas 18 letras. Nome maior faz o gerador parar.
  - `sub`: detalhe curto embaixo do nome (quem decide, o que é gravado).
  - `desc`: frase da seção "Estados" abaixo do desenho. Escreva para quem não vai olhar o desenho.
  - `final: true`: borda dupla. Estado final não tem saída.
  - `estilo`: `foco` (o estado que importa) ou `fora` (situação de erro), opcional.
- `transicoes`:
  - `evento` é obrigatório: o fato que dispara a mudança. Trecho entre crases vira código.
  - `guarda`: condição sem colchetes; sai como `[condição]`.
  - `acao`: o que o sistema faz na mudança; sai como `/ ação`.
  - `de` igual a `para` desenha o laço (repetição no mesmo estado).
- `direcao`: `RIGHT` ou `DOWN`, opcional. Sem ela, o gerador tenta da esquerda para a direita e cai para cima-baixo se passar de 1320px.
- A seção "Notação" sai sozinha: ponto inicial, estado, estado final e formato do rótulo.

## O que o gerador confere antes de desenhar

Para com `ESTADOS REPROVOU <código>`:

- `SEM-INICIAL`: falta `inicial`, ou ele não está em `estados`;
- `DESCONHECIDO`: transição cita um id que não está em `estados`;
- `SEM-EVENTO`: transição sem `evento`;
- `SAI-DO-FINAL`: estado final com seta saindo;
- `INALCANCAVEL`: nenhum caminho do inicial chega ao estado;
- `SEM-SAIDA`: estado não final sem saída para outro estado (o laço não conta). Ou ele é final, ou falta a transição.

## Comandos

```bash
python3 <skill>/scripts/gerar_estados.py diagramas/_src/NN-nome.json
python3 <skill>/scripts/conceitual.py diagramas/_src/NN-nome.html
```

Precisa de `node` no PATH, como o DER. O gate de desenho é o do conceitual (lista em `references/raias.md`). Se reprovar, encurte o rótulo, divida a guarda ou mude a ordem dos estados no JSON. Não edite o HTML gerado: ele é refeito a cada rodada.

## Na leitura do PNG

- toda seta encosta nos dois estados e o rótulo fica colado na seta certa;
- os finais têm borda dupla e nenhum tem saída;
- o caminho feliz se lê de cima para baixo ou da esquerda para a direita sem voltar;
- a seção "Estados" explica cada situação sem precisar do desenho.
