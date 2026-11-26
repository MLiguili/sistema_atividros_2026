# Plano de Implementação — Sistema Atividros (V1.0)

> **Versão:** 1.0  
> **Status:** Plano Executivo Aprovado para Execução Imediata (Pós-Planejamento)  
> **Base Funcional:** `docs/PRD.md` (v2.0)  
> **Baseline Arquitetural:** `docs/ARQUITETURA.md` (v1.0)  
> **Baseline Visual e UX:** `docs/DESIGN_SYSTEM.md` (v1.0)  
> **Referência Metodológica:** `C:\FluxeScripts\Fluxe\fluxeOS` (`ROADMAP.md` e `SCOPE_MATRIX.md`, adaptados com filtros de escopo R4)

---

## 1. Sumário Executivo e Premissas de Entrega

### 1.1 Objetivo do Plano
Este documento consolida o plano executável de engenharia para evoluir o MVP WIP atualmente presente em `c:\Marcel\atividros` até a versão **Atividros V1.0**, eliminando todos os débitos críticos de segurança e regras de negócio mapeados no `docs/PRD.md` (§4), implementando a remodelagem de banco e contratos REST de `docs/ARQUITETURA.md`, e aplicando o Design System modular e a refatoração de componentes especificados em `docs/DESIGN_SYSTEM.md`.

### 1.2 Premissas de Entrega e Fronteiras de Escopo (V1.0)
- **Pronto para execução imediata:** O `PRD.md` v2.0, `ARQUITETURA.md` v1.0 e `DESIGN_SYSTEM.md` v1.0 já estão consolidados e o código atual foi auditado por completo; a implementação inicia diretamente na **Sprint 0 / Épico 1**, sem gates artificiais de descoberta pendentes.
- **Ambiente Pré-Lançamento:** Não há usuários em produção nem dados reais de clientes a preservar (`PRD.md`, cabeçalho), o que permite consolidar o schema V1.0 do banco de dados de forma limpa e corrigir contratos REST/enums legados sem camadas de compatibilidade desnecessárias.
- **Operação Loja Única:** Sistema web responsivo interno (FastAPI + SQLAlchemy 2.0 Async + React 19 + Vite) para **1 a 2 usuários simultâneos** no **Balcão (Desktop `>= 1024 px`)** e na **Oficina (Celular/Tablet `320–1023 px`)**, persistindo em SQLite (desenvolvimento/piloto) com portabilidade nativa para PostgreSQL (produção).
- **Fora de Escopo V1.0 (`Won't Have` e Filtros R4):** Não fazem parte deste plano shell desktop nativo (Tauri/Electron), pipelines de IA/LLM/áudio/RAG, multi-tenancy, RBAC complexo, exportação PPTX/DOCX (apenas **1 PDF Único**), integração automática WhatsApp, NF-e/NFC-e, fluxo de caixa contábil ou plano de corte/retalhos de chapas.

---

## 2. Rastreabilidade de Débitos Técnicos (`PRD.md` §4) e Achados Extras

### 2.1 Tabela Mestra dos 8 Débitos Técnicos Críticos (`PRD.md` §4)

| # | Débito Técnico (`PRD.md` §4) | Evidência Exata no Repositório Atual | Épico / Sprint | Solução Canônica (`ARQUITETURA` / `DESIGN_SYSTEM`) | Critério Objetivo de Encerramento |
|---|---|---|---|---|---|
| **D1** | `NUMERO_COUNTER` em memória RAM | `backend/app/services/pedido.py:39-46` (`{"valor": 1}`, ano fixo `2026`, colide após restart) | **Épico 2** (Sprint 1) | `ADR-005`: tabela `sequencia_numeracao` com `INSERT ... ON CONFLICT DO UPDATE RETURNING` (+ `BEGIN IMMEDIATE` no SQLite) | Teste de integração criando pedidos concorrentes e simulando reinício de engine sem colisão (`YYYYNNNNN` monotônico) |
| **D2** | Frete ignorado no cálculo de `valor_total` | `backend/app/services/pedido.py:153-154`, `api/pedidos.py:100-101` e `Pedidos.jsx:624-739` | **Épico 4** (Sprint 3) | `ARQUITETURA §4.1`: `valor_total = max(0, subtotal_itens + frete - desconto_calculado)` calculado apenas no backend | Testes unitários e de integração validando `subtotal_itens + frete - desconto` em `POST`/`PUT /pedidos/` |
| **D3** | `ItemPedido` só suporta 1 moldura e sem paspatour | `backend/app/models/pedido.py:60-81`, `schemas/pedido.py:9-27` | **Épico 2** (Sprint 1) | `ADR-004`: `ItemPedido` multi-tipo (`quadro_sob_medida`, `vidro_avulso`, `servico_livre`), `snapshot_calculo` JSON e filha `ItemPedidoMoldura` (`0..N`) | Migração aplicada (`alembic upgrade head`) + persistência de pedido com 2+ molduras, paspatour e snapshot imutável |
| **D4** | Login hardcoded em `App.jsx` | `frontend/src/App.jsx:16,27,31` (`login('admin', 'admin123')` ignorando inputs) | **Épico 1** (Sprint 0) | `DESIGN_SYSTEM §5.1`: extração de `pages/Login.jsx` com estado controlado, erro inline e interceptor `401` | Teste Vitest/RTL digitando credenciais reais, falhando em `401` e autenticando sem credencial fixa |
| **D5** | Senha logada em texto plano | `backend/app/api/autenticacao.py:22` (`dados_form.password` passado a `logger.debug`) | **Épico 1** (Sprint 0) | `ADR-006` e `ARQUITETURA §7.1`: remoção imediata do argumento de senha e regra de zero log de credenciais/tokens | Inspeção de código + teste `caplog` em nível `DEBUG` garantindo ausência da senha/JWT nos logs do login |
| **D6** | Rotas `GET` de estoque e tabelas sem auth | `backend/app/api/estoque.py:39,82,87,128,133,174` e `api/calculadora.py:55,84` | **Épico 1** (Sprint 0) | `ARQUITETURA §6.1`: `Depends(obter_usuario_atual)` em 100% das rotas exceto `GET /` e `POST /autenticacao/entrar` | Testes automatizados validando HTTP `401` sem token em todos os `GET` de estoque e tabelas de preço |
| **D7** | Motor de cálculo duplicado | `api/calculadora.py:23-51`, `services/calculadora.py:19-159`, `services/pedido.py:61-110` (preço vidro `100.0` / fundo `30.0` hardcoded) | **Épico 3** (Sprint 2) | `ADR-007`: motor único em `services/calculadora.py` (`POST /calculadora/quadro` e `/vidro-avulso`); remover `/calculadora/`, `/simular` e `obter_detalhes_calculo` | Endpoints legados retornando `404`; `Pedidos` e `Calculadora` consumindo o mesmo motor determinístico (`Decimal`) |
| **D8** | Arquivos residuais rastreados no git e `.gitignore` falho | `backend/test_atividros.db`, `frontend/src/test*.jsx`, `.idea/`, docs raiz legados, `.gitignore:210` bloqueando migration | **Épico 1** (Sprint 0) | Limpeza controlada via `git rm`, remoção da linha 210 de `.gitignore` e bloqueio global de `*.db` / `.idea/` | `git status` e `git ls-files` limpos de residuais; todas as migrations Alembic versionadas |

### 2.2 Tabela de Achados Extras Identificados na Auditoria do Repositório

