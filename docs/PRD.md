# PRD — Sistema Atividros (V1.0)

> **Versão:** 2.0 (Escopo Consolidado)  
> **Responsável:** Product Management (PM Sênior)  
> **Status:** Aprovado para Discovery Técnico (Arquiteto, Designer e Tech Lead)  
> **Ambiente Atual:** Pré-lançamento (nenhum usuário em produção — liberdade total para remodelagem de banco e contratos).

---

## 1. Visão do Produto e Contexto

O **Atividros** é um sistema web responsivo de gestão interna para uma loja de quadros, molduras, vidros e espelhos. Seu foco na **V1.0** é digitalizar o balcão e a oficina, garantindo **orçamentos rápidos e precisos** e **controle real de estoque**, do primeiro contato com o cliente até a entrega e quitação do pedido.

### Personas e Contexto de Uso
- **Operação:** 1 a 2 pessoas (balcão + oficina) usando o sistema simultaneamente.
- **Dispositivos:** Computador no balcão (fluxo principal de atendimento/orçamento) e celular/tablet na oficina (consulta de medidas, atualização de produção e baixa de estoque).
- **Escopo de Loja:** Uso interno, loja única (sem multitenancy).

### Dores Prioritárias (JTBD — Jobs To Be Done)
1. **Orçamento ágil e sem erro:** *"Quando um cliente pede um quadro ou espelho sob medida no balcão/WhatsApp, quero calcular em segundos dimensões, perdas e preço exato e transformar isso em orçamento/pedido sem retrabalho."*
2. **Controle real de estoque:** *"Antes de prometer prazo e ao iniciar a produção, quero saber exatamente quantas barras de moldura e quantos m² de vidro/fundo tenho disponíveis para evitar rupturas."*

---

## 2. Recorte de Escopo — Matriz MoSCoW

| Prioridade | Itens |
|---|---|
| **Must Have (V1.0)** | Autenticação real e rotas protegidas; Gestão de Estoque (Molduras por barra, Vidros/Fundos em m² com conversor de chapas, Suplementos manuais); Tabelas de Preço (Vidro, Espelho, Fundo, Paspatour + área mínima); Calculadora Unificada com propagação de dimensões, perda 45°, área mínima e mão de obra; Integração Calculadora → Pedido + edição livre de preço com alerta não-bloqueante; Pedidos com 3 tipos de item (quadro sob medida, vidro/espelho avulso, item/serviço livre); Orçamento (`rascunho`) com data de validade; 3 Eixos de Status saneados; Financeiro completo (desconto, forma de pagamento, múltiplos lançamentos parciais); Baixa de estoque assistida na produção (alerta sem bloqueio); 1 PDF único completo (Orçamento/OS); Clientes com histórico; Dashboard operacional confiável. |
| **Won't Have na V1.0 (Backlog V1.1+)** | Integração automática/botão WhatsApp; Emissão fiscal (NF-e / NFC-e); Múltiplos perfis de permissão (RBAC complexo); Relatórios financeiros avançados / fluxo de caixa / contas a pagar; Controle de retalhos / otimização de plano de corte de chapas. |

---

## 3. Módulos e Regras de Negócio (V1.0)

### 3.1 Autenticação e Segurança
- Login funcional com usuário e senha reais via formulário (remover credenciais hardcoded do frontend).
- Token JWT com expiração configurável.
- **Todas** as rotas da API (exceto login e healthcheck) devem exigir autenticação — incluindo leitura de estoque e tabelas de preço.
- **Proibido** logar senhas ou tokens em texto plano.
- CORS configurável via variável de ambiente.

---

### 3.2 Estoque e Tabelas de Preço

#### A. Molduras (Controle por Barra)
- Campos: `codigo` (único), `cor`, `marca` (opcional), `tamanho_barra` (metros), `largura_barra` (cm), `preco_custo` (R$/m ou por barra — padronizar com Arquiteto), `preco_venda` (R$/m), `quantidade` (barras inteiras em estoque), `estoque_minimo` (para alerta no dashboard).

#### B. Chapas — Vidros e Fundos (Controle por m²)
- O saldo em estoque é armazenado em **m² totais disponíveis** (`area_disponivel_m2`, Decimal).
- **Conversor automático na entrada:** Ao registrar entrada de novas chapas, o usuário informa `quantidade_chapas`, `largura_chapa (cm)` e `altura_chapa (cm)` e o sistema calcula e soma automaticamente `(qtd × largura × altura) / 10000` ao saldo em m².
- Também permite ajuste manual direto em m² (inventário/correção).
- **Vidros:** `tipo` (`incolor`, `antireflexo`, `espelho`, `outro`), `espessura (mm)`, `cor` (opcional), `area_disponivel_m2`, `estoque_minimo_m2`.
- **Fundos:** `tipo` (ex: MDF, Eucatex, Foam Board), `espessura (mm)`, `cor` (opcional), `area_disponivel_m2`, `estoque_minimo_m2`.

