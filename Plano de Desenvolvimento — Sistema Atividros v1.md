

## Contexto do Projeto

O **Atividros** é um sistema de gestão interno para uma loja de quadros, molduras, vidros e espelhos. O objetivo é digitalizar o controle de estoque, pedidos e clientes em uma aplicação web responsiva, acessível via navegador desktop e mobile.

---

## Stack Tecnológica

### Backend

- **Linguagem**: Python (versão mais recente estável)
- **Gerenciador de dependências**: Poetry
- **Framework web**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Banco de dados**: SQLite (desenvolvimento) → PostgreSQL (produção futura)
- **Autenticação**: JWT com OAuth2PasswordBearer (FastAPI nativo)
- **Geração de PDF**: WeasyPrint ou ReportLab (Orçamento e Ordem de Serviço)
- **Logging**: `logging` padrão Python, nível DEBUG
- **Linters/Formatadores**: Ruff, Black, isort

### Frontend

- **Framework**: React (Vite como bundler)
- **Estilização**: Tailwind CSS
- **Componentes UI**: shadcn/ui
- **Gerenciamento de estado**: Zustand (leve e simples)
- **Chamadas HTTP**: Axios
- **Roteamento**: React Router v6

---

## Arquitetura Geral

```
atividros/
├── backend/
│   ├── app/
│   │   ├── api/             # Routers FastAPI (endpoints)
│   │   │   ├── estoque.py
│   │   │   ├── pedidos.py
│   │   │   ├── clientes.py
│   │   │   ├── calculadora.py
│   │   │   └── auth.py
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Schemas Pydantic (request/response)
│   │   ├── services/        # Regras de negócio
│   │   ├── db/              # Sessão e configuração do banco
│   │   ├── pdf/             # Geração de documentos PDF
│   │   └── main.py          # Entrypoint FastAPI
│   ├── tests/
│   ├── pyproject.toml
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes reutilizáveis
│   │   ├── pages/           # Páginas (Estoque, Pedidos, Clientes)
│   │   ├── services/        # Chamadas à API (Axios)
│   │   ├── store/           # Estado global (Zustand)
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Módulos e Funcionalidades

### 1. Autenticação

- Login com usuário e senha (admin único inicial)
- Token JWT com expiração configurável
- Proteção de todas as rotas autenticadas
- Tela de login responsiva no React

### 2. Estoque

#### 2.1 Molduras

|Campo|Tipo|Obrigatório|
|---|---|---|
|Código|String (único)|✅|
|Quantidade|Integer|✅|
|Preço de Venda|Decimal|✅|
|Preço de Custo|Decimal|✅|
|Cor|String|✅|
|Tamanho da Barra|Decimal (metros)|✅|
|Largura da Barra|Decimal (cm)|✅|
|Marca|String|❌|

#### 2.2 Vidros

|Campo|Tipo|Obrigatório|
|---|---|---|
|Espessura|Decimal (mm)|✅|
|Tipo|Enum: incolor, antireflexo, espelho, outro|✅|
|Quantidade|Integer|✅|
|Largura da Chapa|Decimal (cm)|✅|
|Altura da Chapa|Decimal (cm)|✅|
|Cor|String|❌|

#### 2.3 Fundo

|Campo|Tipo|Obrigatório|
|---|---|---|
|Tipo|String|✅|
|Espessura|Decimal (mm)|✅|
|Quantidade|Integer|✅|
|Largura|Decimal (cm)|✅|
|Altura|Decimal (cm)|✅|
|Cor|String|❌|

#### 2.4 Suplementos

Itens com controle de quantidade simples: Cola, Grampos, Fita, Massa de acabamento, Penduradores, Parafusos, Embalagem.

### 3. Pedidos

- Um pedido pode conter **um ou mais produtos** (quadro, moldura, espelho, etc.)
- Cada item do pedido possui: descrição, quantidade e valor unitário
- O sistema calcula o **valor total** automaticamente
- Campos financeiros do pedido: `valor_total`, `valor_sinal`, `saldo_devedor` (calculado)
- Campos opcionais: endereço de entrega, frete
- **Baixa no estoque**: ao mover para `em_producao`, o sistema exibe uma confirmação para o usuário e, após aprovação, dá baixa automática nos itens consumidos

#### 3.1 Modelo de Status — Dois Eixos Independentes

O pedido possui **três dimensões de estado** que evoluem em paralelo e são armazenadas separadamente no banco:

---

**Eixo 1 — Status Geral** (ciclo de vida do pedido)

|Status|Descrição|
|---|---|
|`rascunho`|Pedido criado mas ainda não confirmado ao cliente|
|`confirmado`|Pedido aceito, aguardando início do fluxo|
|`cancelado`|Cancelado em qualquer momento; congela os outros eixos|
|`entregue`|Produto entregue ao cliente; encerra o ciclo|
|`arquivado`|Pedido concluído e arquivado para histórico|

Transições permitidas:

```
rascunho → confirmado → entregue → arquivado
    ↓           ↓
 cancelado   cancelado
