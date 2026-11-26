# Relatório Executivo de Decisões Autônomas e Aceite — Atividros V1.0

**Data de conclusão:** 2026-11-26  
**Repositório:** `MLiguili/sistema_atividros_2026`  
**Branch principal de entrega:** `master`  
**Escopo executado:** Documentação fundacional + Épicos 1 a 6 concluídos e validados.

---

## 1. Resumo Executivo da Entrega (Épicos 1 a 6)

O projeto **Atividros V1.0** foi estruturado, implementado, testado e integrado ponta a ponta até o **Épico 6**, respeitando integralmente o escopo aprovado no [PRD](PRD.md), [Arquitetura](ARQUITETURA.md), [Design System](DESIGN_SYSTEM.md) e [Plano de Implementação](PLANO_IMPLEMENTACAO.md).

| Épico / Sprint | Escopo Entregue | Pull Request | Issue |
| --- | --- | --- | --- |
| Documentação Base | PRD, Arquitetura, Design System e Plano de Implementação | Commit direto `8aba2fc` em `master` | — |
| **Épico 1 / Sprint 0** | Limpeza do repositório, segurança JWT/CORS/logs, `pbkdf2_sha256` (29k), Login real e `redirect` em HTTP 401 | PR `#7` | Issue `#1` |
| **Épico 2 / Sprint 1** | Remodelagem para 15 tabelas, baseline único Alembic `0b7a9f3950c1`, `asyncpg`, PRAGMAs SQLite e numeração anual atômica `YYYYNNNNN` | PR `#8` | Issue `#2` |
| **Épico 3 / Sprint 2** | Motor determinístico único (`Decimal`), calculadora quadro/vidro avulso, entrada de chapas/ajuste `m²`, filtros `?q=`/`?critico=true` e `409 Conflict` | PR `#9` | Issue `#3` |
| **Épico 4 / Sprint 3** | Pedidos com 3 eixos (`geral`/`producao`/`financeiro`), pagamentos parciais e estorno, Baixa Assistida, snapshots imutáveis, Dashboard e PDF único sanitizado | PR `#10` | Issue `#4` |
| **Épico 5 / Sprints 4–5** | CSS modular em 3 camadas (`.at-*`, WCAG AA), 12 primitivos acessíveis, decomposição de `Pedidos.jsx` (164 linhas) em 8 componentes + Kanban 6 colunas e suíte Vitest/RTL | PR `#11` | Issue `#5` |
| **Épico 6 / Sprint 6** | Jornada E2E balcão+oficina, validação real em PostgreSQL 16 via `asyncpg`, cobertura backend >= 80% (`91.67%`) e este relatório | PR `#12` (em fechamento) | Issue `#6` |

---

## 2. Registro de Decisões Autônomas Tomadas

### 2.1 Escopo de Produto e Regras de Negócio
1. **Unidades de estoque e conversão:** Molduras controladas por quantidade inteira de barras (com cálculo auxiliar de `R$/m` no cadastro e custo/barra no modal); vidros e fundos controlados em área contínua (`m²` com 4 casas decimais) alimentados por conversor de entrada em chapas (`quantidade_chapas × largura_cm × altura_cm`).
2. **Sem distinção de preço entre tipos de cliente e sem cálculo de aparas:** Conforme definido na fase de descoberta e travado no PRD, não há diferenciação de tabela por perfil de cliente nem otimizador de plano de corte/retalhos na V1.0.
3. **Máquina de estados em 3 eixos independentes:** Separação explícita de `status_geral` (`rascunho`, `confirmado`, `entregue`, `arquivado`, `cancelado`), `status_producao` (`pendente`, `aguardando_material`, `na_fila`, `em_producao`, `embalando`, `pronto_entrega`) e `status_financeiro` (`sem_pagamento`, `pagamento_parcial`, `pago_total`, `estornado`).
4. **Confirmação automática no 1º pagamento:** Registrar qualquer pagamento positivo em um pedido `rascunho` o promove automaticamente para `confirmado`, emitindo evento de auditoria e liberando a ordem no Kanban.
5. **Política não bloqueante para preço abaixo do sugerido e ruptura de estoque:**
   - Preço praticado abaixo de `valor_sugerido` emite alerta persistente na UI e marca internamente o item/pedido, mas **não bloqueia** o salvamento.
   - Ruptura de estoque na Baixa Assistida permite ajuste manual em steppers (`>= 44×44px`) e **não bloqueia** a entrada em produção mesmo com saldo projetado negativo, registrando `alertas_ruptura` para compra posterior.