| ID | Achado Extra Verificado | Localização Real | Épico / Sprint | Resolução Planejada |
|---|---|---|---|---|
| **E1** | Script `create_admin.py` quebrado (imports pré-PT-BR `app.models.user`, `app.services.auth`, `DATABASE_URL`) e senha hardcoded `"admin123"` | `backend/scripts/create_admin.py:4-6,27` | **Épico 1** (Sprint 0) | Atualizar imports para `app.models.usuario`, `app.services.autenticacao`, `settings.database_url` e ler `ADMIN_INITIAL_PASSWORD` / `getpass`. |
| **E2** | `migrations/env.py` omite modelos `TabelaPreco*`, lê URL fixa de `alembic.ini` e não usa `render_as_batch=True` | `backend/migrations/env.py:10-15,43,56` | **Épico 2** (Sprint 1) | Importar todos os 5 módulos de models, injetar `settings.database_url` e habilitar `render_as_batch=True`. |
| **E3** | CORS aberto (`allow_origins=["*"]` + `allow_credentials=True`) e `chave_secreta` insegura sem bloqueio fora de `debug` | `backend/app/main.py:24-30`, `app/config.py:6-9` | **Épico 1** (Sprint 0) | Adicionar `cors_origins` em `Settings` (`.env`) e validar `chave_secreta` no `lifespan` quando `debug=False`. |
| **E4** | `pyproject.toml` sem driver PostgreSQL (`asyncpg`) e com `passlib[bcrypt]` divergente de `pbkdf2_sha256` | `backend/pyproject.toml:18` | **Épico 1** e **2** | Trocar `passlib[bcrypt]` por `passlib` (`ADR-006`) na Sprint 0 e adicionar `asyncpg ^0.30.0` no Épico 2. |
| **E5** | Enums divergentes (`para_embalar`, `entregue` na produção, `sinal_recebido`), `baixa-estoque` bloqueante com HTTP 400 e hardcode `pendente`, cancelamento sem estorno de `pago_total` e `gerador_pdf.py` incompleto | `backend/app/models/pedido.py`, `services/pedido.py:15-37,176-323`, `services/gerador_pdf.py:44-92` | **Épico 2** e **4** | Enums saneados (Épico 2); máquina 3 eixos, `PagamentoPedido`, Baixa Assistida não-bloqueante e PDF Único A4 (Épico 4). |
| **E6** | Interceptor `401` em `api/config.js` não redireciona para `/login`; `vite.config.js` tem `allowedHosts` ngrok hardcoded | `frontend/src/api/config.js:18-26`, `frontend/vite.config.js` | **Épico 1** (Sprint 0) | Limpar `token_atividros`, zerar contexto e redirecionar para `/login?sessao=expirada`; ler `VITE_ALLOWED_HOSTS` via env. |
| **E7** | Container `.container` duplicado em `App.jsx` + `Layout.jsx`, ausência de rota `*` e ausência da rota `/precos` | `frontend/src/App.jsx:44,51-60`, `components/Layout.jsx:65` | **Épico 5** (Sprint 4) | Remover `.container` de `RotaProtegida`, adicionar `<Route path="/precos">` e fallback `*` (`DD-009`). |
| **E8** | Tokens CSS quebrados (`--card-bg`, `--warning`), contraste `2,54:1` em `.btn-primary`, `<style>` inline em 5 `.jsx`, `src/styles/` vazio e `window.alert`/`confirm` nativos | `index.css`, `Layout.jsx`, `Clientes.jsx`, `Estoque.jsx`, `Calculadora.jsx`, `Pedidos.jsx` | **Épico 5** (Sprints 4–5) | Criar `src/styles/` (`tokens.css`, `base.css`, `layout.css`, `components.css`, `pages/*.css`) e primitivos `src/components/ui/*` (`DD-001`..`DD-010`). |
| **E9** | `Dashboard.jsx` soma `rascunho`/`cancelado` na receita e usa alertas hardcoded (`< 5` / `< 3`) | `frontend/src/pages/Dashboard.jsx:21,40-42` | **Épico 4** + **5** | Endpoint `GET /dashboard/resumo` (Épico 4) e atualização de `Dashboard.jsx` usando `StatCard` (Épico 5). |
| **E10** | `Clientes.jsx` baixa `GET /pedidos/` inteiro para filtrar histórico no navegador | `frontend/src/pages/Clientes.jsx:82-83` | **Épico 3** + **5** | `GET /clientes/{id}/pedidos` + `?q=` no backend (Épico 3) e consumo direto em `ModalHistoricoCliente.jsx` (Épico 5). |
| **E11** | Ausência total de infraestrutura de testes no frontend (`package.json` sem Vitest/RTL) | `frontend/package.json` | **Épico 5** (Sprint 4) | Configurar `vitest`, `@testing-library/react`, `@testing-library/user-event` e `jsdom` com scripts `test` e `test:cov`. |
| **E12** | `AtualizarCliente` não normaliza strings vazias (`empty_str_to_none`) como `BaseCliente` | `backend/app/schemas/cliente.py:14-30` | **Épico 3** (Sprint 2) | Aplicar validador compartilhado em `email`, `endereco` e `cep` no schema `AtualizarCliente`. |

---

## 3. Visão Geral dos Épicos, Sprints e Gates de Saída Verificáveis

Seguindo o modelo de gestão orientada a **outcomes e gates verificáveis** (`fluxeOS/docs/product/ROADMAP.md` §2), nenhum épico pode ser declarado concluído apenas por *merge* de código: cada marco exige evidência real de testes executados e artefatos validados.

| Épico / Sprint | Objetivo Principal | Requisitos (`PRD`) & Débitos | Gate de Saída e Evidência Real Exigida | Dependência |
|---|---|---|---|---|
| **Épico 1 / Sprint 0**<br>*Fundação, Limpeza e Saneamento de Segurança* | Limpar residuais do git/disco, fechar falhas críticas de segurança no backend/frontend e estabilizar autenticação real | `PRD §3.1`, **D4, D5, D6, D8**, **E1, E3, E4 (parcial), E6** | `git status` sem residuais; `pytest` passando com testes de `401` em todas as rotas `GET` de estoque/tabelas e zero senha no log `DEBUG`; `create_admin.py` funcional; login real funcionando no browser sem `admin123` hardcoded + `npm run build` verde. | Nenhuma (Início imediato) |
| **Épico 2 / Sprint 1**<br>*Remodelagem de Dados, Alembic Dual-Engine e Sequência* | Corrigir `migrations/env.py`, habilitar portabilidade PostgreSQL (`asyncpg`) e consolidar schema V1.0 + `SequenciaNumeracao` atômica | `PRD §3.2, §3.4`, `ADR-001..005, ADR-008`, **D1, D3**, **E2, E4, E5 (enums)** | `alembic upgrade head` executado com sucesso em banco SQLite limpo; revisão de DDL compatível com PostgreSQL; teste de integração gerando `numero_pedido` concorrente sem colisão após reinício de engine; `pytest` verde. | Épico 1 (Sprint 0) |
| **Épico 3 / Sprint 2**<br>*Motor Único de Cálculo, Estoque `m²` e Tabelas de Preço* | Unificar calculadora no backend (eliminando `/simular`), implementar entrada/ajuste `m²`, CRUD de 3 tabelas de preço e busca/histórico de clientes | `PRD §3.2, §3.3, §3.5`, `ADR-001..003, ADR-007`, **D7**, **E10 (backend), E12** | Endpoints legados `/calculadora/` e `/calculadora/simular` removidos (`404`); testes unitários `Decimal` cobrindo propagação, perda 45°, área mínima, fundo pela medida do vidro e `mao_de_obra` R$/un; testes de integração de chapas `m²`, 3 tabelas de preço e `GET /clientes/{id}/pedidos`. | Épico 2 (Sprint 1) |
| **Épico 4 / Sprint 3**<br>*Pedidos, 3 Eixos, Pagamentos, Baixa Assistida e PDF Único* | Implementar ciclo completo de pedidos multi-item, financeiro multi-pagamento, Baixa Assistida não-bloqueante, `/dashboard/resumo` e PDF Único A4 | `PRD §3.4, §3.6, §3.7`, `ADR-004, ADR-008, ADR-009`, **D2**, **E5, E9 (backend)** | Testes de integração cobrindo `frete` + `desconto`, `abaixo_do_sugerido`, 3 eixos sem `entregue` na produção, `PagamentoPedido` + confirmação automática + estorno, Baixa Assistida com ajuste manual e saldo negativo (`200 OK`), imutabilidade de snapshot e conteúdo do PDF (`ORÇAMENTO` vs `PEDIDO / ORDEM DE SERVIÇO` sem `valor_sugerido`). | Épico 3 (Sprint 2) |
| **Épico 5 / Sprints 4–5**<br>*Design System CSS, Primitivos UI e Refatoração do Frontend* | Implementar `src/styles/` (`tokens.css`..`pages/*.css`), primitivos `ui/`, setup Vitest/RTL, decompor `Pedidos.jsx` (939 L) e atualizar todas as páginas para Balcão + Oficina | `PRD §3.2–§3.7`, `DD-001..DD-010`, **E7, E8, E9, E10, E11** | Zero tags `<style>` inline e zero hex literal nos `.jsx`; `vitest run` passando nos fluxos críticos (Login+401, Calculadora→Pedido, alerta amarelo, Baixa Assistida, Kanban 6 colunas); `npm run lint` e `npm run build` sem erros; revisão visual desktop (`1280px`) e mobile (`375px`/`320px`). | Épico 1 (Sprint 0) para base CSS/UI;<br>Épicos 3–4 para integração final |
| **Épico 6 / Sprint 6**<br>*Hardening E2E, Portabilidade PostgreSQL e Aceite V1.0* | Validar jornada ponta a ponta Balcão + Oficina, validar execução real contra PostgreSQL (`asyncpg`), auditoria WCAG 2.2 AA e fechamento de cobertura | Todos os `PRD §3`, `ARQUITETURA §7.4`, `DESIGN_SYSTEM §8` | Suíte completa `pytest --cov=app` (`>= 80%`) + `ruff check` + `vitest run` + `eslint` + `vite build` executados no estado final; validação de `alembic upgrade head` e smoke E2E em PostgreSQL; checklist WCAG 2.2 AA verificado sem bloqueios. | Épico 4 + Épico 5 |

---

## 4. Critérios Horizontais de Qualidade (DoD Global)

Aplicáveis a **100% dos épicos e pull requests** antes de avançar para o gate seguinte (adaptado de `fluxeOS/ROADMAP.md` §2.2 para o domínio Atividros):

1. **Evidência Real Obrigatória:** É proibido declarar qualquer tarefa ou épico como concluído sem registro da execução bem-sucedida dos comandos de verificação (`pytest`, `ruff check`, `vitest run`, `npm run lint`, `npm run build` ou `alembic upgrade head`), com zero mocks enganosos nos fluxos de integração.
2. **Consistência Contratual Cruzada:** Nomes de campos, enums (`status_geral`, `status_producao`, `status_financeiro`, `tipo_item`, `forma_pagamento`), rotas REST e rótulos de interface devem obedecer integralmente a `ARQUITETURA.md` e `DESIGN_SYSTEM.md`.
3. **Zero Vazamento de Segredos:** Nenhuma senha em texto plano, hash, token JWT, `Authorization` header ou `chave_secreta` pode aparecer em logs (`INFO`/`DEBUG`), respostas de erro HTTP 500 ou commits.
4. **Integridade Matemática e Monetária:** No backend, todo cálculo de moeda, metragem e `m²` usa `decimal.Decimal` com `ROUND_HALF_UP` (nunca `float`); no frontend, exibições monetárias e dimensionais usam `tabular-nums` (`.at-num`) e formatação `pt-BR`.
5. **Higiene de Código, CSS e Docstrings:** Funções e classes documentadas com *docstrings* em PT-BR; no frontend, proibição estrita de `<style>` inline, `window.alert`/`confirm`, cores hex literais fora de `tokens.css` e tokens quebrados (`--card-bg`, `--warning`).
6. **Não-Regressão:** A atualização de contratos e testes legados só é permitida quando explicitamente motivada por mudança aprovada no `PRD.md` v2.0 (ex.: remoção de `400` na ruptura de estoque), devendo ser documentada na revisão.

---

## 5. Caminho Crítico e Paralelismo Permitido