```

---

**Eixo 2 — Status de Produção** (fluxo linear da execução)

|Status|Descrição|
|---|---|
|`pendente_aprovacao`|Aguardando aprovação do cliente (ex: orçamento enviado)|
|`aguardando_material`|Aprovado, mas falta material em estoque|
|`na_fila`|Material disponível, aguardando vez na bancada|
|`em_producao`|Em execução na oficina|
|`embalando`|Produto pronto, sendo embalado|
|`pronto_para_entrega`|Embalado e aguardando retirada ou envio|

Transições permitidas (fluxo linear, sem retrocesso exceto por `aguardando_material`):

```
pendente_aprovacao → aguardando_material ⇄ na_fila → em_producao → embalando → pronto_para_entrega
                   ↘ na_fila (se material disponível)
```

> A baixa de estoque é disparada na transição `na_fila → em_producao`, com confirmação do usuário.

---

**Eixo 3 — Status Financeiro** (pode alternar livremente)

|Status|Descrição|
|---|---|
|`sem_pagamento`|Nenhum valor recebido ainda|
|`sinal_recebido`|Entrada/sinal pago parcialmente|
|`pago_total`|Valor total quitado|
|`estornado`|Pagamento devolvido (ex: cancelamento)|

Transições permitidas:

```
sem_pagamento → sinal_recebido → pago_total
     ↓               ↓               ↓
  estornado       estornado       estornado
```

---

#### 3.2 Tabela de Histórico de Eventos (`PedidoEvento`)

Cada mudança de status em qualquer eixo gera um registro imutável de auditoria:

|Campo|Tipo|Descrição|
|---|---|---|
|`id`|Integer|PK|
|`pedido_id`|FK|Referência ao pedido|
|`eixo`|Enum: `geral`, `producao`, `financeiro`|Qual eixo mudou|
|`status_anterior`|String|Estado antes da transição|
|`status_novo`|String|Estado após a transição|
|`observacao`|String (opcional)|Motivo ou nota livre|
|`criado_em`|DateTime|Timestamp automático (UTC)|

Esse histórico serve como **linha do tempo completa do pedido** e alimenta o PDF da OS.

### 4. Clientes

- Cadastro com nome, sobrenome, telefone
- Endereço e CEP opcionais
- Histórico de pedidos vinculado automaticamente
- Busca por nome ou telefone

### 5. Calculadora de Quadro

Módulo dedicado ao cálculo de orçamento de um quadro, acessível tanto na criação de um pedido quanto de forma avulsa. Toda a lógica reside no backend (`services/calculadora.py`) e o frontend apenas exibe o formulário e o resultado.

#### 5.1 Entradas do Usuário

|Campo|Tipo|Obrigatório|Observação|
|---|---|---|---|
|Altura do quadro (obra)|Decimal (cm)|✅|Tamanho da imagem/obra original|
|Largura do quadro (obra)|Decimal (cm)|✅|Tamanho da imagem/obra original|
|Molduras|Lista ordenada|✅|Mínimo 1; cada item referencia um código do estoque|
|Paspatour|Boolean|✅|Se sim, solicita tamanho em cm|
|Tamanho do Paspatour|Decimal (cm)|❌|Obrigatório se `paspatour = true`|
|Tipo de vidro|Enum (da tabela fixa)|✅|Incolor, Antireflexo|

#### 5.2 Lógica de Cálculo de Dimensões

O cálculo propaga de dentro para fora, camada por camada:

```
Tamanho base (obra) = altura × largura informadas pelo usuário