#### C. Suplementos (Controle Manual)
- Itens como Cola, Grampos, Fita, Massa de acabamento, Penduradores, Parafusos, Embalagem.
- Controle **100% manual** (entrada/saída avulsa no módulo de estoque), sem baixa automática nos pedidos.

#### D. Tabelas de Preço (Gerenciáveis no Frontend e Backend)
Entidades editáveis pelo usuário diretamente na interface:
1. **Tabela de Vidros e Espelhos** (`incolor`, `antireflexo`, `espelho`, `outro`): `preco_por_m2`, `area_minima_m2` (ex: `0.25` m²), `descricao`.
2. **Tabela de Fundos** (por tipo): `preco_por_m2`, `descricao`.
3. **Tabela de Paspatour**: `preco_por_m2`, `descricao`.

---

### 3.3 Calculadora de Quadros (Motor Único no Backend)

Toda a lógica de dimensões e precificação reside **exclusivamente no backend** (unificar e eliminar o endpoint legado `/calculadora/simular` com preços hardcoded).

#### Entradas
- Dimensões da obra: `altura (cm)` e `largura (cm)`
- `quantidade` (inteiro ≥ 1)
- `paspatour`: boolean + `tamanho_paspatour (cm)` (se ativo)
- `molduras`: lista ordenada (0, 1 ou N molduras selecionadas do estoque, da interna para a externa)
- `vidro_tipo`: opcional (`incolor`, `antireflexo`, `espelho`, `outro` ou nenhum)
- `fundo_tipo` / `fundo_id`: opcional
- `mao_de_obra`: Decimal opcional (R$ por unidade ou fixo — definir padrão de UX com Designer)

#### Regras de Cálculo de Dimensões (Propagação de Dentro para Fora)
1. **Obra:** `altura_obra × largura_obra`
2. **Vidro / Paspatour:**
   - Se tem Paspatour: `altura_vidro = altura_obra + 2 × tamanho_paspatour` e `largura_vidro = largura_obra + 2 × tamanho_paspatour`
   - Sem Paspatour: `altura_vidro = altura_obra`, `largura_vidro = largura_obra`
3. **Molduras (da interna para a externa):**
   - Para cada moldura `N` com largura de barra `L_N`:
     - `altura_N = altura_(N-1) + 2 × L_N`
     - `largura_N = largura_(N-1) + 2 × L_N`
4. **Quadro Final:** dimensões da moldura mais externa (ou do vidro/obra se sem moldura).

#### Regras de Cálculo de Preço e Consumo
- **Moldura (com perda de corte em 45°):**
  - `perimetro_seco_m = 2 × (altura_N + largura_N) / 100`
  - `perda_45_m = (8 × largura_barra_N) / 100` *(4 cantos em esquadria)*
  - `metragem_total_m = perimetro_seco_m + perda_45_m`
  - `subtotal_moldura_N = metragem_total_m × preco_venda_moldura_N`
  - `barras_sugeridas_N = ceil((metragem_total_m × quantidade) / tamanho_barra_N)` *(usado na baixa de estoque)*
- **Vidro / Espelho (com área mínima):**
  - `area_real_m2 = (altura_vidro × largura_vidro) / 10000`
  - `area_cobrada_m2 = max(area_real_m2, area_minima_m2)` *(ex: 0,25 m²)*
  - `subtotal_vidro = area_cobrada_m2 × preco_m2_vidro`
  - *(Nota: a baixa de estoque usa `area_real_m2 × quantidade`, enquanto o preço usa `area_cobrada_m2`.)*
- **Paspatour:**
  - `subtotal_paspatour = area_real_m2 × preco_m2_paspatour`
- **Fundo:**
  - `area_fundo_m2 = (altura_vidro × largura_vidro) / 10000` *(acompanha a medida interna da moldura/vidro)*
  - `subtotal_fundo = area_fundo_m2 × preco_m2_fundo`
- **Mão de Obra:** somada ao total quando informada.

#### Integração com Pedido e Liberdade de Preço
- A partir do resultado da calculadora, o usuário clica em **"Adicionar ao Pedido"** (novo ou em edição), levando automaticamente a descrição detalhada, dimensões, composição (múltiplas molduras, paspatour, vidro, fundo) e preço sugerido.
- O usuário pode **sobrescrever livremente** qualquer preço unitário ou total antes de salvar.
- **Alerta não-bloqueante:** se `total_final < total_sugerido`, o sistema exibe um alerta visual amarelo interno (ex: *"Valor abaixo do sugerido pela calculadora: R$ X"*), permitindo salvar normalmente. O `total_sugerido` nunca é exibido no PDF do cliente.