O **Caminho Crítico** da V1.0 passa pela cadeia sequencial:  
`Sprint 0 (Segurança + Limpeza)` → `Épico 2 (Modelos + Migrations + Sequência)` → `Épico 3 (Calculadora + Chapas m² + Preços)` → `Épico 4 (Pedidos + Baixa + Pagamentos + PDF)` → `Épico 5 (Integração Pedidos/Kanban/Baixa)` → `Épico 6 (Hardening E2E + Aceite)`.

Contudo, diversas frentes de frontend e infraestrutura são **isoláveis** e podem avançar em paralelo após a Sprint 0:

| Frente de Trabalho | Pode Iniciar em Paralelo Com | Bloqueia / Não Pode Declarar Concluído Sem |
|---|---|---|
| **A. Design System CSS (`src/styles/*`) e Primitivos UI (`src/components/ui/*`)** | **Épico 2 e Épico 3** (logo após Sprint 0) | Setup do `Vitest + RTL` e validação visual de contraste/teclado dos primitivos (`Dialog`, `ConfirmDialog`, `StatusBadge`, `Callout`, `DataTable`, `Tabs`). |
| **B. Setup Vitest/RTL + `Layout.jsx` + `Dashboard` UI base** | **Épico 2 e Épico 3** | Contrato real de `GET /dashboard/resumo` (Épico 4) e remoção do container duplicado em `App.jsx` (`DD-009`). |
| **C. Refatoração de `Clientes.jsx` e `TabelasPreco.jsx`** | **Épico 4** (assim que Épico 3 entregar `/clientes/{id}/pedidos` e CRUD das 3 tabelas) | Testes RTL de busca/histórico filtrado no servidor e CRUD de `Vidro`, `Fundo` (`area_minima_m2`) e `Paspatour`. |
| **D. Refatoração de `Estoque.jsx` e `Calculadora.jsx`** | **Épico 4** (assim que Épico 3 entregar `entrada-chapas`, `ajuste-m2` e `POST /calculadora/*`) | Testes RTL do conversor `m²`, auxiliar de custo/barra (`DD-004`) e `mao_de_obra` R$/un (`DD-003`). |
| **E. Decomposição de `Pedidos.jsx` (939 L) e Fluxo Calculadora→Pedido** | **Final do Épico 4** (estrutura visual dos 8 subcomponentes pode iniciar durante Épico 4 usando tipos/contratos de `ARQUITETURA.md §6.3`) | Integração real com endpoints de `Pedidos`, `PagamentoPedido`, `previsao-baixa`, `baixa-estoque`, `GET /pdf` e suíte E2E do Épico 6. |
| **F. Provisionamento / Teste PostgreSQL (`asyncpg`)** | **Épico 3 e Épico 4** (após Épico 2 fechar `migrations/env.py` e models) | Execução limpa de `alembic upgrade head` + bateria completa `pytest` contra instância PostgreSQL no Épico 6. |

---

## 6. Detalhamento Executável por Épico e Sprint

### Épico 1 / Sprint 0 — Fundação, Limpeza do Repositório e Saneamento Crítico de Segurança

**Objetivo:** Eliminar arquivos residuais rastreados no git, corrigir o `.gitignore`, fechar imediatamente todas as vulnerabilidades de segurança (credenciais hardcoded, senha em log, rotas `GET` abertas, CORS irrestrito) e restaurar o script administrativo.