Se tem Paspatour:
    altura_com_pasp  = altura_obra + (tamanho_pasp × 2)
    largura_com_pasp = largura_obra + (tamanho_pasp × 2)
    → esse é o tamanho do VIDRO e da MOLDURA INTERNA

Para cada moldura (da mais interna para a mais externa):
    altura_moldura_N  = altura_moldura_(N-1) + (largura_barra_moldura_N × 2)
    largura_moldura_N = largura_moldura_(N-1) + (largura_barra_moldura_N × 2)

Tamanho final do quadro = dimensões da moldura mais externa
```

**Exemplo com Paspatour + 2 molduras:**

```
Obra:          40 × 50 cm
Paspatour 5cm: 50 × 60 cm  ← tamanho do vidro + moldura interna (M1)
Moldura M1 (barra 3cm): 56 × 66 cm  ← tamanho para moldura externa (M2)
Moldura M2 (barra 4cm): 64 × 74 cm  ← tamanho final do quadro
```

#### 5.3 Lógica de Cálculo de Preço

**Molduras** — preço por metro linear do perímetro:

```
perímetro_moldura_N (m) = (altura_N + largura_N) × 2 / 100
custo_moldura_N = perímetro_moldura_N × preço_por_metro (do estoque, campo preço_venda)
```

**Vidro** — preço por m² (tabela fixa cadastrada no sistema):

```
área_vidro (m²) = (altura_com_pasp × largura_com_pasp) / 10000
custo_vidro = área_vidro × preço_m²_do_tipo_de_vidro
```

**Paspatour** — item com preço próprio na tabela fixa:

```
custo_paspatour = área_vidro × preço_m²_paspatour
```

> O paspatour é cobrado pela mesma área do vidro, pois ele cobre exatamente essa superfície.

**Total do quadro:**

```
total = soma(custo_moldura_N) + custo_vidro + custo_paspatour (se houver)
```

#### 5.4 Tabela de Preços Fixos de Vidro

Entidade separada no banco (`TabelaPrecoVidro`), editável pelo admin:

|Campo|Tipo|
|---|---|
|Tipo|Enum: incolor, antireflexo|
|Preço por m²|Decimal|
|Descrição|String (opcional)|

Tabela análoga para Paspatour (`TabelaPrecoPaspatour`):

|Campo|Tipo|
|---|---|
|Descrição|String|
|Preço por m²|Decimal|

#### 5.5 Saída do Cálculo (Response da API)

Os valores retornados pela calculadora são **sugestões editáveis**. O frontend deve permitir que o usuário sobrescreva qualquer valor de preço antes de adicionar ao pedido.

```json
{
  "dimensoes": {
    "obra": { "altura": 40, "largura": 50 },
    "vidro": { "altura": 50, "largura": 60 },
    "molduras": [
      { "codigo": "M01", "altura": 56, "largura": 66 },
      { "codigo": "M02", "altura": 64, "largura": 74 }
    ],
    "quadro_final": { "altura": 64, "largura": 74 }
  },
  "custos": {
    "molduras": [
      { "codigo": "M01", "perimetro_m": 2.44, "preco_metro_sugerido": 12.50, "preco_metro_final": 12.50, "subtotal": 30.50 },
      { "codigo": "M02", "perimetro_m": 2.76, "preco_metro_sugerido": 18.00, "preco_metro_final": 18.00, "subtotal": 49.68 }
    ],
    "vidro": { "tipo": "antireflexo", "area_m2": 0.30, "preco_m2_sugerido": 85.00, "preco_m2_final": 85.00, "subtotal": 25.50 },
    "paspatour": { "area_m2": 0.30, "preco_m2_sugerido": 40.00, "preco_m2_final": 40.00, "subtotal": 12.00 },
    "total_sugerido": 117.68,
    "total_final": 117.68
  }
}
```

> `_sugerido` = valor calculado pelas tabelas de preço. `_final` = valor efetivamente cobrado (editável pelo usuário). O backend armazena `total_sugerido` apenas para disparar o alerta de valor abaixo — nunca é exibido ao cliente.

```