---

### 3.4 Pedidos, Orçamentos e Itens

#### Mix de Itens no Pedido
Um pedido pode conter 1 ou mais itens de qualquer um dos 3 tipos:
1. **Quadro sob medida** (gerado pela Calculadora — suporta múltiplas molduras, paspatour, vidro, fundo, mão de obra e snapshot das medidas de corte).
2. **Vidro / Espelho avulso** (corte sob medida por largura × altura, usando tabela de m² + área mínima).
3. **Item / Serviço livre** (descrição livre, quantidade e preço unitário — ex: quadro pronto, troca de vidro, instalação).

#### Campos do Pedido
- `numero_pedido`: sequencial e imutável, **persistido no banco** (ex: `202600001`), nunca em memória.
- `cliente_id`: obrigatório.
- `data_validade_orcamento`: data de validade quando o pedido está em `rascunho` (padrão configurável, ex: +7 dias).
- `prazo_entrega`: data prevista de entrega.
- `endereco_entrega`: opcional.
- `frete`: Decimal (default `0.00`), **sempre somado ao `valor_total`**.
- `desconto_valor` / `desconto_tipo` (`valor` ou `percentual`): opcional, **subtraído do `valor_total`**.
- Totais calculados exclusivamente no backend:
  - `subtotal_itens = soma(item.subtotal)`
  - `valor_total = max(0, subtotal_itens + frete - desconto_calculado)`
  - `valor_pago = soma(pagamentos válidos)`
  - `saldo_devedor = max(0, valor_total - valor_pago)`

#### Modelo de Status — 3 Eixos Independentes (Saneado)

1. **Eixo 1 — Status Geral (Ciclo de vida):**
   - `rascunho` (Orçamento) → `confirmado` → `entregue` → `arquivado`
   - `rascunho` ou `confirmado` → `cancelado` *(congela os eixos de Produção e Financeiro; se `valor_pago > 0`, alerta sobre necessidade de estorno)*.
2. **Eixo 2 — Status de Produção (Oficina — sem `entregue` duplicado):**
   - `pendente` → `aguardando_material` ⇄ `na_fila` → `em_producao` → `embalando` → `pronto_entrega`
   - A oficina conclui seu trabalho em `pronto_entrega`. A entrega efetiva ao cliente é registrada no Eixo Geral (`entregue`).
3. **Eixo 3 — Status Financeiro (Derivado dos lançamentos de pagamento):**
   - `sem_pagamento` (`valor_pago == 0`)
   - `pagamento_parcial` (`0 < valor_pago < valor_total`)
   - `pago_total` (`valor_pago >= valor_total`)
   - `estornado` (quando estornado após cancelamento/devolução)

#### Financeiro Completo (Múltiplos Pagamentos)
- Entidade `PagamentoPedido` vinculada ao pedido:
  - `valor` (Decimal > 0)
  - `forma_pagamento` (`pix`, `cartao_credito`, `cartao_debito`, `dinheiro`, `outro`)
  - `data_pagamento` (DateTime)
  - `observacao` (opcional)
- Permite registrar sinal, parcelas intermediárias e quitação final.
- Ao registrar o primeiro pagamento em um pedido `rascunho`, o sistema pode confirmar automaticamente o pedido (`confirmado`), registrando evento na auditoria.

#### Baixa de Estoque (Transição para `em_producao`)
- Disparada explicitamente ao mover o pedido para `em_producao`, abrindo um **modal de confirmação**:
  - **Molduras:** sistema exibe a quantidade de barras sugerida (`ceil(metragem_total / tamanho_barra)`) e permite **ajuste manual** pelo operador antes de confirmar.
  - **Vidros / Fundos:** sistema exibe a área real em m² que será debitada do saldo em m².
- **Ruptura de estoque:** se o saldo atual for menor que a baixa, o sistema exibe um **alerta visual destacado**, mas **não bloqueia** a confirmação (estoque pode ficar negativo para posterior regularização).
- Toda baixa é registrada no `PedidoEvento` e nos logs do backend com detalhes de cada material debitado.

#### Auditoria (`PedidoEvento`)
- Toda transição de status, lançamento financeiro e baixa de estoque gera um registro imutável com timestamp UTC, formando a linha do tempo do pedido.

---