6. **Bloqueio de entrada manual em `em_producao`:** A transição para `em_producao` é aceita exclusivamente via endpoint `POST /pedidos/{id}/baixa-estoque`, garantindo rastreabilidade dos insumos debitados.
7. **PDF único e proteção de margens:** Um único layout A4 é gerado tanto para orçamento quanto para confirmação/entrega, omitindo estritamente `valor_sugerido`, `abaixo_do_sugerido` e `preco_custo`, com sanitização Latin-1 no gerador FPDF2 para evitar falhas tipográficas com acentuação e símbolos (`•`, `—`, `→`, `×`).

### 2.2 Decisões de Arquitetura, Banco e Segurança
1. **Baseline único Alembic (`0b7a9f3950c1_v1_0_schema_inicial.py`):** Como não havia usuários em produção antes da V1.0, as 5 migrations legadas e fragmentadas foram consolidadas em um baseline limpo das 15 tabelas com `render_as_batch=True` para compatibilidade simultânea SQLite + PostgreSQL.
2. **Precisão monetária e dimensional:** Todos os cálculos de cálculo de quadro, área, conversão de chapas e totais de pedido no backend usam `decimal.Decimal` com `ROUND_HALF_UP`, eliminando erros binários de ponto flutuante.
3. **Numeração sequencial anual atômica (`YYYYNNNNN`):** Implementada em `app/services/sequencia.py` via `INSERT INTO sequencia_numeracao ... ON CONFLICT (ano) DO UPDATE ... RETURNING ultimo_valor`, compatível tanto com SQLite (com retry para lock operacional e `BEGIN IMMEDIATE`) quanto com PostgreSQL.
4. **Fallback determinístico de fuso horário no Windows:** Como o ambiente Python Windows sem pacote `tzdata` gera `ZoneInfoNotFoundError` ao carregar `"America/Sao_Paulo"`, foi aplicado fallback seguro para `timezone(timedelta(hours=-3))` em `sequencia.py` e `dashboard.py`.
5. **Async SQLAlchemy + Greenlet + `asyncpg`:**
   - Em `services/pedido.py`, as relações são manipuladas explicitamente antes do `flush` e recarregadas com `populate_existing=True`, evitando `MissingGreenlet` em runtime assíncrono.
   - Em `tests/conftest.py`, foi adotado `NullPool` quando `TEST_DATABASE_URL` não é SQLite, evitando reutilização de conexões `asyncpg` presas a event loops encerrados pelo `pytest-asyncio`.
   - Em `backend/pyproject.toml`, foi configurado `concurrency = ["greenlet", "thread"]` e `fail_under = 80` no `coverage`.
6. **Saneamento de segurança (Sprint 0):** Remoção de logs de senha em texto puro, remoção do placeholder de hash inseguro em `create_admin.py` (`pbkdf2_sha256` com 29.000 iterações), proteção autenticada de todas as rotas de estoque/tabelas/pedidos/clientes/dashboard e validação explícita de `SECRET_KEY` em produção.