#### 5.6 Endpoint

```

POST /calculadora/quadro → Recebe os parâmetros do quadro → Retorna dimensões calculadas + breakdown de custos

GET /calculadora/tabela-vidro PUT /calculadora/tabela-vidro/{id}

GET /calculadora/tabela-paspatour PUT /calculadora/tabela-paspatour/{id}

```

#### 5.7 Integração com Pedido

O resultado da calculadora pode ser **aproveitado diretamente na criação de um pedido**: o usuário calcula o quadro, revisa o breakdown de custos e clica em "Adicionar ao Pedido", que pré-preenche um item com a descrição e o valor total calculado.

---

### 6. Geração de PDF
Dois documentos gerados sob demanda a partir de um pedido:

**Orçamento PDF**
- Logo/cabeçalho da loja
- Dados do cliente
- Tabela de itens com valores
- Valor total + frete
- Prazo de entrega
- Rodapé com validade do orçamento

**Ordem de Serviço (OS)**
- Número da OS
- Dados do cliente
- Descrição detalhada dos produtos/serviços
- Status atual
- Data de entrada e prazo de entrega
- Campo para assinatura (impressão)

---

## Regras de Negócio Importantes

1. **Baixa de estoque**: Só ocorre após confirmação explícita do usuário na transição `na_fila → em_producao`. O sistema registra no log quais itens foram baixados, em qual quantidade e por qual pedido.
2. **Cancelamento**: Pode ocorrer em qualquer status geral. Ao cancelar, os eixos de produção e financeiro são congelados (não aceitam mais transições). Se houver `sinal_recebido`, o sistema alerta sobre necessidade de estorno.
3. **Número do pedido**: Gerado automaticamente de forma sequencial e imutável após criação.
4. **Número do cliente**: Gerado automaticamente e vinculado ao histórico de pedidos.
5. **Valor total**: Calculado no backend (soma dos itens + frete), nunca confiado ao frontend.
6. **Validação de estoque**: Ao confirmar a baixa, o sistema verifica se há quantidade suficiente e alerta o usuário caso não haja, sem bloquear o pedido.
7. **Histórico de eventos**: Toda transição de status em qualquer eixo gera um `PedidoEvento` imutável com timestamp UTC. Nunca se deleta ou edita um evento.
8. **Pagamento parcial**: O pedido possui campos dedicados `valor_sinal` (Decimal) e `valor_total`. O sistema calcula automaticamente `saldo_devedor = valor_total - valor_sinal` quando o status financeiro for `sinal_recebido`. Ao atingir `pago_total`, o saldo é zerado.
9. **Calculadora de quadro**: Todo o cálculo de dimensões e preços ocorre **exclusivamente no backend**. O frontend envia os parâmetros e exibe o resultado — nunca calcula localmente.
10. **Propagação de dimensões**: As dimensões se propagam sempre de dentro para fora — obra → paspatour → moldura interna → moldura(s) externa(s). Qualquer alteração num nível recalcula todos os níveis seguintes.
11. **Liberdade de preço no pedido**: A calculadora fornece valores sugeridos, mas o usuário pode sobrescrever livremente o valor final do pedido, o preço por metro de qualquer moldura e o preço por m² do vidro e do paspatour. O valor editado substitui diretamente o calculado — sem trava ou confirmação extra.
12. **Alerta de valor abaixo do calculado**: Se o valor final informado pelo usuário for **menor** que o valor sugerido pela calculadora, o sistema exibe um alerta visual não-bloqueante (ex: banner amarelo "Valor abaixo do calculado: R$ X"). O pedido pode ser salvo normalmente. O valor calculado original é guardado internamente apenas para gerar esse alerta — não aparece no PDF nem no histórico do cliente.

---

## Endpoints REST (Esboço)

