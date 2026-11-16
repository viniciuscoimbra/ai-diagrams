-- Modelo lógico da fintech de exemplo: quatro schemas.
-- comum: referências gerais | cadastro: clientes | conta: contas e movimentos | cobranca: faturas e recebimentos.
-- Colunas de controle (criado_em, atualizado_em, versao_registro) seguem o padrão da plataforma.

CREATE SCHEMA comum;
CREATE SCHEMA cadastro;
CREATE SCHEMA conta;
CREATE SCHEMA cobranca;

-- ---------------------------------------------------------------- comum
CREATE TABLE comum.moedas (
  moeda_id      uuid PRIMARY KEY,
  codigo        char(3)      NOT NULL UNIQUE,   -- ISO 4217
  nome          varchar(60)  NOT NULL
);

CREATE TABLE comum.paises (
  pais_id       uuid PRIMARY KEY,
  codigo        char(2)      NOT NULL UNIQUE,   -- ISO 3166
  nome          varchar(80)  NOT NULL
);

CREATE TABLE comum.feriados (
  feriado_id    uuid PRIMARY KEY,
  data          date         NOT NULL UNIQUE,
  descricao     varchar(80)  NOT NULL
);

-- ---------------------------------------------------------------- cadastro
CREATE TABLE cadastro.situacoes_cliente (
  situacao_cliente_id uuid PRIMARY KEY,
  codigo        varchar(20)  NOT NULL UNIQUE    -- ativo, bloqueado, encerrado
);

CREATE TABLE cadastro.clientes (
  cliente_id    uuid PRIMARY KEY,
  documento     varchar(14)  NOT NULL UNIQUE,
  nome          varchar(120) NOT NULL,
  situacao_cliente_id uuid   NOT NULL REFERENCES cadastro.situacoes_cliente,
  criado_em     timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE cadastro.enderecos (
  endereco_id   uuid PRIMARY KEY,
  cliente_id    uuid         NOT NULL REFERENCES cadastro.clientes,
  pais_id       uuid         NOT NULL REFERENCES comum.paises,
  logradouro    varchar(160) NOT NULL,
  cep           varchar(9)   NOT NULL
);

-- ---------------------------------------------------------------- conta
CREATE TABLE conta.situacoes_conta (
  situacao_conta_id uuid PRIMARY KEY,
  codigo        varchar(20)  NOT NULL UNIQUE    -- aberta, bloqueada, encerrada
);

CREATE TABLE conta.contas (
  conta_id      uuid PRIMARY KEY,
  cliente_id    uuid         NOT NULL REFERENCES cadastro.clientes,
  numero        varchar(20)  NOT NULL UNIQUE,
  moeda_id      uuid         NOT NULL REFERENCES comum.moedas,
  situacao_conta_id uuid     NOT NULL REFERENCES conta.situacoes_conta,
  aberta_em     timestamptz  NOT NULL
);

CREATE TABLE conta.movimentos (
  movimento_id  uuid PRIMARY KEY,
  conta_id      uuid          NOT NULL REFERENCES conta.contas,
  valor         numeric(18,2) NOT NULL,
  ocorrido_em   timestamptz   NOT NULL
);

CREATE TABLE conta.outbox (
  outbox_id     uuid PRIMARY KEY,
  evento_id     uuid          NOT NULL UNIQUE,
  tipo_evento   varchar(80)   NOT NULL,
  payload       jsonb         NOT NULL
);

-- ---------------------------------------------------------------- cobranca
CREATE TABLE cobranca.situacoes_fatura (
  situacao_fatura_id uuid PRIMARY KEY,
  codigo        varchar(20)  NOT NULL UNIQUE    -- aberta, paga, vencida, cancelada
);

CREATE TABLE cobranca.meios_pagamento (
  meio_pagamento_id uuid PRIMARY KEY,
  codigo        varchar(20)  NOT NULL UNIQUE    -- boleto, pix, debito_conta
);

CREATE TABLE cobranca.faturas_cobranca (
  fatura_id     uuid PRIMARY KEY,
  numero        varchar(20)   NOT NULL UNIQUE,
  cliente_id    uuid          NOT NULL REFERENCES cadastro.clientes,
  conta_id      uuid          NOT NULL REFERENCES conta.contas,
  moeda_id      uuid          NOT NULL REFERENCES comum.moedas,
  situacao_fatura_id uuid     NOT NULL REFERENCES cobranca.situacoes_fatura,
  valor_total   numeric(18,2) NOT NULL,
  vencimento    date          NOT NULL,
  emitida_em    timestamptz   NOT NULL,
  criado_em     timestamptz   NOT NULL DEFAULT now(),
  atualizado_em timestamptz   NOT NULL DEFAULT now()
);

CREATE TABLE cobranca.itens_fatura (
  item_id       uuid PRIMARY KEY,
  fatura_id     uuid          NOT NULL REFERENCES cobranca.faturas_cobranca,
  descricao     varchar(140)  NOT NULL,
  quantidade    integer       NOT NULL,
  valor_unitario numeric(18,2) NOT NULL
);

CREATE TABLE cobranca.execucoes_cobranca (
  execucao_id   uuid PRIMARY KEY,
  data_referencia date        NOT NULL UNIQUE,
  situacao      varchar(20)   NOT NULL,
  iniciada_em   timestamptz   NOT NULL
);

-- fatura_id nullable: o pagamento pode chegar sem identificar a fatura e ser conciliado depois.
CREATE TABLE cobranca.pagamentos_recebidos (
  pagamento_recebido_id uuid PRIMARY KEY,
  fatura_id     uuid          REFERENCES cobranca.faturas_cobranca,
  conta_id      uuid          NOT NULL REFERENCES conta.contas,
  meio_pagamento_id uuid      NOT NULL REFERENCES cobranca.meios_pagamento,
  identificador_externo varchar(40) NOT NULL UNIQUE,
  valor         numeric(18,2) NOT NULL,
  recebido_em   timestamptz   NOT NULL
);

-- execucao_id nullable: tentativa manual não pertence a uma execução do lote.
-- pagamento_recebido_id nullable: só preenchido quando a tentativa resultou em pagamento.
CREATE TABLE cobranca.tentativas_cobranca (
  tentativa_id  uuid PRIMARY KEY,
  fatura_id     uuid          NOT NULL REFERENCES cobranca.faturas_cobranca,
  pagamento_recebido_id uuid  REFERENCES cobranca.pagamentos_recebidos,
  meio_pagamento_id uuid      NOT NULL REFERENCES cobranca.meios_pagamento,
  execucao_id   uuid          REFERENCES cobranca.execucoes_cobranca,
  numero_tentativa integer    NOT NULL,
  resultado     varchar(20)   NOT NULL,
  tentada_em    timestamptz   NOT NULL
);

CREATE TABLE cobranca.outbox (
  outbox_id     uuid PRIMARY KEY,
  evento_id     uuid          NOT NULL UNIQUE,
  agregado_id   uuid          NOT NULL,
  tipo_evento   varchar(80)   NOT NULL,
  payload       jsonb         NOT NULL
);