### 2.3 Decisões de Interface e Experiência (Frontend)
1. **Substituição integral do glassmorphism:** Adoção de superfícies sólidas em slate com tokens CSS em 3 camadas (`src/styles/tokens.css`, `base.css`, `layout.css`, `components.css` e `pages/*.css`), alcançando contraste WCAG AA (`#042F2E` sobre `#10B981`, eliminando `#FFF` sobre `#10B981` de baixo contraste e removendo `--card-bg`/`--warning`).
2. **Kanban operacional enxuto em 6 colunas:** Exibição exclusiva de pedidos `confirmado` nas 6 etapas de oficina (`pendente` até `pronto_entrega`), mantendo `entregue`/`arquivado`/`cancelado`/`rascunho` na visão de Lista; no mobile (`<= 767px`), seletores em abas com contadores por etapa.
3. **Decomposição de `Pedidos.jsx`:** O monólito original (~939 linhas) foi substituído por um orquestrador de **164 linhas** apoiado em 8 componentes especializados sob `frontend/src/components/pedidos/`.
4. **Remoção total de diálogos nativos:** `window.alert` e `window.confirm` foram substituídos por `Dialog`, `ConfirmDialog` (com foco inicial seguro no botão **Cancelar**) e sistema global de Toasts.
5. **Fluxo GitHub (`master` vs `main`):** Detectado durante o fechamento que o repositório remoto mantinha `main` como branch padrão vazia/legada enquanto toda a base V1.0 evoluiu em `master`. Todos os PRs foram abertos com `--base master` e as issues `#1`–`#6` requerem fechamento explícito até a troca da branch padrão no GitHub.

---

## 3. Evidências Verificadas da Suite Final

Todos os comandos abaixo foram executados sobre o estado final do código após as últimas edições:

- **Backend (SQLite `:memory:` + Coverage + Ruff):**
  - `poetry run pytest --cov=app --cov-report=term-missing`: **123 passed in 15.82s** | Cobertura total: **91.67%** (`fail_under = 80` atingido; zero falhas, zero skipped).
  - `poetry run ruff check app tests scripts`: **`All checks passed!`** (0 erros).
- **Backend contra PostgreSQL 16 real em Docker (`postgres:16-alpine` + `asyncpg`):**
  - `poetry run alembic upgrade head`: upgrade `-> 0b7a9f3950c1, v1_0_schema_inicial` executado com sucesso.
  - `poetry run alembic check`: **`No new upgrade operations detected.`**
  - `poetry run pytest tests/integration/ --no-cov`: **41 passed in 14.68s** (zero falhas, zero erros). Container efêmero removido após o teste.
- **Frontend (Verificação estática + Vitest + ESLint + Vite Build):**
  - Checagem estática em `frontend/src/**/*.jsx`: **0 ocorrências** de `<style>`, `window.alert`, `window.confirm`, `--card-bg`, `--warning`, `/calculadora/simular` e cores hex literais; `Pedidos.jsx` com **164 linhas** (`<= 180`).
  - `npm test -- --run`: **6 test files passed, 9 tests passed**.
  - `npm run lint`: **0 erros**.
  - `npm run build`: **`built in 3.42s`** (`dist/` gerado sem erros).

---

## 4. Recomendações de Go-Live em Produção

1. **GitHub Default Branch:** Nas configurações do repositório `MLiguili/sistema_atividros_2026` (`Settings -> Branches`), alterar a default branch de `main` para `master` (e remover a branch `main` legada caso não seja mais necessária) para que futuros `Closes #N` em PRs fechem issues automaticamente.
2. **Variáveis de Ambiente Obrigatórias:** Definir em produção `SECRET_KEY` forte e aleatória (comprimento >= 32 bytes), `DATABASE_URL` apontando para o PostgreSQL gerenciado (`postgresql+asyncpg://...`), `CORS_ORIGINS` restrito ao domínio real do frontend e `DEBUG=false`.
3. **Bootstrap Inicial do Banco:** Executar `poetry run alembic upgrade head` e criar o primeiro usuário operacional via `poetry run python scripts/create_admin.py` com senha forte.
4. **Cadastro Rápido na Tela de Pedidos (melhoria V1.0.1 sugerida):** Em `PedidoForm.jsx`, caso o atendente use o modal "Cadastro Rápido de Cliente", incluir também os campos `sobrenome` e `telefone` obrigatórios no esquema `CriarCliente` do backend antes de habilitar uso intenso desse atalho.