```

POST /auth/login GET /auth/me

GET /estoque/molduras POST /estoque/molduras PUT /estoque/molduras/{id} DELETE /estoque/molduras/{id}

# (mesmo padrão para /vidros, /fundos, /suplementos)

GET /clientes POST /clientes GET /clientes/{id} PUT /clientes/{id}

GET /pedidos POST /pedidos GET /pedidos/{id} PUT /pedidos/{id} PATCH /pedidos/{id}/status/geral # Transição no eixo geral PATCH /pedidos/{id}/status/producao # Transição no eixo produção PATCH /pedidos/{id}/status/financeiro # Transição no eixo financeiro POST /pedidos/{id}/baixa-estoque # Confirmação de baixa (na_fila → em_producao) GET /pedidos/{id}/eventos # Histórico completo de eventos GET /pedidos/{id}/pdf/orcamento GET /pedidos/{id}/pdf/os

```

---

## Padrões de Código (Backend)

- **Paradigma**: Funcional por padrão; `dataclasses` e classes apenas onde necessário
- **Docstrings**: Obrigatórias em todas as funções e módulos
- **Logging**: Nível DEBUG durante desenvolvimento; todas as ações críticas (criação, edição, baixa de estoque, geração de PDF) devem ser logadas
- **Tratamento de erros**: HTTPException com mensagens claras em português
- **Variáveis de ambiente**: Gerenciadas via `.env` + `pydantic-settings`

---

## Etapas de Desenvolvimento Sugeridas

### Fase 1 — Base do Backend
1. Setup do projeto com Poetry
2. Configuração do SQLAlchemy + SQLite + migrations (Alembic)
3. Modelos de banco: Moldura, Vidro, Fundo, Suplemento, Cliente, Pedido, ItemPedido, **PedidoEvento**
4. Autenticação JWT
5. CRUD completo de Estoque e Clientes

### Fase 2 — Pedidos e Regras de Negócio
1. CRUD de Pedidos com itens
2. Máquina de estados para os três eixos (geral, produção, financeiro) com validação de transições permitidas
3. Registro automático de `PedidoEvento` a cada transição
4. Lógica de baixa de estoque com confirmação
5. Lógica de cancelamento com alerta de estorno financeiro
6. Cálculo automático de totais

### Fase 2.5 — Calculadora de Quadro
1. Modelos `TabelaPrecoVidro` e `TabelaPrecoPaspatour` no banco
2. Service `calculadora.py` com funções puras de cálculo de dimensões e preços
3. Endpoint `POST /calculadora/quadro`
4. Endpoints de leitura/edição das tabelas de preço
5. Testes unitários do motor de cálculo (casos: só moldura, com paspatour, múltiplas molduras)
6. Integração "Adicionar ao Pedido" a partir do resultado da calculadora

### Fase 3 — Geração de PDF
1. Template de Orçamento
2. Template de Ordem de Serviço
3. Endpoint de download

### Fase 4 — Frontend React
1. Setup com Vite + Tailwind + shadcn/ui
2. Tela de login
3. Dashboard com resumo (pedidos do dia, estoque crítico)
4. CRUD de Estoque (todas as categorias)
5. CRUD de Clientes com histórico
6. **Calculadora de quadro** — formulário com preview em tempo real das dimensões calculadas e breakdown de custos
7. Gestão de Pedidos com kanban de status de produção — cada card exibe os três eixos simultaneamente: badge de produção (cor por etapa), badge financeiro (sinal/pago/pendente) e badge geral (ativo/cancelado/entregue). Ao clicar no card abre o painel de detalhe.
8. Painel lateral do pedido com linha do tempo de eventos (`PedidoEvento`)
9. Controles independentes para eixo financeiro (sinal / pago total) e eixo geral (cancelar / entregar)
10. Botão de geração e download de PDF

### Fase 5 — Qualidade e Entrega
1. Testes automatizados (pytest) nos serviços críticos
2. Aplicação de Ruff, Black e isort
3. Revisão de logs e tratamento de exceções
4. Documentação do README
5. Build de produção

---

## Observações Finais

- O banco começa em **SQLite** para simplicidade. A migração futura para PostgreSQL deve ser transparente via SQLAlchemy, bastando trocar a string de conexão.
- O frontend React com Vite + Tailwind é responsivo por padrão, cobrindo desktop e mobile.
- shadcn/ui oferece componentes acessíveis e bem documentados, ideais para quem está aprendendo React.
- O sistema foi projetado para **uma loja, uso interno**, sem multitenancy — simplificando bastante a autenticação e o modelo de dados.
```