#### Tarefas Técnicas
1. **Limpeza do Repositório e `.gitignore` (Débito D8):**
   - Executar o plano exato descrito na **Seção 8** deste documento (`git rm` dos residuais rastreados, remoção da linha 210 de `.gitignore`, inclusão de `*.db`, `*.sqlite*`, `.idea/`, `frontend/dist/`).
   - Limpar caches e bancos locais não rastreados (`backend/atividros.db`, `htmlcov/`, `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `frontend/dist/`).
2. **Sanitização de Logs e Alinhamento de Hash (`ADR-006`, Débito D5, Achado E4):**
   - Em `backend/app/api/autenticacao.py:22`: remover `dados_form.password` da chamada `logger.debug(...)`, deixando apenas `logger.debug("Tentativa de login para usuario: %s", dados_form.username)`.
   - Revisar `backend/app/api/` e `services/` para garantir que nenhum log imprima senha, `token_acesso` ou header `Authorization`.
   - Em `backend/pyproject.toml:18`: ajustar `passlib = {extras = ["bcrypt"], version = "^1.7.4"}` para `passlib = "^1.7.4"` (padronizado em `pbkdf2_sha256` conforme `ADR-006`), configurando `pbkdf2_sha256__default_rounds` explícito no `CryptContext` de `services/autenticacao.py`.
3. **Proteção de 100% das Rotas `GET` de Negócio (Débito D6):**
   - Em `backend/app/api/estoque.py`: adicionar `usuario_atual: Usuario = Depends(obter_usuario_atual)` em `listar_molduras` (L39), `listar_vidros` (L82), `obter_vidro` (L87), `listar_fundos` (L128), `obter_fundo` (L133) e `listar_suplementos` (L174).
   - Em `backend/app/api/calculadora.py`: adicionar `usuario_atual: Usuario = Depends(obter_usuario_atual)` em `listar_tabela_vidro` (L55) e `listar_tabela_paspatour` (L84).
   - **Atualização de Testes Legados na Sprint 0:** Atualizar `backend/tests/test_calculadora_extra.py:21-24,81-85` para enviar `headers=cabecalho_autorizacao` nos testes de sucesso e adicionar casos dedicados validando `401 Unauthorized` sem token em todos esses `GET`.
4. **Configuração Segura, CORS e Handler Global de Erro (Achado E3):**
   - Em `backend/app/config.py`: adicionar `cors_origins: list[str] = ["http://localhost:5173"]` (com parsing de CSV/JSON via `.env`) e `log_level: str = "INFO"`. Atualizar `backend/.env.example`.
   - Em `backend/app/main.py`: substituir `allow_origins=["*"]` por `settings.cors_origins`; implementar `lifespan` que aborta a inicialização com `RuntimeError` se `settings.debug is False` e (`settings.chave_secreta == "sua_chave_secreta_super_segura_aqui"` ou `len(settings.chave_secreta) < 32`); adicionar exception handler global HTTP 500 sanitizado (`{"detail": "Erro interno no servidor"}`).
5. **Correção do Script `backend/scripts/create_admin.py` (Achado E1):**
   - Substituir imports quebrados (`app.models.user`, `app.services.auth`, `DATABASE_URL`) por `app.models.usuario.Usuario`, `app.services.autenticacao.obter_hash_senha` e `app.config.settings.database_url`.
   - Ler senha de `os.getenv("ADMIN_INITIAL_PASSWORD")` ou `getpass.getpass(...)` (com fallback apenas se `settings.debug is True` e aviso explícito em console), sem logar a URL se contiver credenciais de PostgreSQL.
6. **Saneamento de Login e Sessão Expirada no Frontend (Débito D4, Achado E6):**
   - Extrair `Login` de `frontend/src/App.jsx` para `frontend/src/pages/Login.jsx` com `useState` controlado para `nomeUsuario` e `senha`, sem `defaultValue="admin"`/`"admin123"` e sem `alert()`.
   - Exibir mensagem de erro inline acessível (`role="alert"`) e aviso informativo quando a URL contiver `?sessao=expirada`.
   - Em `frontend/src/api/config.js`: no interceptor de resposta `401` (exceto quando a própria requisição for `/autenticacao/entrar`), remover `token_atividros`, emitir evento customizado (ex.: `window.dispatchEvent(new Event('atividros:sessao-expirada'))`) ouvido pelo `ContextoAutenticacao` para zerar `usuario`, e redirecionar para `/login?sessao=expirada`.
   - Em `frontend/vite.config.js`: remover `allowedHosts` ngrok hardcoded e carregar hosts permitidos de variável de ambiente opcional (`VITE_ALLOWED_HOSTS`).

#### Gate de Saída (Sprint 0)
- `git ls-files` não contém `.idea/`, `*.db`, `frontend/src/test*.jsx` nem docs raiz obsoletos.
- `cd backend && pytest` 100% verde (incluindo novos testes `401` e `test_login_nao_loga_senha`).
- `cd backend && ruff check app tests scripts` sem violações.
- `python -m scripts.create_admin` executa sem `ModuleNotFoundError`.
- `cd frontend && npm run lint && npm run build` sem erros; login testado manualmente rejeitando senha inválida e redirecionando no `401`.

---

### Épico 2 / Sprint 1 — Remodelagem de Dados, Alembic Dual-Engine e Numeração Sequencial

**Objetivo:** Estruturar a base relacional completa da V1.0 compatível com SQLite e PostgreSQL, corrigir o pipeline do Alembic e erradicar o contador de pedidos em memória (`NUMERO_COUNTER`).

#### Tarefas Técnicas
1. **Driver PostgreSQL e Configuração Dual-Engine (`app/db/session.py`, `pyproject.toml`, Achado E4):**
   - Adicionar `asyncpg = "^0.30.0"` em `backend/pyproject.toml`.
   - Em `backend/app/db/session.py`: adicionar event listener no engine síncrono subjacente quando o dialeto for `sqlite` para executar `PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;` em novas conexões.
2. **Correção do Alembic (`backend/migrations/env.py`, Achado E2):**
   - Importar **todos** os módulos de modelos (`usuario`, `cliente`, `estoque`, `tabela_preco`, `pedido`) para popular `Base.metadata`.
   - Configurar `config.set_main_option("sqlalchemy.url", settings.database_url)`.
   - Habilitar `render_as_batch=True` em `run_migrations_offline()` e `do_run_migrations()` para compatibilidade de `ALTER TABLE` no SQLite.
3. **Remodelagem das Entidades (`backend/app/models/`, Débito D3, `ARQUITETURA §3.2–3.3`):**
   - `models/estoque.py` (com integridade referencial protegida por `ON DELETE RESTRICT` nas FKs de `ItemPedidoMoldura.moldura_id`, `ItemPedido.vidro_id` e `ItemPedido.fundo_id`):
     - `Moldura`: adicionar `estoque_minimo: Mapped[int]` (default `5`, `CHECK >= 0`); permitir `quantidade` negativa (sem `CHECK >= 0`, pois ruptura é permitida).
     - `Vidro`: remover `quantidade`, `largura_chapa`, `altura_chapa`; adicionar `area_disponivel_m2: Mapped[Decimal]` (`Numeric(12, 4)`, default `0.0000`) e `estoque_minimo_m2: Mapped[Decimal]` (`Numeric(12, 4)`, default `2.0000`, `CHECK >= 0`).
     - `Fundo`: remover `quantidade`, `largura`, `altura`; adicionar `area_disponivel_m2: Mapped[Decimal]` (`Numeric(12, 4)`) e `estoque_minimo_m2: Mapped[Decimal]` (`Numeric(12, 4)`).
   - `models/tabela_preco.py`:
     - `TabelaPrecoVidro`: adicionar `area_minima_m2: Mapped[Decimal]` (`Numeric(10, 4)`, default `0.2500`, `CHECK >= 0`).
     - `TabelaPrecoFundo` *(nova)*: `id`, `tipo` (`String(50)`, `UNIQUE`, `NOT NULL`), `preco_por_m2` (`Numeric(10, 2)`), `descricao`.
     - `TabelaPrecoPaspatour`: adicionar `UNIQUE` em `descricao`.
   - `models/pedido.py`:
     - Saneamento de Enums: `StatusProducao` (`pendente`, `aguardando_material`, `na_fila`, `em_producao`, `embalando`, `pronto_entrega` — **sem `entregue`** e trocando `para_embalar` por `embalando`); `StatusFinanceiro` (`sem_pagamento`, `pagamento_parcial`, `pago_total`, `estornado` — trocando `sinal_recebido`); `Eixo` (`geral`, `producao`, `financeiro`, `estoque`); novos enums `TipoItemPedido` (`quadro_sob_medida`, `vidro_avulso`, `servico_livre`), `TipoDesconto` (`valor`, `percentual`) e `FormaPagamento` (`pix`, `cartao_credito`, `cartao_debito`, `dinheiro`, `outro`).
     - `SequenciaNumeracao` *(nova)*: tabela `sequencia_numeracao (ano INTEGER PRIMARY KEY, ultimo_valor INTEGER NOT NULL)`.
     - `Pedido`: remover `valor_sinal`; adicionar `data_validade_orcamento` (`Date`), `prazo_entrega` (`Date`), `desconto_valor` (`Numeric(12, 2)`), `desconto_tipo` (`Enum(TipoDesconto)`), `subtotal_itens` (`Numeric(12, 2)`), `valor_pago` (`Numeric(12, 2)`), `observacoes` (`Text`).
     - `ItemPedido`: remover `moldura_id`, `largura`, `altura`; garantir `vidro_id` (`FK -> vidros.id`, `ON DELETE RESTRICT`) e `fundo_id` (`FK -> fundos.id`, `ON DELETE RESTRICT`); adicionar `tipo_item`, `valor_sugerido`, `obra_largura`, `obra_altura`, `paspatour`, `tamanho_paspatour`, `paspatour_id`, `vidro_tipo`, `fundo_tipo`, `mao_de_obra`, `snapshot_calculo` (`JSON`).
     - `ItemPedidoMoldura` *(nova)*: `id`, `item_pedido_id`, `moldura_id` (`ON DELETE RESTRICT`), `ordem`, `codigo_moldura_snapshot`, `largura_barra_cm`, `tamanho_barra_m`, `preco_m_aplicado`, `altura_calculada_cm`, `largura_calculada_cm`, `metragem_total_m`, `barras_sugeridas`, `UNIQUE(item_pedido_id, ordem)`.
     - `PagamentoPedido` *(nova)*: `id`, `pedido_id`, `valor` (`CHECK > 0`), `forma_pagamento`, `data_pagamento`, `observacao`, `estornado` (`bool`), `criado_em`.
     - Atualizar `models/__init__.py` exportando todas as classes para uso limpo sem `F821` onde possível.
4. **Migration Consolidada V1.0 (`backend/migrations/versions/`):**
   - Criar revisão Alembic `v1_0_remodelagem_completa.py` aplicando as alterações estruturais de forma idempotente/limpa sobre a cadeia existente (garantindo que `alembic upgrade head` em banco vazio e sobre a revisão anterior funcione tanto em SQLite quanto em PostgreSQL).
5. **Serviço de Numeração Sequencial Segura (`ADR-005`, Débito D1):**
   - Remover `NUMERO_COUNTER` de `backend/app/services/pedido.py:39-46`.
   - Implementar `gerar_numero_pedido(db: AsyncSession) -> str` usando `INSERT INTO sequencia_numeracao (ano, ultimo_valor) VALUES (:ano, 1) ON CONFLICT (ano) DO UPDATE SET ultimo_valor = sequencia_numeracao.ultimo_valor + 1 RETURNING ultimo_valor` com ano corrente em fuso `America/Sao_Paulo` (configurável), `BEGIN IMMEDIATE` no dialeto `sqlite` e retry controlado em `OperationalError` transitório (`50ms`, `100ms`, `200ms`).

#### Gate de Saída (Épico 2)
- `alembic upgrade head` cria todas as 15 tabelas (`usuarios`, `clientes`, `molduras`, `vidros`, `fundos`, `suplementos`, `tabela_preco_vidro`, `tabela_preco_fundo`, `tabela_preco_paspatour`, `sequencia_numeracao`, `pedidos`, `itens_pedido`, `itens_pedido_moldura`, `pagamentos_pedido`, `pedidos_eventos`) em SQLite limpo e `alembic check` não acusa drift.
- Teste automatizado de concorrência criando múltiplos pedidos em paralelo e após descarte/reinício do engine gerando `202600001`, `202600002`... sem colisão.

---

### Épico 3 / Sprint 2 — Motor Único de Cálculo, Estoque `m²` e Tabelas de Preço

**Objetivo:** Consolidar toda a matemática determinística em `services/calculadora.py`, implementar o controle contínuo de chapas em `m²` com conversor de entrada, CRUD completo das 3 tabelas de preço e busca/histórico otimizado de clientes.

#### Tarefas Técnicas
1. **Motor Único de Cálculo (`app/services/calculadora.py`, `schemas/calculadora.py`, `api/calculadora.py`, Débito D7):**
   - Remover rotas legadas `POST /calculadora/` e `POST /calculadora/simular` e remover `obter_detalhes_calculo` de `services/pedido.py:61-110`.
   - Implementar `calcular_quadro(db, entrada)` (`POST /calculadora/quadro`) e `calcular_vidro_avulso(db, entrada)` (`POST /calculadora/vidro-avulso`) usando exclusivamente `decimal.Decimal` (`ROUND_HALF_UP`, 2 casas para R$/cm e 4 casas para m²/m):
     - **Propagação:** `Obra` → `Vidro/Paspatour/Fundo` (`+ 2 × tamanho_paspatour` se ativo) → `Molduras 0..N` (`+ 2 × largura_barra_cm`) → `Quadro Final`.
     - **Perda 45°:** `perimetro_seco_m = 2 × (altura_N + largura_N) / 100`, `perda_45_m = (8 × largura_barra_N) / 100`, `metragem_total_m = perimetro_seco_m + perda_45_m`, `barras_sugeridas = ceil((metragem_total_m × quantidade) / tamanho_barra_N)`.
     - **Vidro / Espelho:** `area_real_m2 = (altura_vidro × largura_vidro) / 10000`, `area_cobrada_m2 = max(area_real_m2, area_minima_m2)`.
     - **Paspatour:** exige `paspatour_id` válido (`TabelaPrecoPaspatour`, eliminando `limit(1)` implícito, conforme `ADR-003`).
     - **Fundo (`TabelaPrecoFundo`):** resolve `fundo_tipo` ou `fundo_id` (`Fundo.tipo`) e calcula sobre `area_real_m2` (medida do vidro, não apenas da obra).
     - **Mão de obra (`ADR-002`):** `R$/unidade` somada ao `valor_sugerido_unitario`, multiplicado por `quantidade` para `total_sugerido`.
   - Retornar estrutura completa (`dimensoes`, `areas`, `custos`, `valor_sugerido_unitario`, `total_sugerido`, `descricao_sugerida`) pronta para persistência em `ItemPedido.snapshot_calculo`.
2. **Estoque `m²`, Conversor de Chapas e Filtros (`app/api/estoque.py`, `schemas/estoque.py`, `ADR-001`, `ADR-008`):**
   - Atualizar schemas e rotas de `Moldura` (`estoque_minimo`, `preco_custo` em `R$/m`, filtros `?q=` e `?critico=true`).
   - Atualizar `Vidro` e `Fundo` para `area_disponivel_m2` e `estoque_minimo_m2`.
   - Criar `POST /estoque/vidros/{id}/entrada-chapas` e `POST /estoque/fundos/{id}/entrada-chapas` calculando `(quantidade_chapas × largura_cm × altura_cm) / 10000` com precisão de 4 casas decimais e log operacional.
   - Criar `POST /estoque/vidros/{id}/ajuste-m2` e `POST /estoque/fundos/{id}/ajuste-m2` para inventário manual direto (permitindo ajuste positivo ou negativo).
   - Impedir exclusão de `Moldura`, `Vidro` ou `Fundo` com vínculo em itens de pedido (alinhado ao `ON DELETE RESTRICT` nas FKs `ItemPedidoMoldura.moldura_id`, `ItemPedido.vidro_id` e `ItemPedido.fundo_id`), retornando `409 Conflict` amigável.
3. **CRUD Completo das 3 Tabelas de Preço (`app/api/calculadora.py`, `schemas/tabela_preco.py`):**
   - Atualizar `TabelaPrecoVidro` com `area_minima_m2` (default `0.2500`) + `DELETE /calculadora/tabela-vidro/{id}`.
   - Criar CRUD completo `GET/POST/PUT/DELETE /calculadora/tabela-fundo[/{id}]`.
   - Adicionar `DELETE /calculadora/tabela-paspatour/{id}` e validação de duplicidade (`400`/`409`).
4. **Clientes e Histórico Filtrado no Servidor (`app/api/clientes.py`, `schemas/cliente.py`, Achados E10, E12):**
   - Aplicar `empty_str_to_none` compartilhado em `BaseCliente` e `AtualizarCliente` (`email`, `endereco`, `cep`).
   - Implementar busca server-side `GET /clientes/?q=` (case-insensitive em `nome`, `sobrenome`, `telefone`, `email`).
   - Implementar `GET /clientes/{id}/pedidos` retornando `list[RespostaPedidoResumo]` ordenado por `criado_em DESC` (`404` se cliente inexistente).
   - Proteger `DELETE /clientes/{id}` com `409 Conflict` se houver pedidos vinculados.

#### Gate de Saída (Épico 3)
- `POST /calculadora/` e `POST /calculadora/simular` removidos (retornam `404`); nenhuma ocorrência de `Decimal("100.0")` ou `Decimal("30.0")` hardcoded em serviços.
- Testes unitários de cálculo (`Decimal`) e testes de integração de chapas `m²`, 3 tabelas de preço e `GET /clientes/{id}/pedidos` 100% passando.

---

### Épico 4 / Sprint 3 — Pedidos, 3 Eixos Saneados, Pagamentos, Baixa Assistida e PDF Único

**Objetivo:** Entregar o núcleo transacional de pedidos com os 3 tipos de item, cálculo correto de frete/desconto, 3 eixos independentes, múltiplos pagamentos com estorno, Baixa Assistida não-bloqueante, `/dashboard/resumo` e PDF Único A4.

#### Tarefas Técnicas
1. **CRUD de Pedidos Multi-Item, Snapshot e Totais (`app/services/pedido.py`, `api/pedidos.py`, `schemas/pedido.py`, Débito D2):**
   - `POST /pedidos/`: exige `itens` (`min_length=1`); para cada item `quadro_sob_medida` ou `vidro_avulso`, invoca `services/calculadora.py` para gravar `valor_sugerido`, `snapshot_calculo` e `ItemPedidoMoldura` (`0..N`); aceita `preco_unitario` sobrescrito livremente e calcula flag derivada `abaixo_do_sugerido = preco_unitario < valor_sugerido`.
   - `data_validade_orcamento`: preenchida automaticamente (`hoje + 7 dias`) na criação de `rascunho` se omitida.
   - Totais exclusivos no backend: `subtotal_itens`, `frete` **somado ao total**, `desconto_valor`/`desconto_tipo` (`valor` ou `percentual` validado `0..100`), `valor_total = max(0, subtotal_itens + frete - desconto_calculado)` e `saldo_devedor = max(0, valor_total - valor_pago)`.
   - `PUT /pedidos/{id}`: bloqueia com `400` se `status_geral != "rascunho"`.
   - `GET /pedidos/`: filtros server-side `?cliente_id=`, `?status_geral=`, `?status_producao=`, `?q=`.
   - `DELETE /pedidos/{id}`: permitido apenas para `rascunho` ou `cancelado` sem pagamentos não estornados (`400` caso contrário).
2. **Máquinas de Estado dos 3 Eixos (`app/services/pedido.py`, `ARQUITETURA §4.2`):**
   - **Eixo Geral:** `rascunho → confirmado | cancelado`; `confirmado → entregue | cancelado`; `entregue → arquivado`. Ao confirmar pedido com `valor_total == 0` (desconto 100%), `status_financeiro` deriva automaticamente para `"pago_total"`. Ao cancelar com `valor_pago > 0`, não altera silenciosamente pagamentos reais: grava evento indicando estorno pendente e retorna flag/alerta na resposta (`requer_estorno: true`), permitindo acionar o estorno explícito via `/pagamentos/{pag_id}/estornar`.
   - **Eixo Produção:** `pendente`, `aguardando_material`, `na_fila`, `em_producao`, `embalando`, `pronto_entrega` (**sem `entregue`**). Rejeita transição com `400` se `status_geral in ["cancelado", "arquivado"]`. Rejeita transição para `em_producao` via `PATCH /status` (exige `POST /baixa-estoque`).
   - **Eixo Financeiro:** somente derivado de `PagamentoPedido` e da regra de total zerado (`valor_total == 0` → `pago_total` ao confirmar), bloqueando alteração manual via `PATCH /status`.
3. **Múltiplos Pagamentos e Estorno (`POST /pedidos/{id}/pagamentos`, `POST .../estornar`):**
   - `POST /pedidos/{id}/pagamentos`: valida `valor > 0` e `valor <= saldo_devedor`; bloqueia em `cancelado`/`arquivado`; confirma automaticamente pedido se estava em `rascunho` (`PedidoEvento` no eixo `geral`); recalcula `valor_pago`, `saldo_devedor` e `status_financeiro` (`pagamento_parcial` ou `pago_total`); grava `PedidoEvento(eixo="financeiro")`. No caso de borda `valor_total == 0` (desconto 100%), ao confirmar o pedido `status_financeiro` deriva automaticamente para `"pago_total"`.
   - `POST /pedidos/{id}/pagamentos/{pag_id}/estornar`: permitido inclusive em pedidos `cancelado` para regularizar estorno pendente, bloqueado com `400` apenas em pedidos `arquivado` ou quando o pagamento já estiver estornado; marca `estornado = True`, recalcula totais e define `status_financeiro = "estornado"` quando existiram pagamentos lançados (`len(pagamentos) > 0`) e **todos** foram estornados (`valor_pago == 0`), ou `"pagamento_parcial"` se ainda restar saldo pago válido (`0 < valor_pago < valor_total`, ou `"pago_total"` se `valor_pago >= valor_total`); `"sem_pagamento"` aplica-se apenas quando nunca houve pagamento lançado (`len(pagamentos) == 0`).
4. **Baixa de Estoque Assistida Não-Bloqueante (`GET /previsao-baixa`, `POST /baixa-estoque`, `ADR-008`):**
   - `GET /pedidos/{id}/previsao-baixa`: exige **`status_geral == "confirmado"`** (rejeitando `rascunho`, `entregue`, `cancelado` e `arquivado` com `400`) e `status_producao in ["pendente", "aguardando_material", "na_fila"]`; agrupa `ItemPedidoMoldura` por `moldura_id` (`barras_sugeridas`, `estoque_atual`, `saldo_projetado`, `em_ruptura`), agrupa `vidro_id`/`fundo_id` pela soma de `area_real_m2 × quantidade` do `snapshot_calculo` (`area_a_baixar_m2`, `area_disponivel_m2`, `saldo_projetado_m2`, `em_ruptura`) e informa `possui_insumos_estoque: bool` (contemplando `false` quando não há insumos físicos vinculados, ex.: `servico_livre`).
   - `POST /pedidos/{id}/baixa-estoque`: exige **`status_geral == "confirmado"`** (rejeitando `rascunho`, `entregue`, `cancelado` e `arquivado` com `400`); aceita `ajustes_molduras` opcionais (`barras_baixadas >= 0`); debita molduras, vidros e fundos em transação única **mesmo que saldo fique negativo**, contemplando também o caso `possui_insumos_estoque: false` (ex.: `servico_livre`, avançando `status_producao` para `em_producao` com `materiais_baixados: []` e `alertas_ruptura: []`); grava `status_anterior` real no `PedidoEvento` (corrigindo o hardcode `pendente`), registra evento no eixo `estoque` + eixo `producao`, loga `WARNING` se houver ruptura e retorna `materiais_baixados` + `alertas_ruptura`.
5. **Dashboard Operacional (`GET /dashboard/resumo`, `ARQUITETURA §6.3.9`, Achado E9):**
   - Criar router `app/api/dashboard.py` e registrar em `main.py`.
   - `receita_confirmada`: soma `valor_total` apenas de `confirmado`, `entregue`, `arquivado` (exclui `rascunho` e `cancelado`).
   - `total_a_receber`: soma `saldo_devedor` de `confirmado` e `entregue`.
   - Contadores `pedidos_ativos`, `pedidos_hoje`, `pedidos_prazo_vencido`, `pedidos_vencendo_hoje`, `orcamentos_abertos` e objeto aninhado **`alertas_estoque`** contendo `molduras_criticas` (`<= estoque_minimo`), `vidros_criticos` e `fundos_criticos` (`<= estoque_minimo_m2`, priorizando negativos).
6. **PDF Único A4 (`app/services/gerador_pdf.py`, `ADR-009`, `DESIGN_SYSTEM §6`):**
   - Refatorar `GeradorPDFPedido(FPDF)` para gerar A4 Retrato em memória (`fpdf2`) com:
     - Banner contextual: `ORÇAMENTO #...` + `Validade: DD/MM/AAAA` (`rascunho`), `PEDIDO / ORDEM DE SERVIÇO #...` + `Prazo de Entrega: DD/MM/AAAA` (`confirmado`, `entregue`, `arquivado`), ou cabeçalho `PEDIDO CANCELADO #...` (omitindo `Prazo de Entrega`) quando `status_geral == "cancelado"`.
     - Dados do cliente e endereço de entrega.
     - Tabela de itens usando `item.descricao` + sublinhas técnicas do `snapshot_calculo` (`Obra`, `Paspatour`, `Vidro / Fundo`, `Molduras int→ext` com medidas de corte, `QUADRO FINAL` em negrito).
     - Resumo financeiro (`Subtotal`, `Frete (+)`, `Desconto (-)`, `TOTAL DO PEDIDO`, pagamentos não estornados / `Total Pago`, `SALDO DEVEDOR` — omitindo `SALDO DEVEDOR` como cobrança ativa quando `status_geral == "cancelado"`).
     - Campo `Observações` e linhas duplas de assinatura (`Assinatura do Cliente / Aprovação` e `Conferência Oficina`).
     - **Regra absoluta de sigilo:** `valor_sugerido`, `abaixo_do_sugerido` e `preco_custo` nunca são renderizados no PDF.

#### Gate de Saída (Épico 4)
- Suíte `pytest` cobrindo 100% dos fluxos do Épico 4 (frete, desconto `%`/`R$`, 3 eixos, múltiplos pagamentos, estorno, Baixa Assistida com ruptura negativa `200 OK`, snapshot imutável, dashboard e inspeção textual do PDF Único).

---

### Épico 5 / Sprints 4–5 — Design System CSS Modular + Refatoração do Frontend (Balcão e Oficina)

**Objetivo:** Implantar a arquitetura visual `.at-*` em `src/styles/`, construir os primitivos acessíveis em `src/components/ui/`, estruturar a suíte Vitest/RTL, decompor o monolito `Pedidos.jsx` (939 linhas) e atualizar todas as páginas para operação dual (Balcão desktop + Oficina mobile/tablet).

#### Sprint 4 — Design System, Primitivos UI, Setup de Testes e Páginas Core
1. **Arquitetura CSS Modular (`frontend/src/styles/`, `DD-001`..`DD-008`):**
   - Criar `tokens.css` (Camadas 1, 2 e 3 com paleta *High-Contrast Slate*, corrigindo contraste `.btn-primary` de `2,54:1` para `5,70:1` `#042F2E` sobre `#10B981`), `base.css` (tipografia 8 passos em `rem`, `.at-num` `tabular-nums`, `:focus-visible`, `prefers-reduced-motion`), `layout.css` (`.at-app`, `.at-sidebar` `240px`, `.at-mobile-header` `56px`, `.at-container` `max-width: 1440px`, grids responsivos) e `components.css` (`.at-btn`, `.at-card`, `.at-input`, `.at-table`, `.at-status--*`, `.at-dialog`, `.at-callout`, `.at-toast`, `.at-state`).
   - Criar folhas específicas em `src/styles/pages/`: `pedidos.css`, `calculadora.css`, `estoque.css`.
   - Substituir `src/index.css` por importação limpa das camadas em `main.jsx` e eliminar `--card-bg` e `--warning` quebrados.
2. **Primitivos Acessíveis (`frontend/src/components/ui/`):**
   - Criar `Button.jsx`, `Card.jsx`, `Field.jsx`, `Dialog.jsx` (baseado em `<dialog>.showModal()` com trap de foco e `Esc`), `ConfirmDialog.jsx` (botão `Cancelar` à esquerda com foco inicial, `DD-010`), `StatusBadge.jsx` (3 famílias semânticas distintas + ícone `lucide-react` + borda distintiva, `DD-005`), `Callout.jsx` (`warning` não-bloqueante vs `danger` bloqueante, `DD-006`), `ToastRegion.jsx` (`aria-live="polite"`, `6s`), `EmptyState.jsx` (base vazia vs filtro sem resultado), `Tabs.jsx` (roving tabindex) e `DataTable.jsx`.
3. **Setup de Testes Frontend (`frontend/package.json`, `vite.config.js`, Achado E11):**
   - Instalar `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event` e `jsdom`.
   - Configurar script `"test": "vitest run"`, `"test:watch": "vitest"`, `"test:cov": "vitest run --coverage"` e setup global (`src/test/setup.js`).
   - Criar helpers testáveis em `src/utils/formatadores.js` (`formatarMoeda`, `formatarMedidaCm`, `formatarAreaM2`, `calcularCustoPorMetroDeBarra`, `calcularTotaisPreviewPedido`).
4. **Refatoração de `Layout.jsx`, `App.jsx`, `Dashboard.jsx`, `Clientes.jsx`, `Estoque.jsx`, `TabelasPreco.jsx` e `Calculadora.jsx`:**
   - **`Layout.jsx` (300 L → modular sem `<style>`):** remover 215 L de `<style>` inline e `.sidebar-logo` duplicado; adicionar item **`Tabelas de Preço`** (`/precos`) no menu lateral; usar `<nav aria-label>`, `aria-expanded` e `Esc` no drawer mobile.
   - **`App.jsx`:** remover `<div className="container">` duplicado de `RotaProtegida`, registrar rota `/precos` (`TabelasPreco`) e rota fallback `*`, integrar `ToastRegion`.
   - **`Dashboard.jsx` (208 L):** extrair `ui/StatCard.jsx`; consumir `GET /dashboard/resumo`; exibir `Receita Confirmada`, `A Receber`, `Pedidos Hoje`, `Prazos Vencidos / Vencendo Hoje` e listas de estoque crítico (negativos destacados no topo e saldos em `m²`).
   - **`Clientes.jsx` (380 L):** remover `<style>` inline e `window.confirm`; usar `Dialog`/`ConfirmDialog`; busca server-side `?q=` com placeholder claro (`"Nome, sobrenome, telefone ou e-mail"`); extrair `components/clientes/ModalHistoricoCliente.jsx` consumindo `GET /clientes/{id}/pedidos`.
   - **`Estoque.jsx` (480 L) + `TabelasPreco.jsx` (Nova):** remover `<style>` inline; exibir unidade explícita `(R$/m)` no custo/venda das molduras + extrair `CalculadoraCustoBarra.jsx` (`DD-004`); adicionar `estoque_minimo` / `estoque_minimo_m2`; exibir saldo de Vidros e Fundos em `m²` com `ModalEntradaChapas.jsx` e `ModalAjusteM2.jsx`; implementar página dedicada `TabelasPreco.jsx` para CRUD de `TabelaPrecoVidro` (com `area_minima_m2`), `TabelaPrecoFundo` e `TabelaPrecoPaspatour`.
   - **`Calculadora.jsx` (245 L):** remover `<style>` inline e `alert()`; extrair `FormComposicaoQuadro.jsx` e `PainelResultadoCalculo.jsx`; suportar alternância `Quadro Sob Medida` vs `Vidro Avulso`; incluir `Mão de obra (R$/un)` (`DD-003`), seleção de `paspatour_id`, `vidro_tipo` + `vidro_id` (chapa estoque), `fundo_tipo` + `fundo_id` e botão primário **`Adicionar ao Pedido`** (cria novo rascunho ou anexa a orçamento em rascunho).

#### Sprint 5 — Plano Explícito de Decomposição do Monólito `Pedidos.jsx` (939 linhas)

O arquivo `frontend/src/pages/Pedidos.jsx` atualmente concentra **939 linhas** com 7 responsabilidades acopladas, chamadas ao endpoint legado `/calculadora/simular`, `<style>` inline (L849–934), coluna proibida `entregue` no Kanban (L747) e tokens inexistentes (`--card-bg`, `--warning`). A decomposição seguirá estritamente a estrutura definida em `DESIGN_SYSTEM.md §4.3`:

```text
frontend/src/
├── components/pedidos/
│   ├── KanbanBoard.jsx               # (~140 L) 6 colunas saneadas (pendente..pronto_entrega) + abas com contadores no mobile (<=767px)
│   ├── PedidoCard.jsx                # (~100 L) Card limpo com #numero (tabular-nums), cliente, prazo, máx. 2 badges (Geral + Financeiro) e CTA contextual >=44px
│   ├── PedidoLista.jsx               # (~130 L) DataTable desktop / cards empilhados mobile com os 3 eixos explícitos e filtros por status_geral
│   ├── PedidoForm.jsx                # (~220 L) Criação/edição de rascunho: cliente (+ Novo Cliente), mix dos 3 tipos de item, edição livre de preço com Callout amarelo não-bloqueante, frete, desconto (R$/%), validade e prazo
│   ├── ModalAdicionarItemPedido.jsx  # (~160 L) Seletor segmentado (Quadro sob medida / Vidro avulso / Serviço livre) reutilizando componentes da Calculadora
│   ├── PedidoDetalhe.jsx             # (~210 L) Visão 2 colunas: controle dos 3 eixos, botão "Marcar Entregue", lista técnica de cortes, pagamentos, timeline de PedidoEvento, Baixar PDF e Cancelar (ConfirmDialog)
│   ├── ModalBaixaEstoque.jsx         # (~160 L) Consome GET previsao-baixa -> ajuste manual barras (+/- >=44px) com recálculo instantâneo de saldo projetado, estado vazio para possui_insumos_estoque=false (servico_livre) -> Callout amarelo não-bloqueante em ruptura -> POST baixa-estoque
│   └── ModalPagamento.jsx            # (~130 L) Lista de PagamentoPedido + estorno + formulário (valor, forma_pagamento, data, obs) + aviso de confirmação automática se rascunho
└── pages/Pedidos.jsx                 # (~150 L) Orquestrador de rota, filtros rápidos (Kanban ativo vs Lista completa), busca ?q= e coordenação de estado/modais
```

**Regras Obrigatórias na Decomposição de `Pedidos.jsx`:**
1. **Zero acesso direto a `api.post('/calculadora/simular')`**: `ModalAdicionarItemPedido` invoca `POST /calculadora/quadro` ou `POST /calculadora/vidro-avulso`.
2. **Kanban estritamente com 6 colunas (`ADR-008`, `DESIGN_SYSTEM §5.4`):** `pendente`, `aguardando_material`, `na_fila`, `em_producao`, `embalando`, `pronto_entrega`. A coluna `entregue` é removida; a entrega é feita pelo botão **`Marcar Entregue`** (`status_geral = entregue`). O Kanban ativo exibe **apenas pedidos `confirmado`**, ocultando `rascunho` (Orçamentos), `entregue`, `arquivado` e `cancelado` (acessíveis na visão **Lista**).
3. **Oficina Mobile (`<= 767 px`):** O `KanbanBoard` alterna automaticamente para barra horizontal de chips de estágio com contadores, exibindo os cards da etapa selecionada em 100% da largura com medidas técnicas legíveis (`>= 16 px`) e botões `>= 44 × 44 px`.
4. **Transição para `em_producao`:** Bloqueada em dropdowns diretos; sempre abre `ModalBaixaEstoque`.

#### Gate de Saída (Épico 5)
- `Pedidos.jsx` reduzido de `939 L` para `<= 180 L` atuando apenas como orquestrador dos 8 componentes em `src/components/pedidos/`.
- Zero ocorrências de `<style>`, `window.alert`, `window.confirm`, `--card-bg`, `--warning` ou `/calculadora/simular` em `frontend/src/`.
- `npm test` (`vitest run`), `npm run lint` e `npm run build` passam 100%.

---

### Épico 6 / Sprint 6 — Hardening E2E, Portabilidade PostgreSQL e Aceite Final V1.0

**Objetivo:** Certificar o sistema de ponta a ponta em condições reais de operação (Balcão + Oficina + PostgreSQL), garantir cobertura mínima consolidada e executar o checklist final de acessibilidade e segurança.

#### Tarefas Técnicas
1. **Portabilidade e Teste em PostgreSQL (`asyncpg`):**
   - Subir instância PostgreSQL de verificação (local/Docker), configurar `DATABASE_URL=postgresql+asyncpg://...`, rodar `alembic upgrade head` do zero e executar a bateria `pytest` validando dialeto PostgreSQL (especialmente `SequenciaNumeracao` `ON CONFLICT ... RETURNING`, `Numeric`, `Enum` e `JSON`).
2. **Elevação do Piso de Cobertura e Gates de CI Local:**
   - Elevar `fail_under` em `backend/pyproject.toml:45` de `50` para **`80`** após validar cobertura real (`services/calculadora.py >= 95%`, `services/pedido.py >= 85%`, `services/gerador_pdf.py >= 85%`).
3. **Verificação E2E Balcão + Oficina + Acessibilidade WCAG 2.2 AA:**
   - Executar jornada completa manual/automatizada: Login real → Cadastrar Moldura (`R$/m`), Chapa de Vidro (`entrada-chapas` m²) e `TabelaPrecoFundo` → Calcular Quadro com Paspatour + 2 Molduras + Mão de obra → **Adicionar ao Pedido** → Sobrescrever preço abaixo do sugerido (confirmar banner amarelo) → Adicionar Vidro Avulso + Serviço Livre + Frete + Desconto → Baixar **PDF Orçamento** (conferir ausência de `valor_sugerido`) → Lançar 1º Pagamento PIX (confirmar conversão automática para `confirmado`) → Mover na Oficina para `em_producao` via **Modal de Baixa Assistida** com ajuste de barras e ruptura negativa → Baixar **PDF OS** → Avançar até `pronto_entrega` → `Marcar Entregue` → Quitar saldo restante → Conferir Dashboard.
   - Validar layout em desktop (`1280×800`), tablet (`768×1024`) e celular oficina (`375×812` e reflow `320 px`), navegação por teclado (`Tab`/`Esc`/foco inicial em `Cancelar` no `ConfirmDialog`) e auditoria com `axe-core`/Lighthouse.

#### Gate de Saída (Aceite Final V1.0)
- `pytest --cov=app` com `>= 80%` de cobertura e **0 falhas** (SQLite e PostgreSQL validados).
- `ruff check` sem erros ou warnings pendentes.
- `vitest run` + `npm run lint` + `npm run build` verdes.
- Checklist WCAG 2.2 AA (`DESIGN_SYSTEM.md §8`) e RNFs (`ARQUITETURA.md §7.4`) validados com evidências registradas.

---

## 7. Estratégia Completa de Testes Automatizados

### 7.1 Backend (`pytest` + `pytest-asyncio` + `httpx` + `pytest-cov`)

#### A. Plano de Atualização de Testes Legados (Mudanças Intencionais da V1.0)
Alguns testes existentes no repositório falharão **propositalmente** quando os débitos da V1.0 forem corrigidos e devem ser atualizados nos respectivos épicos:

| Arquivo Legado | Comportamento Legado Atual | Épico | Ação Planejada na V1.0 |
|---|---|---|---|
| `backend/tests/test_calculadora_extra.py:22,83` | Faz `GET /calculadora/tabela-vidro` e `GET /calculadora/tabela-paspatour` **sem token** esperando `200`. | **Épico 1** | Enviar `headers=cabecalho_autorizacao` nos casos de sucesso e adicionar testes explícitos garantindo `401` sem auth. |
| `backend/tests/test_estoque.py` e `test_estoque_extra.py` | Cria `Vidro`/`Fundo` com `quantidade`, `largura_chapa`, `altura_chapa` e lista `GET` sem auth. | **Épico 1 / 2 / 3** | Adicionar auth em todos os `GET`; migrar fixtures de `Vidro`/`Fundo` para `area_disponivel_m2` e `estoque_minimo_m2`. |
| `backend/tests/test_calculadora.py` | Testa `POST /calculadora/` (endpoint legado com preços hardcoded). | **Épico 3** | Substituir por testes do motor unificado (`POST /calculadora/quadro` e `POST /calculadora/vidro-avulso`) e assert `404` para `/calculadora/` e `/calculadora/simular`. |
| `backend/tests/test_baixa_estoque.py:31-51` | `test_baixa_estoque_estoque_insuficiente` espera `400` quando saldo é insuficiente; usa `moldura_id` direto no item e `valor_sinal`. | **Épico 4** | Atualizar para esperar `200 OK` com `saldo_atual < 0`, `em_ruptura: true`, `alertas_ruptura` preenchido e uso do novo payload `ajustes_molduras` + `PagamentoPedido`. |
| `backend/tests/test_pedidos.py` e `test_pedidos_extra.py` | Usam `para_embalar`, `entregue` na produção, `sinal_recebido`, `valor_sinal` e `itens: []` (L62 de `test_baixa_estoque.py`). | **Épico 4** | Atualizar enums para `na_fila`, `embalando`, `pronto_entrega`, `pagamento_parcial`, exigir `min_length=1` nos itens e testar os novos contratos de pagamento. |

#### B. Novos Testes Unitários Obrigatórios (`backend/tests/unit/`)
1. `test_calculadora_motor.py`:
   - Propagação dimensional: obra sem paspatour, obra com paspatour (`+ 2 × borda`), e com `0`, `1` e `3` molduras ordenadas da interna para a externa.
   - Fórmula de perda 45°: `(8 × largura_barra_cm) / 100` somada ao perímetro seco; cálculo exato de `barras_sugeridas = ceil((metragem_total × qtd) / tamanho_barra)`.
   - Regra de área mínima do vidro (`max(area_real_m2, area_minima_m2)` para cobrança vs `area_real_m2 × qtd` para estoque).
   - Área do fundo acompanhando a medida do vidro (`obra + 2 × paspatour`) e consultando `TabelaPrecoFundo`.
   - `mao_de_obra` como `R$/unidade` multiplicada por `quantidade`.
   - Arredondamento `Decimal` (`ROUND_HALF_UP`) e prevenção de erros de ponto flutuante.
2. `test_totais_pedido.py`:
   - `frete` somado corretamente a `subtotal_itens`.
   - Desconto `valor` e `percentual` (inclusive limite `100%` zerando `valor_total` sem ficar negativo).
   - `saldo_devedor = max(0, valor_total - valor_pago)` com múltiplos pagamentos e estornos parciais/totais.
3. `test_conversor_chapas.py`:
   - Conversão `(qtd × L × A) / 10000` em `Numeric(12, 4)` para chapas de vidro e fundo.

#### C. Novos Testes de Integração Obrigatórios (`backend/tests/integration/`)
1. `test_seguranca_rotas.py`: varredura sistemática validando `401 Unauthorized` sem token em todos os endpoints protegidos (todos os `GET/POST/PUT/PATCH/DELETE` de `/estoque/*`, `/calculadora/*`, `/clientes/*`, `/pedidos/*`, `/dashboard/*`), e `test_autenticacao_logs.py` com `caplog` em `DEBUG` verificando ausência de senha/JWT.
2. `test_sequencia_numeracao.py`: geração sequencial `YYYYNNNNN`, persistência após descarte/reinício de sessão/engine, virada de ano simulada, não-reutilização após `DELETE` de rascunho e execução concorrente (`asyncio.gather`) sem duplicidade.
3. `test_pedidos_ciclo_e_pagamentos.py`: mix dos 3 tipos de item (`quadro_sob_medida`, `vidro_avulso`, `servico_livre`), edição de preço abaixo do sugerido retornando `abaixo_do_sugerido: true`, bloqueio de `PUT` fora de `rascunho`, múltiplos `PagamentoPedido` (`pix`, `cartao_credito`), confirmação automática de `rascunho → confirmado` no 1º pagamento, bloqueio de pagamento `> saldo_devedor`, caso de borda **`valor_total == 0` (desconto 100%)** derivando automaticamente `status_financeiro = "pago_total"` ao confirmar pedido, cancelamento com alerta de estorno, estorno efetivo (inclusive em `cancelado` e bloqueado em `arquivado`/já estornado) validando `"estornado"` (`len(pagamentos) > 0` e `valor_pago == 0`) vs `"pagamento_parcial"` vs `"sem_pagamento"` (`len(pagamentos) == 0`).
4. `test_baixa_assistida_e_snapshot.py`: exigência de `status_geral == "confirmado"` em `previsao-baixa` e `baixa-estoque` (rejeitando `rascunho`, `entregue`, `cancelado` e `arquivado` com `400`), suporte ao caso `possui_insumos_estoque: false` (ex.: `servico_livre`), fluxo `previsao-baixa` → `baixa-estoque` com ajuste manual de barras de moldura, débito real de vidro/fundo em `m²` (sem área mínima comercial), saldo negativo permitido sem bloqueio (`200 OK` + `alertas_ruptura`), registro de `PedidoEvento` com `status_anterior` real e **teste de imutabilidade** alterando `preco_venda` de moldura após criar o pedido e confirmando que item/PDF preservam o snapshot original.
5. `test_clientes_dashboard_e_pdf.py`: busca `?q=` e `GET /clientes/{id}/pedidos` filtrado, `409` ao excluir cliente com pedido (e `409` em `Moldura`/`Vidro`/`Fundo` vinculados via `ON DELETE RESTRICT`), `GET /dashboard/resumo` excluindo `rascunho`/`cancelado` da receita confirmada e reportando `alertas_estoque` (`molduras_criticas`, `vidros_criticos`, `fundos_criticos`) com saldos negativos/abaixo do mínimo, e inspeção de conteúdo textual do PDF (`pypdf` ou extrator de texto em `fpdf2` / bytes) validando `ORÇAMENTO` + validade (`rascunho`), `PEDIDO / ORDEM DE SERVIÇO` + prazo (`confirmado`), `PEDIDO CANCELADO` sem `Prazo de Entrega` nem `SALDO DEVEDOR` como cobrança ativa (`cancelado`), camadas de corte, totais financeiros e **ausência** de `valor_sugerido`.

### 7.2 Frontend (`Vitest` + `@testing-library/react` + `@testing-library/user-event` + `jsdom`)

1. **Infraestrutura a adicionar em `frontend/package.json`:**
   - `devDependencies`: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `@vitest/coverage-v8`.
   - Mock limpo de `api` (`axios`) / `HTMLDialogElement.prototype.showModal` no `src/test/setup.js` para testar modais `<dialog>` em `jsdom`.
2. **Testes Unitários (`frontend/src/utils/__tests__/`):**
   - `formatadores.test.js`: formatação `R$`, `m²` (4 casas), medidas `cm`, cálculo auxiliar de `R$/m` a partir de custo da barra (`DD-004`) e preview de totais (`itens + frete - desconto`).
3. **Testes de Componentes e Fluxos Críticos (`frontend/src/__tests__/`):**
   - `Login.test.jsx`: formulário vazio envia valores reais digitados (não `admin123` fixo), exibe erro inline em falha `401`, e interceptor redireciona para `/login?sessao=expirada` exibindo banner informativo.
   - `FluxoCalculadoraPedido.test.jsx`: calcula quadro via API mockada, exibe `mao_de_obra` por unidade, aciona **"Adicionar ao Pedido"**, preenche item no `PedidoForm`, reduz `preco_unitario` abaixo de `valor_sugerido` e verifica exibição do alerta amarelo `.at-callout--warning` **mantendo botão de salvar habilitado**.
   - `ModalBaixaEstoque.test.jsx`: renderiza previsão de barras e `m²`, testa cliques nos botões `[-]`/`[+]` de ajuste manual atualizando saldo projetado em tempo real, verifica exibição do alerta de ruptura sem desabilitar `Confirmar Baixa e Iniciar Produção`, e cobre estado vazio sem insumos físicos (`possui_insumos_estoque: false`, ex.: `servico_livre`) permitindo avançar para `em_producao`.
   - `KanbanBoard.test.jsx`: garante exatamente **6 colunas** (`pendente`..`pronto_entrega`) **sem** coluna `entregue`, verifica que apenas pedidos `confirmado` aparecem no Kanban ativo (ocultando `rascunho`, `entregue`, `arquivado` e `cancelado`), ação `Marcar Entregue` na coluna `pronto_entrega`, e modo abas de estágio no viewport mobile.
   - `ConfirmDialog.test.jsx`: garante que ao abrir diálogo destrutivo, o foco inicial está no botão `Cancelar` (`DD-010`).

---

## 8. Plano de Limpeza do Repositório (Execução Exclusiva na Sprint 0)

> **Atenção:** Esta seção descreve os comandos a serem executados **somente ao iniciar a Sprint 0**. Nenhum arquivo foi removido durante a fase de planejamento.

### 8.1 Inventário Exato de Arquivos Residuais Identificados

1. **Arquivos Rastreados no Git (`git ls-files`) a Remover do Versionamento:**
   - Banco SQLite versionado indevidamente: `backend/test_atividros.db` (114 KB)
   - Rascunhos React residuais: `frontend/src/test.jsx` (108 B), `frontend/src/test2.jsx` (823 B)
   - Configurações locais de IDE JetBrains/PyCharm (6 arquivos rastreados):
     - `.idea/.gitignore`
     - `.idea/inspectionProfiles/Project_Default.xml`
     - `.idea/inspectionProfiles/profiles_settings.xml`
     - `.idea/misc.xml`
     - `.idea/modules.xml`
     - `.idea/vcs.xml`
   - Documentos legados obsoletos na raiz (substituídos por `docs/PRD.md`, `ARQUITETURA.md`, `DESIGN_SYSTEM.md`, `PLANO_IMPLEMENTACAO.md`):
     - `Plano de Desenvolvimento — Sistema Atividros v1.md` (359 linhas)
     - `Sistema atividros.md` (53 linhas)
2. **Migration Versionada Incorretamente Ignorada em `.gitignore`:**
   - `.gitignore:210` contém `/backend/migrations/versions/baf432e819f5_adicionando_modelos_de_pedidos.py`, impedindo que esta migration existente em disco seja versionada no git.
3. **Artefatos Locais Não Rastreados (Limpeza de Workspace na Sprint 0):**
   - `backend/atividros.db` (será recriado limpo via `alembic upgrade head` no Épico 2)
   - `backend/htmlcov/`, `backend/.coverage`, `backend/.pytest_cache/`, `backend/.ruff_cache/`, `frontend/dist/`

### 8.2 Sequência Segura de Comandos (Sprint 0)

```powershell
# 1. Remover arquivos residuais rastreados (mantendo apenas o que for histórico desejado no git log)
git rm backend/test_atividros.db
git rm frontend/src/test.jsx frontend/src/test2.jsx
git rm -r .idea
git rm "Plano de Desenvolvimento — Sistema Atividros v1.md" "Sistema atividros.md"

# 2. Atualizar o .gitignore:
#    - Remover as linhas 208-210 (/.idea/atividros.iml, /backend/atividros.db, /backend/migrations/versions/baf432e819f5_adicionando_modelos_de_pedidos.py)
#    - Adicionar regras globais limpas:
#      .idea/
#      *.db
#      *.sqlite
#      *.sqlite3
#      frontend/dist/

# 3. Versionar a migration que estava bloqueada pela linha 210 do .gitignore
git add .gitignore backend/migrations/versions/baf432e819f5_adicionando_modelos_de_pedidos.py

# 4. Remover artefatos/caches locais não rastreados no disco
Remove-Item -Force -ErrorAction SilentlyContinue backend/atividros.db, backend/.coverage
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue backend/htmlcov, backend/.pytest_cache, backend/.ruff_cache, frontend/dist

# 5. Validar árvore antes do commit da Sprint 0
git status
```

---

## 9. Matriz de Riscos e Plano de Mitigação

| Risco | Probabilidade | Impacto | Gatilho / Sintoma | Mitigação Concreta |
|---|---|---|---|---|
| **R1. Contenção / Lock de escrita no SQLite ao gerar `numero_pedido` ou baixar estoque** | Média | Alto | `OperationalError: database is locked` sob acessos simultâneos de balcão e oficina | Configurar `WAL` + `busy_timeout=5000` em `session.py`, iniciar transação com `BEGIN IMMEDIATE` no SQLite e aplicar retry exponencial (3 tentativas) em `gerar_numero_pedido` (`ADR-005`). |
| **R2. Regressão funcional ao decompor o monólito `Pedidos.jsx` (939 L)** | Alta | Alto | Quebra de criação de pedido, atualização de status ou download de PDF | Decompor primeiro os primitivos `ui/*`, manter `Pedidos.jsx` coberto por testes Vitest/RTL nos 4 fluxos principais antes de remover o código legado, e realizar smoke E2E completo no Épico 6. |
| **R3. Divergência de arredondamento (`float` JS vs `Decimal` Python)** | Média | Médio | Diferença de `R$ 0,01` entre preview da tela e valor persistido pelo backend | Adotar o backend como **fonte única da verdade** (`Decimal` `ROUND_HALF_UP`); o frontend exibe o preview retornado pela API (`POST /calculadora/*`) e exibe totais recalculados na resposta de `POST/PUT /pedidos/`. |
| **R4. Incompatibilidade DDL entre SQLite e PostgreSQL na migration V1.0** | Média | Alto | Falha de `alembic upgrade head` ao migrar para PostgreSQL (nomes de `ENUM`, `ALTER COLUMN`, `batch_alter_table`) | Usar nomes explícitos em todos os `sa.Enum(..., name="...")`, habilitar `render_as_batch=True` no `env.py` e validar `alembic upgrade head` + `pytest` contra instância PostgreSQL real (`asyncpg`) no Épico 6. |
| **R5. Quebra de testes legados bloqueando verificação contínua** | Alta | Baixo | Testes antigos esperando HTTP 400 na ruptura ou `GET` sem token | Executar a tabela de atualização planejada (§7.1.A) exatamente no épico em que cada regra muda, nunca desabilitando ou pulando testes. |
| **R6. Vazamento de `valor_sugerido` ou `preco_custo` no PDF do cliente** | Baixa | Alto | Cliente visualiza margem interna ou preço sugerido antes de desconto | Proibição explícita em `gerador_pdf.py` + teste de integração inspecionando o texto extraído do PDF garantindo ausência da string de `valor_sugerido` quando diferente de `preco_unitario`. |
| **R7. Expansão silenciosa de escopo (*Scope Creep* contra R4)** | Média | Médio | Tentativa de incluir WhatsApp, NF-e, RBAC multi-perfil, plano de corte ou integrações externas durante os sprints | Manter a Matriz MoSCoW (`PRD.md` §2) e as fronteiras (`ARQUITETURA.md` §1.1) como trava de escopo; novos pedidos fora da V1.0 entram em backlog V1.1+. |