### 3.5 Clientes
- CRUD completo: `nome`, `sobrenome`, `telefone`, `email` (opcional), `endereco` (opcional), `cep` (opcional).
- Busca por nome, telefone ou e-mail.
- Histórico de pedidos consultado via endpoint filtrado no backend (`GET /clientes/{id}/pedidos` ou `GET /pedidos?cliente_id={id}`), evitando carregar todos os pedidos no navegador.

---

### 3.6 Documento PDF Único (Orçamento / Ordem de Serviço)
- **1 documento unificado** gerado sob demanda (`GET /pedidos/{id}/pdf`) que atende tanto o cliente quanto a oficina:
  - Cabeçalho da Atividros + Número do Pedido + Data de criação.
  - Se `rascunho`: título **ORÇAMENTO** + **Data de Validade**. Se `confirmado`/seguintes: título **PEDIDO / ORDEM DE SERVIÇO** + **Prazo de Entrega**.
  - Dados do cliente e endereço de entrega.
  - Tabela de itens com **descrição detalhada e medidas técnicas** (obra, paspatour, vidro, molduras e quadro final), quantidade, valor unitário e subtotal.
  - Resumo financeiro: subtotal, frete, desconto, **total**, histórico/total pago e **saldo devedor**.
  - Campo de observações e linha para **assinatura / conferência**.

---

### 3.7 Dashboard Operacional
- **Receita confirmada:** soma apenas pedidos `confirmado`, `entregue` e `arquivado` (exclui `rascunho` e `cancelado`).
- **A receber:** soma do `saldo_devedor` dos pedidos ativos.
- **Pedidos de hoje** e **Pedidos com prazo vencido / vencendo hoje**.
- **Alertas de estoque crítico:** molduras abaixo do mínimo de barras e vidros/fundos abaixo do mínimo de m² (incluindo saldos negativos).

---

## 4. Débitos Técnicos e Bugs do Código Atual (Mapeados para Saneamento)

Estes itens foram identificados na auditoria do MVP WIP e devem ser resolvidos durante a implementação da V1.0:
1. `NUMERO_COUNTER` em memória ([services/pedido.py](file:///c:/Marcel/atividros/backend/app/services/pedido.py)) → migrar para geração segura persistida no banco.
2. Frete ignorado no cálculo de `valor_total` → corrigir para `itens + frete - desconto`.
3. `ItemPedido` só suporta 1 moldura e sem paspatour → remodelar para composição completa + snapshot de cálculo.
4. Login hardcoded em [App.jsx](file:///c:/Marcel/atividros/frontend/src/App.jsx) → ligar aos inputs reais.
5. Senha logada em texto plano em [api/autenticacao.py](file:///c:/Marcel/atividros/backend/app/api/autenticacao.py) → remover imediatamente.
6. Rotas `GET` de estoque e tabelas de preço sem autenticação → proteger todas.
7. Motor de cálculo duplicado (`/calculadora/simular` vs `/calculadora/quadro`) → unificar.
8. Arquivos residuais no git (`backend/test_atividros.db`, `frontend/src/test.jsx`, `frontend/src/test2.jsx`) → remover e ajustar `.gitignore`.

---

## 5. Briefing de Handoff para o Time

### Para o Arquiteto
- Redesenhar o modelo de dados (`ItemPedido`, `ItemPedidoMoldura` ou composição JSON/relacional com snapshot de dimensões/preços, `PagamentoPedido`, `MovimentacaoEstoque` se aplicável, estoque de chapas em m² e `TabelaPrecoFundo`).
- Definir estratégia segura para numeração sequencial de pedidos (compatível com SQLite agora e PostgreSQL na produção).
- Formalizar `docs/ARQUITETURA.md` e ADRs das decisões-chave.

### Para o Designer (UX/UI)
- Definir o Design System (decisão entre manter CSS customizado ou adotar Tailwind + shadcn/ui) priorizando **legibilidade no balcão (PC) e na oficina (mobile/tablet)**.
- Desenhar o fluxo ultra-rápido **Calculadora → Adicionar ao Pedido → PDF**.
- Desenhar o modal de **Baixa de Estoque Assistida** (ajuste manual de barras + alerta de estoque negativo) e a visualização clara dos **3 eixos de status** no Kanban sem poluição visual.
- Desenhar o layout limpo do **PDF único** (Orçamento / OS).

### Para o Tech Lead
- Quebrar o trabalho em épicos/sprints a partir da arquitetura definida, priorizando primeiro o saneamento de segurança/bugs e a remodelagem do backend.
- Quebrar componentes monolíticos no frontend (ex: `Pedidos.jsx` com 939 linhas) em componentes reutilizáveis e camada de serviços limpa.
- Estruturar cobertura de testes automatizados (unitários na calculadora/perda 45°/área mínima + integração nos fluxos de pedido, pagamentos e baixa de estoque) e limpeza do repositório.
