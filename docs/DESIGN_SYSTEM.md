# Design System e Fluxos UX/UI — Sistema Atividros (V1.0)

> **Versão:** 1.0  
> **Status:** Especificação Aprovada para Implementação (Frontend React + PDF Único)  
> **Base Funcional:** `docs/PRD.md` (v2.0)  
> **Baseline Arquitetural:** `docs/ARQUITETURA.md` (v1.0)  
> **Referência Estrutural:** `C:\FluxeScripts\Fluxe\fluxeOS\design\` *(adaptada com filtros de escopo R4)*  
> **Contexto de Uso:** Aplicação Web Responsiva Interna — Loja Única (**Balcão Desktop** + **Oficina Celular/Tablet**)

---

## 1. Visão Geral, Contextos de Uso e Limites de Escopo

O **Design System Atividros (V1.0)** estabelece a linguagem visual, a arquitetura de tokens, o catálogo de componentes e os fluxos operacionais da interface web do sistema Atividros e de seu documento PDF único. Seu propósito é transformar o MVP atual (`frontend/src/`) em uma interface rápida, legível e livre de inconsistências visuais ou contratuais para uma operação simultânea de 1 a 2 pessoas em dois ambientes físicos distintos:

| Contexto Físico | Dispositivo Alvo | Fluxos Primários | Restrições Ergonômicas e Ambientais |
|---|---|---|---|
| **Balcão de Atendimento** | Desktop / Notebook (`>= 1024 px`) | Orçamentos rápidos na Calculadora, cadastro de clientes, criação/edição de pedidos, recebimento de pagamentos, impressão/download de PDF, gestão de estoque e tabelas de preço. | Iluminação comercial intensa (risco de reflexo), atendimento presencial ou via WhatsApp exigindo digitação ágil pelo teclado (`Tab`/`Enter`), números financeiros e medidas em `tabular-nums` para evitar erro de leitura ao vivo com o cliente. |
| **Oficina / Bancada** | Celular (`320–767 px`) e Tablet (`768–1023 px`) | Consulta de medidas de corte (obra, paspatour, vidro, molduras, quadro final), avanço no Kanban de produção, **Baixa de Estoque Assistida** (`em_producao`) e conferência rápida de prazos. | Leitura rápida à distância na bancada, iluminação variável/poeira, uso frequente com **uma mão, mãos ocupadas ou luvas**, **ausência de hover** (`touch-first`) e conexão Wi-Fi/4G intermitente. |

### Limites Explícitos da V1.0 (Aderência ao PRD e Filtros R4)
- **100% Web Responsivo:** SPA em **React 19 + Vite** consumindo API REST FastAPI; não há shell desktop nativo (Tauri/Electron), chrome de janela simulado nem gate de plataforma macOS.
- **Domínio Puro de Vidraçaria e Molduraria:** Toda a interface reflete exclusivamente o domínio determinístico do Atividros (`Obra`, `Paspatour`, `Moldura`, `Vidro`, `Fundo`, `Suplemento`, `Calculadora`, `Pedidos/Orçamentos`, `Pagamentos`, `Baixa Assistida` e `PDF Único`). Não existem pipelines de IA/LLM, captura de áudio, transcrição ou telas de consultoria.
- **Saída Documental Única:** Gera exclusivamente **1 PDF A4 unificado** (`ORÇAMENTO` ou `PEDIDO / ORDEM DE SERVIÇO` via `GET /pedidos/{id}/pdf`), sem exportação PPTX/DOCX.
- **Loja Única Interna:** Sem multi-tenancy, sem portal externo do cliente e sem RBAC granular na V1.0 (`PRD.md` §1–§2).

---

## 2. Registro de Decisões de Design (`DD-001` .. `DD-010`)

| ID | Decisão | Alinhamento | Status |
|---|---|---|---|
| **DD-001** | **Stack Visual:** CSS modular customizado em 3 camadas (`src/styles/`) + primitivos React acessíveis nativos (sem Tailwind/shadcn) | `package.json`, `index.css` | Aprovada |
| **DD-002** | **Tema Único V1.0:** Escuro Operacional de Alto Contraste (*High-Contrast Slate*), substituindo *glassmorphism* turvo e corrigindo falhas WCAG | `index.css`, WCAG 2.2 AA | Aprovada |
| **DD-003** | **UX de `mao_de_obra`:** Entrada em **`R$ por unidade`** com preview unitário e subtotal expandido quando `quantidade > 1` | `ADR-002` | Aprovada |
| **DD-004** | **UX de `preco_custo` de Moldura:** Input canônico em **`R$/m`** + calculadora auxiliar opcional *"Calcular a partir do custo da barra"* | `ADR-001` | Aprovada |
| **DD-005** | **Separação das Famílias Semânticas de Cor + "Nunca Só Cor"** para os 3 eixos (`status_geral`, `status_producao`, `status_financeiro`) | `PRD §3.4`, WCAG 1.4.1 | Aprovada |
| **DD-006** | **Alertas Não-Bloqueantes vs. Erros Bloqueantes** (preço abaixo do sugerido em amarelo interno; ruptura de estoque em aviso destacado sem bloqueio) | `PRD §3.3-3.4`, `ADR-008` | Aprovada |
| **DD-007** | **Escala Tipográfica em `rem` (8 passos) + `tabular-nums` obrigatório** para medidas (`cm`, `m`, `m²`), valores `R$` e códigos | `PRD §3.2-3.6` | Aprovada |
| **DD-008** | **Espaçamento em múltiplos de `4 px` e Alvos de Toque `>= 44×44 px` na Oficina** (mínimo `24×24 px` WCAG 2.5.8 em ações secundárias desktop) | `PRD §1`, WCAG 2.5.8 | Aprovada |
| **DD-009** | **Navegação Responsiva Dual + Acesso a Tabelas de Preço** (Sidebar fixa no balcão; Header + Drawer + Kanban por abas de estágio na oficina) | `Layout.jsx`, `PRD §3.2.D` | Aprovada |
| **DD-010** | **Matriz de Confirmação por Risco (foco inicial em Cancelar)** e Baixa Assistida obrigatória ao mover para `em_producao` | `ARQUITETURA §4.2-4.3` | Aprovada |

### DD-001 — Decisão da Stack Visual: CSS Modular em 3 Camadas + Primitivos React Próprios
- **Contexto e Evidência Real (`frontend/`):**
  - `frontend/package.json` possui exclusivamente `react ^19.2.4`, `react-dom ^19.2.4`, `react-router-dom ^7.13.1`, `axios ^1.13.6`, `date-fns ^4.1.0` e `lucide-react ^0.577.0`. **Não** há Tailwind CSS, PostCSS/Autoprefixer, shadcn/ui, Radix UI ou biblioteca de testes instalados.
  - `frontend/src/index.css` possui **499 linhas** com variáveis `:root` já definidas (`--bg-primary`, `--bg-secondary`, `--accent-primary`, `--danger`), porém com **regras duplicadas** (`h1/h2/h3` em L48-55 e L96-103; `.grid-auto/.grid-2/.grid-3` em L58-74 e L237-253; media queries conflitantes em `1400px` L367 e `1440px` L491).
  - A pasta `frontend/src/styles/` já existe no repositório, atualmente **vazia**.
  - Todos os principais arquivos `.jsx` contêm blocos `<style>` inline duplicados (`Layout.jsx:70-284`, `Calculadora.jsx:237-240`, `Clientes.jsx:164-175`, `Estoque.jsx:169-198`, `Pedidos.jsx:849-934`), e **bugs graves de tokens ausentes**: `Clientes.jsx:169`, `Estoque.jsx:190` e `Pedidos.jsx:234,304,402` referenciam `var(--card-bg)` (inexistente em `index.css`, deixando os modais transparentes), e `Pedidos.jsx:424` referencia `var(--warning)` (também inexistente).
- **Decisão:** **Manter e evoluir CSS customizado modular com tokens em 3 camadas em `src/styles/`** (`tokens.css`, `base.css`, `layout.css`, `components.css` e folhas por domínio) utilizando prefixo semântico `.at-*` (nomenclatura BEM adaptada `at-<bloco>[__elemento][--variante]`), combinado com **primitivos React de acessibilidade próprios em `src/components/ui/`** (usando `<dialog>` nativo HTML5 com `showModal()` para trap de foco e `Esc`, roving tabindex em abas e `aria-live` para toasts).
- **Alternativas Descartadas:**
  1. *Migrar para Tailwind CSS + shadcn/ui:* exigiria instalar Tailwind + toolchain CSS, configurar `@/` path aliases, instalar pacotes `@radix-ui/*` (que têm atritos de peer-dependencies/ref em React 19 sem wrapper atualizado), e reescrever 100% dos 5 módulos e `index.css` sem ganho funcional para uma aplicação interna de 6 rotas.
  2. *Adotar CSS-in-JS (`styled-components` / `emotion`):* adiciona custo de runtime, incompatibilidade com SSR/React 19 compiler e mantém CSS acoplado dentro dos `.jsx`.
  3. *Manter `index.css` monolítico + `<style>` inline:* perpetua colisões de seletores (`.btn-icon`, `.modal-content`), tokens quebrados (`--card-bg`, `--warning`) e impossibilita governança de contraste.
- **Impacto na Refatoração de `Pedidos.jsx` (939 linhas):** A remoção de todo `<style>` inline e a extração dos primitivos (`Dialog`, `StatusBadge`, `Card`, `DataTable`, `AlertBanner`, `ConfirmDialog`, `ToastRegion`) reduzem `Pedidos.jsx` a um orquestrador de visão/rotas, separando `PedidoForm`, `PedidoDetalhe`, `KanbanBoard`, `ModalBaixaEstoque` e `ModalPagamentos` em componentes testáveis e sem CSS acoplado.
- **Regras Estritas de Implementação (Obrigatórias):**
  1. **PROIBIDO** usar tags `<style>` dentro de arquivos `.jsx`.
  2. **PROIBIDO** usar cores hex literais (`#...`) ou `rgb()/rgba()` em arquivos de componentes (`.jsx`) ou em `components.css` — **toda cor deve referenciar um token semântico `var(--at-color-*)`**.
  3. **PROIBIDO** usar `style={{ ... }}` inline para definir cores, fontes, raios ou espaçamentos fora da escala (permitido apenas para valores puramente dinâmicos calculados em runtime, como largura percentual de progresso).

### DD-002 — Tema e Contraste: Escuro Operacional de Alto Contraste (*High-Contrast Slate*)
- **Contexto:** O sistema atual já utiliza tema escuro em Slate (`#0f172a` / `#1e293b`) com acento esmeralda (`#10b981`), porém apresenta **3 falhas críticas de legibilidade e acessibilidade** para o balcão e a oficina:
  1. `.btn-primary` atual (`index.css:122-123`) usa texto branco (`#FFFFFF`) sobre `#10B981`, resultando em razão de contraste **2,54:1** (reprovado na WCAG AA que exige `>= 4,5:1`; mesmo no hover `#059669`, cai para **3,77:1**).
  2. Badges atuais (`Dashboard.jsx:64`, `Pedidos.jsx:191`) usam texto `#FFFFFF` sobre fundos claros/saturados (`#f59e0b`, `#06b6d4`, `#10b981`, `#22c55e`), todos abaixo de `4,5:1`.
  3. Uso excessivo de `backdrop-filter: blur(12px)` e `rgba(30, 41, 59, 0.7)` em `.card` reduz nitidez sob reflexo de vitrine no balcão e consome GPU desnecessariamente em celulares de entrada na oficina.
- **Decisão:** Adotar na V1.0 um **Tema Único Escuro Operacional de Alto Contraste** (`#0B1120` canvas / `#131C2E` surface / `#1B2740` elevated), preservando a identidade visual esmeralda do Atividros, porém:
  - Substituindo fundos translúcidos (*glassmorphism*) por **superfícies sólidas com borda nítida de `1 px`** (`border-subtle` e `border-strong` `>= 3:1`);
  - Corrigindo o texto sobre botão primário esmeralda (`#10B981`) para tinta escura de alto contraste **`#042F2E` (`5,70:1`)** e hover `#34D399` com `#042F2E` (`7,53:1`);
  - Elevando `--at-color-text-secondary` para `#CBD5E1` (`11,47:1` sobre surface) e `--at-color-text-muted` para `#94A3B8` (`6,64:1` sobre surface);
  - Estruturando `tokens.css` em 3 camadas para que um futuro tema claro (V1.1+) possa ser habilitado via `[data-theme="light"]` sem alterar componentes.
- **Alternativas Descartadas:** Forçar dois temas obrigatórios (claro + escuro) já na V1.0 — descartada porque duplica a matriz de QA visual sem requisito no `PRD.md` (conforme filtro R4).

### DD-003 — Padrão de UX para `mao_de_obra` na Calculadora (`ADR-002`)
- **Contexto:** `PRD.md` §3.3 deixa em aberto se `mao_de_obra` entra por unidade ou valor fixo total. `ARQUITETURA.md` (`ADR-002`) padronizou **`R$ por unidade`** para preservar a invariante `ItemPedido.subtotal = preco_unitario * quantidade`.
- **Decisão:** Na Calculadora, o campo **`Mão de obra (R$/un)`** aparece na seção de Materiais/Serviços com:
  - Rótulo explícito: `Mão de obra (R$/un)`;
  - Hint fixo abaixo do input: `Somada ao valor unitário de cada quadro`;
  - Input numérico decimal (`min="0"`, `step="0.01"`, placeholder `0,00`, default `0.00`, alinhado à direita em `tabular-nums`);
  - **Comportamento no Painel de Resultado:**
    - Quando `quantidade === 1`: exibe linha única `Mão de obra (1 un) ....... R$ 25,00`.
    - Quando `quantidade > 1` (ex.: `2`): exibe claramente na composição unitária `Mão de obra (R$ 25,00/un × 2) ....... R$ 50,00` e mantém destaque visual equivalente para **Valor unitário sugerido** e **Total sugerido (× 2)**.
- **Consequência:** Ao clicar em **"Adicionar ao Pedido"**, o operador pode alterar a `quantidade` diretamente no pedido sem gerar dízimas periódicas nem distorcer o preço unitário.

### DD-004 — Padrão de UX para `preco_custo` de Moldura (`ADR-001`)
- **Contexto:** `Estoque.jsx:328-334` exibe hoje os rótulos ambíguos `Preço de Venda (R$) *` e `Preço de Custo (R$) *` sem unidade. `ADR-001` padronizou ambos em **`R$/m`**.
- **Decisão:**
  - Os campos principais do formulário de Moldura passam a exibir explicitamente a unidade: **`Preço de Custo (R$/m) *`** e **`Preço de Venda (R$/m) *`**.
  - Logo abaixo do campo `Preço de Custo (R$/m)`, disponibilizar um botão discreto/expansível (`link` / `ghost` sm): **`Calcular a partir do custo da barra`**.
  - Ao expandir, exibe um mini-bloco auxiliar (não enviado à API):
    - Input `Custo da barra inteira (R$)` + leitura do `Tamanho da Barra (m)` já preenchido no formulário;
    - Cálculo instantâneo: `R$ <custo_barra / tamanho_barra>/m` com botão **`Aplicar ao custo/m`** que preenche `preco_custo` arredondado em 2 casas decimais;
    - Se `tamanho_barra <= 0` ou vazio, exibe hint inline `"Informe primeiro o Tamanho da Barra (m)"` sem bloquear o campo manual.
  - Exibir também um indicador informativo passivo de margem unitária abaixo dos preços: `Margem: R$ X,XX/m (Y%)`.

### DD-005 — Três Famílias Semânticas de Cor + Regra "Nunca Só Cor" (WCAG 1.4.1)
- **Contexto:** Hoje `Dashboard.jsx:53-57` e `Pedidos.jsx:180-184` usam cores ad-hoc que colidem entre si (ex.: `pendente` amarelo = `sinal_recebido` amarelo; `pronto_entrega` verde = `entregue` verde = `pago_total` verde; `cancelado` vermelho = `sem_pagamento` vermelho), gerando ambiguidade nos cards de pedido com 3 badges simultâneos.
- **Decisão:** Separar estritamente as famílias semânticas de cor e exigir **ícone + rótulo textual explícito + traço visual distinto** em todos os badges dos 3 eixos:
  1. **Eixo 1 — Status Geral (`status_geral`):** comunica ciclo comercial (`rascunho`, `confirmado`, `entregue`, `arquivado`, `cancelado`). Usa contorno **pontilhado/tracejado** para `rascunho` e **texto tachado ou ícone de bloqueio** para `cancelado`.
  2. **Eixo 2 — Status de Produção (`status_producao`):** comunica estágio da oficina (`pendente`, `aguardando_material`, `na_fila`, `em_producao`, `embalando`, `pronto_entrega`). No Kanban, o eixo é comunicado pela **própria coluna** (e cor da faixa superior da coluna), evitando redundância dentro do card.
  3. **Eixo 3 — Status Financeiro (`status_financeiro`):** comunica situação de pagamento (`sem_pagamento`, `pagamento_parcial`, `pago_total`, `estornado`). Sempre acompanhado de ícone monetário/estado e, quando aplicável, do valor do `saldo_devedor` em `tabular-nums`.
  4. **Feedback de Sistema (`feedback.*`):** exclusivo para alertas, validações, toasts e rupturas de estoque (`success`, `warning`, `danger`, `info`).

### DD-006 — Alertas Não-Bloqueantes vs. Erros Bloqueantes
- **Decisão:** Distinguir visual e comportamentalmente dois níveis de severidade:
  - **Alerta Não-Bloqueante (`at-callout--warning` / âmbar `#FBBF24` sobre `#2B200B`):** usado exclusivamente para (1) preço praticado abaixo do sugerido na edição de item (`abaixo_do_sugerido: true`) e (2) ruptura projetada de estoque (`em_ruptura: true` / saldo `< 0`) no Modal de Baixa Assistida e no Dashboard. **Nunca desabilita o botão de salvar/confirmar.**
  - **Erro Bloqueante (`at-callout--danger` / rosa-vermelho `#FB7185` sobre `#2E111B` + borda `2 px`):** usado para erros de validação de campo (`aria-invalid="true"`), tentativas inválidas de transição (ex.: editar pedido `confirmado`/`cancelado`, pagamento maior que `saldo_devedor`) e falhas de rede/API (`400/401/409/422/500`).

### DD-007 — Escala Tipográfica em `rem` + `tabular-nums` Obrigatório
- **Decisão:** Reduzir tamanhos soltos (`0.65rem`, `0.7rem`, `0.8rem`, `0.85rem`, `0.9rem`, `0.95rem`, `1.1rem`, `2.5rem`) para uma **escala fixa de 8 passos em `rem`** (`xs: 0.75rem / 12px` até `3xl: 2rem / 32px`), com corpo padrão em **`14 px` (`0.875rem`)** no desktop e mínimo absoluto de `12 px` (`xs`) apenas para metadados/badges secundários (medidas de corte na oficina devem usar no mínimo `14 px` / `base` ou `16 px` / `md`).
- **Regra `tabular-nums`:** Toda exibição de medida (`40,00 × 50,00 cm`, `2,6800 m`, `0,3000 m²`), preço (`R$ 414,30`), contagem de barras e número de pedido (`#202600001`) deve aplicar `font-variant-numeric: tabular-nums`.

### DD-008 — Espaçamento em Múltiplos de `4 px` e Alvos de Toque na Oficina
- **Decisão:** Adotar escala de `4 px` (`space-1` = 4px até `space-16` = 64px), 5 raios (`4, 8, 12, 16, 999 px`), elevação baseada em borda nítida + sombra apenas em camadas flutuantes, e regra dupla de alvo de toque:
  - **Oficina (`<= 1023 px` / `pointer: coarse`) e ações principais de formulário:** altura mínima **`44 × 44 px`** (ex.: botões `-/+` no Modal de Baixa Assistida, seletor de coluna no Kanban mobile, botões de avanço de etapa).
  - **Ações secundárias densas em tabela desktop:** mínimo **`28 × 28 px`** (acima do piso `24 × 24 px` da WCAG 2.5.8) com espaçamento mínimo de `8 px` entre botões adjacentes.

### DD-009 — Navegação Dual e Desacoplamento do Container Duplicado
- **Evidência Real:** `App.jsx:44` envolve o `<Layout>` dentro de `<div className="container" style={{ paddingTop: '2rem' }}>`, e `Layout.jsx:65` abre outro `<div className="container fade-in">`, duplicando padding lateral no desktop e comprimindo a tela no mobile. Além disso, `Layout.jsx` não possui acesso às **Tabelas de Preço** (`Vidro`, `Fundo`, `Paspatour`).
- **Decisão:**
  1. Remover o wrapper `.container` de `RotaProtegida` em `App.jsx` — o controle de largura e padding pertence exclusivamente a `Layout`.
  2. Incluir o item de navegação **`Tabelas de Preço`** (rota `/precos` ou sub-seção dedicada em `/estoque/precos` — **padronizado na rota `/precos` no menu lateral** com ícone `Tags`, mantendo link cruzado a partir de Estoque e Calculadora).
  3. **Balcão Desktop (`>= 1024 px`):** Sidebar lateral fixa de `240 px` (`--at-size-sidebar`).
  4. **Tablet (`768–1023 px`) e Oficina Mobile (`<= 767 px`):** Header superior compacto (`56 px`) + Drawer lateral acionado por botão com `aria-expanded` e fechamento via `Esc` + barra de atalho rápido opcional nas telas operacionais (Calculadora / Pedidos).

### DD-010 — Confirmação por Nível de Risco e Fluxo Seguro de Baixa Assistida
- **Decisão:**
  - Eliminar todos os `window.alert()` e `window.confirm()` nativos existentes em `App.jsx:18`, `Calculadora.jsx:48,65`, `Clientes.jsx:75` e `Pedidos.jsx:92,114,547`.
  - Adotar `ConfirmDialog` (`at-dialog--sm`) para ações destrutivas (excluir cliente, excluir item de estoque, excluir rascunho, cancelar pedido), com **botão `Cancelar` à esquerda recebendo foco inicial** e botão destrutivo à direita repetindo o verbo exato (`"Cancelar pedido"`, `"Excluir moldura"`).
  - Ao cancelar pedido com `valor_pago > 0`, exibir `at-callout--warning` dentro do diálogo alertando explicitamente sobre a necessidade de **estorno financeiro** dos `R$ X,XX` já recebidos.
  - Para mover um pedido para `em_producao`, **jamais** permitir troca direta por `<select>`: o botão/ação abre obrigatoriamente o **Modal de Baixa de Estoque Assistida** (`GET /pedidos/{id}/previsao-baixa` → `POST /pedidos/{id}/baixa-estoque`).

---

## 3. Arquitetura de Tokens em 3 Camadas

### 3.1 Estrutura Alvo de Arquivos CSS (`frontend/src/styles/`)

```text
frontend/src/styles/
├── tokens.css       # Camada 1 (Primitivos), Camada 2 (Semânticos) e Camada 3 (Tema :root)
├── base.css         # Reset, body, tipografia base, tabular-nums, foco global, prefers-reduced-motion
├── layout.css       # Shell (.at-app, .at-sidebar, .at-mobile-header, .at-main, .at-container, .at-grid*)
├── components.css   # Primitivos (.at-btn, .at-card, .at-input, .at-table, .at-badge, .at-dialog, .at-callout, .at-toast, .at-state)
└── pages/
    ├── pedidos.css      # Kanban responsivo (6 colunas), timeline de eventos, barra de totais
    ├── calculadora.css  # Grid 2 colunas balcão + preview dimensional de camadas
    └── estoque.css      # Abas de estoque + conversor de chapas m² + tabelas de preço
```

### 3.2 Migração e Correção Explícita dos Tokens Quebrados (`index.css` Atual → V1.0)

| Token Atual / Quebrado | Ocorrência Real no Código | Problema Identificado | Token Canônico V1.0 |
|---|---|---|---|
| `var(--card-bg)` | `Clientes.jsx:169`, `Estoque.jsx:190`, `Pedidos.jsx:234,304,402` | **Token inexistente** em `index.css`; modais renderizavam sem fundo sólido. | `var(--at-color-bg-elevated)` (`#1B2740`) *(manter alias temporário `--card-bg: var(--at-color-bg-elevated)` apenas durante transição, se necessário)* |
| `var(--warning)` | `Pedidos.jsx:424` | **Token inexistente** em `index.css`; texto de alerta caía para cor herdada. | `var(--at-color-feedback-warning-fg)` (`#FBBF24`) |
| `--glass-bg` / `--glass-border` | `index.css:12-13`, `.card`, `.btn-glass` | Translucidez (`rgba(30,41,59,0.7)`) e borda fraca (`10%` branco) prejudicam contraste WCAG 1.4.11 (`< 1,5:1`). | `--at-color-bg-surface` (`#131C2E`), `--at-color-border-subtle` (`#24324D`) e `--at-color-border-strong` (`#64748B`, `3,58:1`) |
| `--text-secondary: #94a3b8` | `index.css:7` | Contraste reduzido sobre fundos elevados em ambiente iluminado de loja. | `--at-color-text-secondary: #CBD5E1` (`11,47:1` em surface) e `--at-color-text-muted: #94A3B8` (`6,64:1` em surface) |
| `.btn-primary` (`#FFF` em `#10B981`) | `index.css:121-124` | Contraste de **2,54:1** (reprovado WCAG AA). | `--at-color-action-primary-bg: #10B981` + `--at-color-action-primary-fg: #042F2E` (**5,70:1**) |

### 3.3 Camada 1 — Tokens Primitivos (`tokens.css`)

```css
:root {
  /* Neutros Slate (Base do Tema Operacional) */
  --at-prim-slate-950: #0B1120;
  --at-prim-slate-925: #0E1729;
  --at-prim-slate-900: #101829;
  --at-prim-slate-850: #131C2E;
  --at-prim-slate-825: #1E293B;
  --at-prim-slate-800: #1B2740;
  --at-prim-slate-750: #24324D;
  --at-prim-slate-600: #475569;
  --at-prim-slate-500: #64748B;
  --at-prim-slate-400: #94A3B8;
  --at-prim-slate-300: #CBD5E1;
  --at-prim-slate-200: #E2E8F0;
  --at-prim-slate-50:  #F8FAFC;

  /* Marca & Ação (Esmeralda Atividros) */
  --at-prim-emerald-950: #042F2E;
  --at-prim-emerald-900: #0B2922;
  --at-prim-emerald-600: #059669;
  --at-prim-emerald-500: #10B981;
  --at-prim-emerald-400: #34D399;

  /* Apoio Semântico (Status & Feedback) */
  --at-prim-amber-950:    #2B200B;
  --at-prim-amber-500:    #F59E0B;
  --at-prim-amber-400:    #FBBF24;
  --at-prim-orange-950:   #2C1B0E;
  --at-prim-orange-300:   #FDBA74;
  --at-prim-sky-950:      #0F2436;
  --at-prim-sky-400:      #38BDF8;
  --at-prim-sky-300:      #7DD3FC;
  --at-prim-blue-950:     #14223B;
  --at-prim-blue-300:     #93C5FD;
  --at-prim-navy-850:     #1A2232;
  --at-prim-violet-950:   #20193B;
  --at-prim-violet-300:   #C4B5FD;
  --at-prim-teal-950:     #0B2828;
  --at-prim-teal-700:     #0F766E;
  --at-prim-teal-300:     #5EEAD4;
  --at-prim-rose-950:     #2E111B;
  --at-prim-rose-400:     #FB7185;
  --at-prim-red-600:      #DC2626;
  --at-prim-graphite-800: #252B36;
  --at-prim-white:        #FFFFFF;
}
```

### 3.4 Camadas 2 e 3 — Tokens Semânticos e Tema (`:root`)

Componentes **só podem referenciar tokens desta seção**, nunca os tokens `--at-prim-*` nem hexadecimais literais.

```css
:root {
  /* Fundos */
  --at-color-bg-canvas:   var(--at-prim-slate-950); /* Fundo principal da página */
  --at-color-bg-subtle:   var(--at-prim-slate-925); /* Linhas alternadas, áreas internas de cards */
  --at-color-bg-sidebar:  var(--at-prim-slate-900); /* Sidebar e mobile header */
  --at-color-bg-surface:  var(--at-prim-slate-850); /* Cards, tabelas, painéis */
  --at-color-bg-elevated: var(--at-prim-slate-800); /* Modais, drawers, popovers, inputs em foco */
  --at-color-bg-hover:    rgba(248, 250, 252, 0.05);
  --at-color-bg-scrim:    rgba(11, 17, 32, 0.82);

  /* Textos */
  --at-color-text-primary:   var(--at-prim-slate-50);
  --at-color-text-secondary: var(--at-prim-slate-300);
  --at-color-text-muted:     var(--at-prim-slate-400);
  --at-color-text-disabled:  var(--at-prim-slate-500);
  --at-color-text-brand:     var(--at-prim-emerald-400);

  /* Bordas e Foco */
  --at-color-border-subtle:  var(--at-prim-slate-750);
  --at-color-border-strong:  var(--at-prim-slate-500); /* Inputs e divisores interativos (>=3:1) */
  --at-color-border-focus:   var(--at-prim-emerald-400);

  /* Ações */
  --at-color-action-primary-bg:       var(--at-prim-emerald-500);
  --at-color-action-primary-fg:       var(--at-prim-emerald-950);
  --at-color-action-primary-hover-bg: var(--at-prim-emerald-400);
  --at-color-action-secondary-bg:     var(--at-prim-slate-800);
  --at-color-action-secondary-fg:     var(--at-prim-slate-50);
  --at-color-action-danger-bg:        var(--at-prim-red-600);
  --at-color-action-danger-fg:        var(--at-prim-white);

  /* Feedback (Alertas, Toasts, Validação) */
  --at-color-feedback-success-fg:     var(--at-prim-emerald-400);
  --at-color-feedback-success-bg:     var(--at-prim-emerald-900);
  --at-color-feedback-success-border: var(--at-prim-emerald-500);

  --at-color-feedback-warning-fg:     var(--at-prim-amber-400);
  --at-color-feedback-warning-bg:     var(--at-prim-amber-950);
  --at-color-feedback-warning-border: var(--at-prim-amber-500);

  --at-color-feedback-danger-fg:      var(--at-prim-rose-400);
  --at-color-feedback-danger-bg:      var(--at-prim-rose-950);
  --at-color-feedback-danger-border:  var(--at-prim-red-600);

  --at-color-feedback-info-fg:        var(--at-prim-sky-400);
  --at-color-feedback-info-bg:        var(--at-prim-sky-950);
  --at-color-feedback-info-border:    var(--at-prim-sky-400);

  /* Badges dos 3 Eixos de Status (§3.5) */
  --at-color-status-geral-rascunho-fg:    var(--at-prim-slate-300);
  --at-color-status-geral-rascunho-bg:    var(--at-prim-slate-825);
  --at-color-status-geral-confirmado-fg:  var(--at-prim-blue-300);
  --at-color-status-geral-confirmado-bg:  var(--at-prim-blue-950);
  --at-color-status-geral-entregue-fg:    var(--at-prim-emerald-400);
  --at-color-status-geral-entregue-bg:    var(--at-prim-emerald-900);
  --at-color-status-geral-arquivado-fg:   var(--at-prim-slate-400);
  --at-color-status-geral-arquivado-bg:   var(--at-prim-navy-850);
  --at-color-status-geral-cancelado-fg:   var(--at-prim-rose-400);
  --at-color-status-geral-cancelado-bg:   var(--at-prim-rose-950);

  --at-color-status-prod-pendente-fg:     var(--at-prim-slate-300);
  --at-color-status-prod-pendente-bg:     var(--at-prim-slate-825);
  --at-color-status-prod-aguardando-fg:   var(--at-prim-orange-300);
  --at-color-status-prod-aguardando-bg:   var(--at-prim-orange-950);
  --at-color-status-prod-na-fila-fg:      var(--at-prim-sky-300);
  --at-color-status-prod-na-fila-bg:      var(--at-prim-sky-950);
  --at-color-status-prod-em-producao-fg:  var(--at-prim-violet-300);
  --at-color-status-prod-em-producao-bg:  var(--at-prim-violet-950);
  --at-color-status-prod-embalando-fg:    var(--at-prim-teal-300);
  --at-color-status-prod-embalando-bg:    var(--at-prim-teal-950);
  --at-color-status-prod-pronto-fg:       var(--at-prim-emerald-400);
  --at-color-status-prod-pronto-bg:       var(--at-prim-emerald-900);

  --at-color-status-fin-sem-fg:           var(--at-prim-rose-400);
  --at-color-status-fin-sem-bg:           var(--at-prim-rose-950);
  --at-color-status-fin-parcial-fg:       var(--at-prim-amber-400);
  --at-color-status-fin-parcial-bg:       var(--at-prim-amber-950);
  --at-color-status-fin-pago-fg:          var(--at-prim-emerald-400);
  --at-color-status-fin-pago-bg:          var(--at-prim-emerald-900);
  --at-color-status-fin-estornado-fg:     var(--at-prim-slate-200);
  --at-color-status-fin-estornado-bg:     var(--at-prim-graphite-800);
}
```

### 3.5 Separação Semântica dos 3 Eixos de Status + Regra "Nunca Só Cor" (WCAG 1.4.1)

Todos os badges de status usam o padrão `<Icon aria-hidden="true" /> + Rótulo PT-BR + Borda/Estilo Distinto`. Nenhum status depende apenas de matiz.

| Eixo (`ARQUITETURA.md`) | Valor do Enum | Rótulo Canônico na UI | Ícone (`lucide-react`) | Tokens (`fg` / `bg`) | Traço Distintivo (além da cor) |
|---|---|---|---|---|---|
| **Eixo 1 — Geral** (`status_geral`) | `rascunho` | Orçamento (Rascunho) | `FileEdit` | `#CBD5E1` / `#1E293B` | **Borda tracejada (`dashed`)** |
| **Eixo 1 — Geral** (`status_geral`) | `confirmado` | Confirmado | `CheckCircle2` | `#93C5FD` / `#14223B` | Borda sólida |
| **Eixo 1 — Geral** (`status_geral`) | `entregue` | Entregue | `PackageCheck` | `#34D399` / `#0B2922` | Borda sólida + ícone de pacote entregue |
| **Eixo 1 — Geral** (`status_geral`) | `arquivado` | Arquivado | `Archive` | `#94A3B8` / `#1A2232` | Borda pontilhada (`dotted`) |
| **Eixo 1 — Geral** (`status_geral`) | `cancelado` | Cancelado | `Ban` | `#FB7185` / `#2E111B` | **Texto com tachado opcional + ícone `Ban`** |
| **Eixo 2 — Produção** (`status_producao`) | `pendente` | Pendente | `Clock` | `#CBD5E1` / `#1E293B` | Borda tracejada |
| **Eixo 2 — Produção** (`status_producao`) | `aguardando_material` | Aguard. Material | `PackageSearch` | `#FDBA74` / `#2C1B0E` | Borda pontilhada + ícone de alerta de insumo |
| **Eixo 2 — Produção** (`status_producao`) | `na_fila` | Na Fila | `ListOrdered` | `#7DD3FC` / `#0F2436` | Borda sólida |
| **Eixo 2 — Produção** (`status_producao`) | `em_producao` | Em Produção | `Hammer` | `#C4B5FD` / `#20193B` | Borda sólida 2px à esquerda |
| **Eixo 2 — Produção** (`status_producao`) | `embalando` | Embalando | `Box` | `#5EEAD4` / `#0B2828` | Borda sólida |
| **Eixo 2 — Produção** (`status_producao`) | `pronto_entrega` | Pronto p/ Entrega | `Sparkles` | `#34D399` / `#0B2922` | Borda sólida destacada |
| **Eixo 3 — Financeiro** (`status_financeiro`) | `sem_pagamento` | Sem Pagamento | `CircleDollarSign` | `#FB7185` / `#2E111B` | Borda sólida + prefixo `R$ 0,00` ou saldo |
| **Eixo 3 — Financeiro** (`status_financeiro`) | `pagamento_parcial` | Pgto. Parcial | `Coins` | `#FBBF24` / `#2B200B` | Borda tracejada |
| **Eixo 3 — Financeiro** (`status_financeiro`) | `pago_total` | Pago Total | `BadgeCheck` | `#34D399` / `#0B2922` | Borda sólida |
| **Eixo 3 — Financeiro** (`status_financeiro`) | `estornado` | Estornado | `RotateCcw` | `#E2E8F0` / `#252B36` | **Borda pontilhada + ícone de reversão** |

> **Regra de Exclusividade:** Os enums legados `para_embalar`, `sinal_recebido` e `entregue` no eixo de produção **não existem** na V1.0. Toda renderização no frontend deve consumir exclusivamente os nomes canônicos da tabela acima.

### 3.6 Matriz de Contraste Verificada (WCAG 2.2 AA)

Razões calculadas por luminância relativa sRGB (mínimo `4,50:1` para texto normal e `3,00:1` para bordas de controle e foco):

| Grupo | Par Semântico | Frente / Fundo | Razão Calculada | Mínimo WCAG AA | Resultado |
|---|---|---|---|---|---|
| **Legado (Corrigido)** | *Antigo `.btn-primary`* | `#FFFFFF` / `#10B981` | `2,54:1` | `4,50:1` | **Reprovado no legado (corrigido)** |
| **Texto** | `text.primary` sobre `bg.surface` | `#F8FAFC` / `#131C2E` | `16,28:1` | `4,50:1` | **Passa** |
| **Texto** | `text.secondary` sobre `bg.surface` | `#CBD5E1` / `#131C2E` | `11,47:1` | `4,50:1` | **Passa** |
| **Texto** | `text.muted` sobre `bg.elevated` | `#94A3B8` / `#1B2740` | `5,81:1` | `4,50:1` | **Passa** |
| **Texto** | `text.brand` sobre `bg.surface` | `#34D399` / `#131C2E` | `8,86:1` | `4,50:1` | **Passa** |
| **Ação** | `action.primary-fg` sobre `action.primary-bg` | `#042F2E` / `#10B981` | `5,70:1` | `4,50:1` | **Passa** |
| **Ação** | `action.primary-fg` sobre `hover-bg` | `#042F2E` / `#34D399` | `7,53:1` | `4,50:1` | **Passa** |
| **Ação** | `action.danger-fg` sobre `action.danger-bg` | `#FFFFFF` / `#DC2626` | `4,83:1` | `4,50:1` | **Passa** |
| **Não-texto** | `border.strong` sobre `bg.surface` | `#64748B` / `#131C2E` | `3,58:1` | `3,00:1` | **Passa** |
| **Não-texto** | `border.strong` sobre `bg.elevated` | `#64748B` / `#1B2740` | `3,13:1` | `3,00:1` | **Passa** |
| **Não-texto** | `border.focus` sobre `bg.elevated` | `#34D399` / `#1B2740` | `7,74:1` | `3,00:1` | **Passa** |
| **Feedback** | `feedback.warning.fg` sobre `warning.bg` | `#FBBF24` / `#2B200B` | `9,57:1` | `4,50:1` | **Passa** |
| **Feedback** | `feedback.danger.fg` sobre `danger.bg` | `#FB7185` / `#2E111B` | `6,44:1` | `4,50:1` | **Passa** |
| **Feedback** | `feedback.success.fg` sobre `success.bg` | `#34D399` / `#0B2922` | `8,06:1` | `4,50:1` | **Passa** |
| **Feedback** | `feedback.info.fg` sobre `info.bg` | `#38BDF8` / `#0F2436` | `7,39:1` | `4,50:1` | **Passa** |
| **Eixos** | `geral.rascunho` / `prod.pendente` | `#CBD5E1` / `#1E293B` | `9,85:1` | `4,50:1` | **Passa** |
| **Eixos** | `geral.confirmado` | `#93C5FD` / `#14223B` | `8,81:1` | `4,50:1` | **Passa** |
| **Eixos** | `geral.arquivado` | `#94A3B8` / `#1A2232` | `6,21:1` | `4,50:1` | **Passa** |
| **Eixos** | `prod.aguardando_material` | `#FDBA74` / `#2C1B0E` | `9,80:1` | `4,50:1` | **Passa** |
| **Eixos** | `prod.na_fila` | `#7DD3FC` / `#0F2436` | `9,50:1` | `4,50:1` | **Passa** |
| **Eixos** | `prod.em_producao` | `#C4B5FD` / `#20193B` | `9,00:1` | `4,50:1` | **Passa** |
| **Eixos** | `prod.embalando` | `#5EEAD4` / `#0B2828` | `10,53:1` | `4,50:1` | **Passa** |
| **Eixos** | `fin.estornado` | `#E2E8F0` / `#252B36` | `11,53:1` | `4,50:1` | **Passa** |

### 3.7 Tipografia, Escala e Regras Numéricas

- **Famílias:**
  - `--at-font-sans`: `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif` *(carregamento progressivo; 100% legível offline via fallback do sistema)*.
  - `--at-font-mono`: `'JetBrains Mono', 'Cascadia Mono', 'Consolas', monospace` *(para códigos de moldura `M01`, números de pedido `#202600001` e linhas técnicas de corte)*.
- **Escala Tipográfica (8 passos em `rem`, base `16 px`):**

| Token | `rem` | `px` | Line-height | Uso Canônico |
|---|---|---|---|---|
| `--at-font-xs` | `0.75rem` | `12` | `1.4` | Badges de status, cabeçalhos de tabela (`th`), legendas de gráfico, hints secundários |
| `--at-font-sm` | `0.8125rem` | `13` | `1.45` | Textos de apoio, rótulos de campo, metadados de card |
| `--at-font-base` | `0.875rem` | `14` | `1.5` | Corpo padrão, linhas de tabela, inputs de formulário desktop |
| `--at-font-md` | `1rem` | `16` | `1.4` | Inputs em mobile (evita zoom automático no iOS Safari!), títulos de card, medidas de corte na oficina |
| `--at-font-lg` | `1.125rem` | `18` | `1.35` | Títulos de modal (`Dialog`), subseções |
| `--at-font-xl` | `1.375rem` | `22` | `1.25` | Títulos de seção (`h2`) e KPIs secundários |
| `--at-font-2xl` | `1.625rem` | `26` | `1.2` | `h1` no mobile (`<= 767 px`), KPIs principais do Dashboard |
| `--at-font-3xl` | `2rem` | `32` | `1.15` | `h1` de página no desktop, total sugerido em destaque na Calculadora |

- **Regra Obrigatória `.at-num` (`tabular-nums`):**
  ```css
  .at-num {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum" 1;
  }
  ```
  Deve ser aplicada obrigatoriamente em: preços (`R$ 1.240,50`), dimensões (`40,00 × 50,00 cm`), áreas (`0,3000 m²`), metragens (`2,6800 m`), quantidades de barras/chapas e números de pedido (`#202600001`).

### 3.8 Espaçamento, Raios, Elevação, Z-index, Movimento e Breakpoints

| Categoria | Tokens e Valores | Regras de Uso |
|---|---|---|
| **Espaçamento (4px)** | `space-1` (`4px`), `space-2` (`8px`), `space-3` (`12px`), `space-4` (`16px`), `space-5` (`20px`), `space-6` (`24px`), `space-8` (`32px`), `space-12` (`48px`) | Padronizar gaps, paddings de card (`16px` desktop / `12px` mobile) e margens entre seções (`24px`). |
| **Raios** | `radius-sm` (`4px`), `radius-md` (`8px`), `radius-lg` (`12px`), `radius-xl` (`16px`), `radius-pill` (`999px`) | `4px` checkboxes/tags; `8px` inputs/botões; `12px` cards/tabelas; `16px` modais; `999px` badges. |
| **Elevação & Borda** | Hierarquia primária por **borda `1px solid var(--at-color-border-subtle)`** e contraste de superfície. Sombras apenas em camadas flutuantes (`shadow-md` toasts/popovers, `shadow-overlay` modais). | Proibido `box-shadow` pesado em cards estáticos ou botões. |
| **Foco** | `outline: 2px solid var(--at-color-border-focus); outline-offset: 2px;` aplicado em `:focus-visible` | Proibido `outline: none` sem anel substituto visível. |
| **Z-index** | `sticky: 10`, `sidebar/header: 20`, `scrim/overlay: 30`, `dialog/drawer: 40`, `toast: 50` | Substitui os valores arbitrários atuais (`100`, `150`, `200`, `1000`). |
| **Movimento** | `duration-fast: 120ms`, `duration-base: 200ms`. Respeita `@media (prefers-reduced-motion: reduce)` zerando animações/transições. | Sem animações decorativas contínuas. |

#### Breakpoints Oficiais (Alinhados aos 2 Ambientes)
| Breakpoint | Faixa | Cenário Real | Comportamento Estrutural |
|---|---|---|---|
| **Oficina Mobile** | `<= 767 px` *(reflow mínimo `320 px`)* | Celular na bancada | Header fixo (`56 px`) + Drawer; grids colapsam para `1fr`; Kanban muda para **abas de estágio** (`1` coluna visível por vez em largura total); modais ocupam `100%` com padding `16px`; inputs `>= 16px` (`md`) e botões `>= 44 px`. |
| **Oficina Tablet** | `768 px – 1023 px` | Tablet compartilhado | Header + Drawer sob demanda; grids `2fr`; Calculadora empilha resultado abaixo do formulário ou em painel condensado; Kanban permite scroll suave de colunas `280 px`. |
| **Balcão Desktop** | `1024 px – 1399 px` | Monitor padrão de loja | Sidebar fixa `240 px`; Calculadora 2 colunas lado a lado; Kanban exibe colunas `272 px` com scroll horizontal limpo. |
| **Balcão Wide** | `>= 1400 px` | Monitor Full HD/QHD | Container máximo `1440 px` (remove conflito `1400px` vs `1440px` atual); KPIs do Dashboard em linha única (`6` ou `4` colunas balanceadas). |

---

## 4. Componentes, Matriz de Escolha e Inventário Real

### 4.1 Tabela "Quando Escolher Cada Componente"

| Preciso de... | Use | Não use |
|---|---|---|
| Ação principal da tela ou modal (1 por contexto) | `.at-btn--primary` | Múltiplos botões primários competindo lado a lado |
| Ação secundária ou cancelar | `.at-btn--secondary` ou `.at-btn--ghost` | Botão primário em ações neutras como "Limpar" ou "Fechar" |
| Ação discreta em linha de tabela ou card | `.at-btn--icon` com `aria-label` obrigatório | Ícone clicável sem `aria-label` nem alvo mínimo |
| Ação destrutiva (cancelar pedido, excluir item) | `.at-btn--danger` **dentro de `ConfirmDialog`** | Botão vermelho direto sem confirmação nem foco seguro |
| Escolher 1 entre 2–4 opções rápidas (ex.: Tipo de Item, Kanban/Lista) | `.at-segmented` (`aria-pressed`) | `<select>` ocultando opções frequentes de balcão |
| Trocar seção dentro da mesma página (ex.: abas do Estoque) | `.at-tabs` (`role="tablist"`, setas + roving tabindex) | Abas para passos sequenciais de wizard |
| Filtrar lista (ex.: "Só críticos", "Vencendo hoje") | `.at-chip` (`aria-pressed="true/false"`) | Chip usado como link de navegação entre páginas |
| Mostrar status de um pedido em 1 dos 3 eixos | `.at-status--<eixo>-<valor>` (ícone + texto + borda) | `.at-badge` genérico sem ícone ou misturando cores dos eixos |
| Alerta não-bloqueante (preço `< sugerido`, ruptura de estoque) | `.at-callout--warning` persistente no contexto | Toast efêmero ou erro bloqueante que impeça salvar |
| Erro de validação de servidor ou regra de negócio | `.at-callout--danger` (`role="alert"`) + `aria-invalid` no campo | `window.alert()` nativo |
| Confirmação transitória ("Pedido salvo", "Pagamento lançado") | `.at-toast` (`aria-live="polite"`, duração `6s`, pausa no hover/foco) | Toast para erro crítico que exige ação corretiva |
| Tarefa curta focalizada (Baixa de Estoque, Pagamento, Cliente rápido) | `.at-dialog` (`<dialog>.showModal()`) | Modal gigante com 20+ campos (use página ou view dedicada) |
| Comparar itens de estoque, tabelas de preço ou itens do pedido | `.at-table` dentro de `.at-table-wrap` | Grid de cards quando o usuário precisa comparar preços/saldos em coluna |
| Tela sem dados, filtrada sem resultado ou com erro de carga | `.at-state` (ícone + título + contexto + CTA resolutivo) | Tabela com apenas cabeçalho vazio ou texto solto `"Sem itens"` |

### 4.2 Inventário Real de Componentes (`frontend/src/` → Alvo V1.0)

| Componente / Arquivo Atual | Situação Real Observada | Classificação | Ação de Evolução para V1.0 |
|---|---|---|---|
| `src/components/Layout.jsx` (300 L) | Sidebar + mobile header + drawer com `<style>` inline (215 L) e `.sidebar-logo` duplicado; falta link de Tabelas de Preço. | **Normalizar** | Mover CSS para `layout.css`; usar `<nav aria-label>`, `aria-expanded` no menu mobile, `Esc` para fechar drawer e adicionar rota `/precos`. |
| `src/App.jsx` (`Login`, `RotaProtegida`) | Login hardcoded (`admin/admin123`), `alert()`, container aninhado em `RotaProtegida`, sem rota `*`. | **Normalizar** | Extrair `pages/Login.jsx` com estado controlado real (`useState`), erro inline acessível e redirect automático via interceptor `401`. |
| `src/pages/Dashboard.jsx` (`StatCard`, listas) | 6 `StatCard` com `rgb` manipulado por slice de string hex inline; soma rascunhos/cancelados na receita. | **Normalizar** | Extrair `ui/StatCard.jsx` usando variantes semânticas CSS; consumir `GET /dashboard/resumo` (receita confirmada, a receber, prazos, críticos negativos/m²). |
| `src/pages/Clientes.jsx` (`ModalCliente`, `ModalHistorico`) | `<style>` inline com `--card-bg` quebrado; histórico busca `GET /pedidos/` inteiro no cliente. | **Normalizar** | Extrair `ui/Dialog.jsx`, `ui/ConfirmDialog.jsx` e `clientes/ModalHistoricoCliente.jsx` consumindo `GET /clientes/{id}/pedidos` + busca `?q=`. |
| `src/pages/Estoque.jsx` (`ModalFormulario`, `TabButton`) | 480 L; `--card-bg` quebrado; falta conversor de chapas m², ajuste manual m², `estoque_minimo` e unidade `R$/m`. | **Normalizar** | Extrair `ui/Tabs.jsx`, `ui/DataTable.jsx`, `estoque/ModalEntradaChapas.jsx`, `estoque/ModalAjusteM2.jsx` e `estoque/CalculadoraCustoBarra.jsx`. |
| `src/pages/Calculadora.jsx` | 245 L; falta `mao_de_obra`, `paspatour_id`, `vidro_id`, `vidro_avulso` e CTA **"Adicionar ao Pedido"**. | **Normalizar** | Extrair `calculadora/FormComposicaoQuadro.jsx` e `calculadora/PainelResultadoCalculo.jsx` (reutilizável também ao adicionar item dentro de um pedido). |
| `src/pages/Pedidos.jsx` (939 L) | **Monólito crítico:** mistura Kanban, Lista, Formulário legado, Detalhe, Sinal, Baixa e Eventos + `<style>` inline + `--warning`/`--card-bg`. | **Decompor + Novo** | Quebrar em **8 componentes modulares** (ver §4.3 abaixo). |
| **Primitivos de UI (`src/components/ui/`)** | Inexistentes como módulo compartilhado (duplicados por página). | **Novo** | Criar `Button`, `Card`, `Dialog`, `ConfirmDialog`, `StatusBadge`, `Callout`, `ToastRegion`, `EmptyState`, `Tabs`, `DataTable`, `Field`. |
| **Página Tabelas de Preço (`src/pages/TabelasPreco.jsx`)** | Inexistente no frontend atual. | **Novo** | CRUD completo de `TabelaPrecoVidro` (com `area_minima_m2`), `TabelaPrecoFundo` e `TabelaPrecoPaspatour`. |

### 4.3 Plano de Decomposição do Monólito `Pedidos.jsx` (939 linhas)

```text
frontend/src/
├── components/ui/                    # Primitivos agnósticos de domínio (só tokens --at-*)
│   ├── Button.jsx / Card.jsx / Field.jsx
│   ├── Dialog.jsx / ConfirmDialog.jsx
│   ├── StatusBadge.jsx / Callout.jsx / ToastRegion.jsx
│   └── DataTable.jsx / EmptyState.jsx / Tabs.jsx
├── components/pedidos/               # Subdomínio Pedidos (substitui o monólito Pedidos.jsx)
│   ├── KanbanBoard.jsx               # 6 colunas saneadas (Desktop) + seletor por abas (Oficina Mobile)
│   ├── PedidoCard.jsx                # Anatomia limpa dos 3 eixos + saldo + prazo
│   ├── PedidoLista.jsx               # Visão tabular/cards para busca rápida
│   ├── PedidoForm.jsx                # Criação/edição de rascunho: 3 tipos de item, frete, desconto, validade, prazo
│   ├── PedidoDetalhe.jsx             # Visão 2 colunas: Status (3 eixos + Marcar Entregue), Itens, Pagamentos, Eventos
│   ├── ModalBaixaEstoque.jsx         # Previsão + ajuste manual barras + alerta não-bloqueante de ruptura
│   ├── ModalPagamento.jsx            # Lançamento de PagamentoPedido (forma_pagamento, valor, obs) + estorno
│   └── ModalAdicionarItemPedido.jsx  # Seletor: Quadro sob medida / Vidro avulso / Serviço livre
└── pages/Pedidos.jsx                 # Orquestrador enxuto (~120–180 L): filtros, alternância Kanban/Lista e rotas/modais
```

### 4.4 Padrões de Interação, Confirmação, Estados Vazios e Microcopy (PT-BR)

#### Matriz de Confirmação por Nível de Risco
| Ação do Usuário | Nível de Risco | Padrão Obrigatório | Regra de Foco e Cópia |
|---|---|---|---|
| Alternar aba, filtrar, abrir detalhe | Zero | Execução imediata | Sem confirmação |
| Reordenar moldura / remover linha não salva no form | Baixo | Execução imediata + opção de readicionar | Sem modal |
| Avançar produção (`pendente → na_fila`, `em_producao → embalando → pronto_entrega`) | Médio (reversível) | Execução imediata + **Toast com resumo** (`"Pedido #202600001 movido para Embalando"`) | Feedback em `aria-live="polite"` |
| Iniciar produção (`→ em_producao`) | **Alto (debita estoque)** | **Modal de Baixa Assistida** obrigatório (`GET previsao-baixa` → `POST baixa-estoque`) | Destaca ruptura `< 0` em amarelo se houver; botão `Confirmar Baixa e Iniciar Produção` |
| Confirmar orçamento (`rascunho → confirmado`), Marcar Entregue (`confirmado → entregue`) | Médio-Alto | Confirmação explícita (ou dialog `--sm` se `saldo_devedor > 0` ao entregar) | Na entrega com saldo em aberto: alerta `"Ainda há R$ X,XX em aberto. Confirmar entrega assim mesmo?"` |
| **Cancelar pedido / Excluir rascunho / Excluir cliente ou material** | **Destrutivo / Irreversível** | **`ConfirmDialog` (`--sm`) com botão `danger` repetindo o verbo** | **`Cancelar` à esquerda recebe foco inicial.** Se `valor_pago > 0` no cancelamento: `at-callout--warning` obrigatório sobre estorno |

#### Estados Vazios Diferenciados (`EmptyState`)
- **Base vazia (zero registros no banco):** ícone neutro + título direto + frase explicativa + botão primário de criação.
  - Ex. Pedidos: *"Nenhum pedido cadastrado ainda"* / *"Crie um orçamento pela Calculadora ou clique em Novo Pedido."* / CTA: `Novo Pedido`.
- **Filtro ou busca sem resultado:** ícone de busca + título citando o termo + botão secundário **`Limpar filtros`**. Nunca confundir com base vazia nem renderizar apenas `<thead>` vazio.

#### Limiares de Carregamento e Sessão Expirada (`401`)
- `< 400 ms`: não exibir skeleton/spinner (evita *flicker* no balcão).
- `400 ms – 3 s`: exibir `Skeleton` estrutural (no Kanban/tabelas) ou botão com `aria-busy="true"` e spinner (`"Calculando..."`, `"Gerando PDF..."`).
- `> 3 s`: exibir texto de etapa (`"Processando baixa de estoque..."`).
- **Erro `401 Unauthorized`:** o interceptor em `src/api/config.js` deve limpar `token_atividros`, disparar evento/callback para zerar `usuario` no `ContextoAutenticacao` e redirecionar imediatamente para `/login?sessao=expirada`, exibindo `at-callout--info` (*"Sua sessão expirou. Entre novamente para continuar."*).

#### Regras de Microcopy PT-BR
- **Botões:** `Verbo no infinitivo + Objeto` (`Adicionar Moldura`, `Adicionar ao Pedido`, `Registrar Pagamento`, `Confirmar Baixa`, `Baixar PDF`). Nunca `"OK"`, `"Sim"` ou `"Enviar"`.
- **Mensagens de Erro:** informam **(1) o que aconteceu**, **(2) o que foi preservado** e **(3) o que fazer**. Ex.: *"Não foi possível excluir o cliente porque existem pedidos vinculados. O cadastro foi mantido."*
- **Formatação Regional:** Datas `DD/MM/AAAA`, hora `24h`, moeda `R$ 1.234,56`, decimais visuais com vírgula na leitura (aceitando ponto ou vírgula na digitação quando aplicável).

---

## 5. Fluxos de Tela End-to-End (Balcão Desktop + Oficina Mobile/Tablet)

### 5.1 Mapa de Telas e Rastreabilidade (`Tela ↔ PRD ↔ ARQUITETURA.md`)

| Rota | Tela | Ambiente Prioritário | Requisitos (`PRD.md`) | Endpoints (`ARQUITETURA.md` §6.2) |
|---|---|---|---|---|
| `/login` | Autenticação | Balcão + Oficina | §3.1, Débito #4/#5 | `POST /autenticacao/entrar`, `GET /autenticacao/me` |
| `/` | Dashboard Operacional | Balcão (manhã) + Oficina | §3.7 | `GET /dashboard/resumo` |
| `/calculadora` | Calculadora Unificada | **Balcão (primário)** | §3.3 | `POST /calculadora/quadro`, `POST /calculadora/vidro-avulso`, `GET /estoque/*`, `GET /calculadora/tabela-*` |
| `/pedidos` | Pedidos & Kanban Produção | **Balcão + Oficina (primário)** | §3.4 | `GET/POST/PUT/DELETE /pedidos/*`, `PATCH /status`, `POST /pagamentos`, `GET /previsao-baixa`, `POST /baixa-estoque`, `GET /eventos`, `GET /pdf` |
| `/estoque` | Estoque & Chapas (`m²`) | Balcão + Oficina | §3.2.A–C, §4.4 | `GET/POST/PUT/DELETE /estoque/*`, `POST /entrada-chapas`, `POST /ajuste-m2` |
| `/precos` | Tabelas de Preço | Balcão | §3.2.D | `GET/POST/PUT/DELETE /calculadora/tabela-vidro`, `tabela-fundo`, `tabela-paspatour` |
| `/clientes` | Clientes & Histórico | Balcão | §3.5 | `GET /clientes/?q=`, `POST/PUT/DELETE /clientes/*`, `GET /clientes/{id}/pedidos` |

> **Nota sobre Login (`/login`):** Remover valores hardcoded (`defaultValue="admin"` / `login('admin', 'admin123')` de `App.jsx:16-31`). Exibir campos controlados vazios (`Usuário`, `Senha` com toggle opcional `Mostrar/Ocultar senha`), botão `Entrar` com `aria-busy` durante requisição e `at-callout--danger` inline para erros `401`/`403`.

---

### 5.2 Fluxo Rápido: Calculadora → Adicionar ao Pedido → Pagamento → PDF

Este é o fluxo de maior frequência no balcão (`JTBD #1` do `PRD.md`). Todo o cálculo vem exclusivamente do backend (`ADR-007`).

#### Wireframe Estrutural — Balcão Desktop (`>= 1024 px`)

```text
+---------------------------------------------------------------------------------------------------+
| ATIVIDROS | Calculadora Unificada            [ Tipo: (• Quadro Sob Medida) ( Vidro Avulso ) ]     |
+------------------------------------------------------+--------------------------------------------+
| 1. OBRA E QUANTIDADE                                 | RESULTADO DA COMPOSIÇÃO                    |
| Largura (cm)* [ 50,00 ]  Altura (cm)* [ 40,00 ]      |                                            |
| Quantidade*   [   2   ]                              |  Valor unitário sugerido:  R$ 414,30       |
|                                                      |  Total sugerido (2 un):    R$ 828,60       |
| 2. PASPATOUR                                         | ------------------------------------------ |
| [x] Usar paspatour                                   | CAMADAS PROPAGADAS (de dentro para fora)   |
| Tipo* [ Paspatour Branco (R$ 80,00/m²) v ]           |  Obra ...................... 50,00 × 40,00 |
| Borda por lado (cm)* [ 5,00 ]                        |  Vidro / Fundo ............. 60,00 × 50,00 |
|                                                      |  Moldura 1 (M01 · 3cm) ..... 66,00 × 56,00 |
| 3. MOLDURAS (interna -> externa)      [+ Moldura]    |    Corte: 2,6800 m/un · ~2 barras p/ lote  |
| 1. [ M01 - Preta (3cm | R$ 50,00/m | est: 4 br) v][x]|  Moldura 2 (M02 · 4cm) ..... 74,00 × 64,00 |
| 2. [ M02 - Ouro  (4cm | R$ 60,00/m | est: 8 br) v][x]|    Corte: 3,0800 m/un · ~3 barras p/ lote  |
|                                                      |  QUADRO FINAL ............... 74,00 × 64,00|
| 4. VIDRO, FUNDO E MÃO DE OBRA                        | ------------------------------------------ |
| Tipo de Vidro [ Incolor (R$ 120/m² | mín 0,25m²) v ] | COMPOSIÇÃO DE CUSTOS (Unitário)            |
| Chapa Estoque [ Incolor 3mm (Saldo: 5,00 m²)    v ]  |  Paspatour (0,3000 m²) ........... R$ 24,00|
| Tipo de Fundo [ MDF (R$ 35,00/m²)               v ]  |  Vidro incolor (0,3000 m²) ....... R$ 36,00|
| Chapa Fundo   [ MDF 3mm (Saldo: 8,20 m²)        v ]  |  Moldura M01 (2,6800 m) ......... R$ 134,00|
| Mão de obra (R$/un) [ 25,00 ]                        |  Moldura M02 (3,0800 m) ......... R$ 184,80|
|  └─ Somada ao valor unitário de cada quadro          |  Fundo MDF (0,3000 m²) ........... R$ 10,50|
|                                                      |  Mão de obra (1 un) .............. R$ 25,00|
| [        Calcular Composição        ]              | ------------------------------------------ |
|                                                      | [ + Adicionar ao Pedido ]  [ Limpar ]      |
+------------------------------------------------------+--------------------------------------------+
```

#### Comportamento no Mobile/Tablet (`<= 1023 px`)
- As duas colunas empilham em coluna única; após calcular, a tela rola suavemente (ou exibe barra fixa inferior *sticky* com `Total sugerido: R$ 828,60` + botão **`Ver detalhe / Adicionar`** de `48 px` de altura).

#### Passo a Passo Pós-Clique em **"Adicionar ao Pedido"**
1. **Destino do Item (`Drawer` ou `Dialog --sm` rápido):**
   - Opção A: **`Criar Novo Orçamento (Rascunho)`** (padrão quando não veio de um pedido aberto).
   - Opção B: **`Adicionar a Orçamento Existente`** (lista rápida de pedidos em `status_geral = rascunho` — ou retorna direto se o usuário abriu a Calculadora a partir do `PedidoForm`).
2. **Suporte aos 3 Tipos de Item no Pedido (`PedidoForm`):**
   - `quadro_sob_medida`: pré-preenchido com `descricao_sugerida` (editável), `quantidade`, `valor_sugerido` (readonly/referência interna), `preco_unitario` (editável livremente) e todo o payload dimensional.
   - `vidro_avulso`: formulário compacto (`vidro_tipo`, `vidro_id` opcional, `obra_largura`, `obra_altura`, `quantidade`, `mao_de_obra`) calculado via `POST /calculadora/vidro-avulso` (exibindo nota se `area_real_m2 < area_minima_m2`, ex.: *"Área mínima aplicada: 0,2500 m²"*).
   - `servico_livre`: formulário direto (`descricao`, `quantidade`, `preco_unitario`).
3. **Edição Livre de Preço + Alerta Amarelo Não-Bloqueante:**
   - Ao editar `preco_unitario` (ou o total do item) para um valor menor que `valor_sugerido`:
     - Exibe imediatamente um banner compacto **`.at-callout--warning`** abaixo do item:
       `[!] Valor abaixo do sugerido pela calculadora (sugerido: R$ 414,30/un). Você pode salvar normalmente.`
     - O botão de salvar **permanece habilitado**; o PDF **nunca** exibe `valor_sugerido` nem esse alerta.
4. **Fechamento Comercial do Pedido (`PedidoForm`):**
   - `Cliente *` (busca rápida + botão `+ Novo Cliente` inline)
   - `Data de Validade do Orçamento` (default automático `hoje + 7 dias` em `rascunho`)
   - `Prazo de Entrega` e `Endereço de Entrega` (opcional)
   - `Frete (R$)` *(somado ao `valor_total`)* e `Desconto` (`valor` R$ ou `percentual` %, *subtraído do `valor_total`*)
   - Painel de Resumo em `tabular-nums`: `Subtotal dos Itens` + `Frete` − `Desconto` = **`Total do Pedido`**.
   - Ações finais: **`Salvar Orçamento`** (`rascunho`) ou **`Salvar e Confirmar`** / **`Baixar PDF`**.
5. **Lançamento de Pagamentos (`ModalPagamento` dentro de `PedidoDetalhe`):**
   - Lista de `PagamentoPedido` já lançados (`Data | Forma | Valor | Observação | Ação Estornar`).
   - Formulário rápido: `Valor (R$)` (atalho opcional *"Preencher saldo restante"*), `Forma de Pagamento` (`pix`, `cartao_credito`, `cartao_debito`, `dinheiro`, `outro`), `Data/Hora` (default agora) e `Observação`.
   - Se o pedido estava em `rascunho`, exibe aviso informativo (`at-callout--info`): *"Ao registrar o primeiro pagamento, este orçamento será confirmado automaticamente como Pedido."*

---

### 5.3 Modal de Baixa de Estoque Assistida (`previsao-baixa` → `baixa-estoque`)

Acionado **obrigatoriamente** sempre que o operador move um pedido de `pendente`, `aguardando_material` ou `na_fila` para `em_producao` (nunca via dropdown direto).

#### Wireframe Estrutural (Desktop e Adaptável para Oficina Mobile)

```text
+-----------------------------------------------------------------------+
| Baixa de Estoque Assistida — Pedido #202600001                    [X] |
+-----------------------------------------------------------------------+
| Ao confirmar, o pedido avançará para Em Produção e os insumos abaixo  |
| serão debitados do estoque.                                           |
|                                                                       |
| MOLDURAS (Ajuste manual de barras permitido)                          |
| +-------------------------------------------------------------------+ |
| | M01 · Preta (Barra 3,00 m)                                        | |
| | Consumo calculado: 5,3600 m  |  Sugestão: 2 barras                | |
| | Estoque atual: 1 br   ->   Saldo projetado: -1 br [!] RUPTURA     | |
| | Barras a baixar:   [ - ]  [  2  ]  [ + ]                          | |
| +-------------------------------------------------------------------+ |
|                                                                       |
| CHAPAS — VIDROS E FUNDOS (Baixa em m² reais de corte)                 |
| +-------------------------------------------------------------------+ |
| | Vidro Incolor 3mm                                                 | |
| | Consumo real: 0,6000 m²  |  Saldo atual: 5,0000 m² -> 4,4000 m²   | |
| +-------------------------------------------------------------------+ |
| | Fundo MDF 3mm                                                     | |
| | Consumo real: 0,6000 m²  |  Saldo atual: 0,4000 m² -> -0,2000 m²  | |
| | [!] RUPTURA: saldo ficará negativo após a baixa                   | |
| +-------------------------------------------------------------------+ |
|                                                                       |
| +-------------------------------------------------------------------+ |
| | [!] ATENÇÃO: 2 materiais ficarão com saldo negativo (ruptura).    | |
| | A produção NÃO será bloqueada; regularize a compra no Estoque.    | |
| +-------------------------------------------------------------------+ |
|                                                                       |
| Observação operacional (opcional)                                     |
| [ Iniciado corte na bancada 1                                       ] |
|                                                                       |
| [ Cancelar ]                     [ Confirmar Baixa e Iniciar Produção]|
+-----------------------------------------------------------------------+
```

#### Regras de UX e Acessibilidade do Modal
1. **Controles de Ajuste Manual de Molduras:**
   - Botões `[-]` e `[+]` com tamanho mínimo **`44 × 44 px`** (oficina touch), `aria-label="Diminuir barras de M01"` / `"Aumentar barras de M01"`, e input numérico inteiro (`min="0"`, `inputMode="numeric"`).
   - O cálculo de `Saldo projetado = estoque_atual - barras_baixadas` atualiza em **tempo real** no cliente conforme o operador ajusta as barras (ex.: se o operador aproveitar sobra e baixar `1` em vez de `2`, o alerta de ruptura de `-1` para `0` desaparece instantaneamente!).
2. **Vidros e Fundos:** exibem estritamente `area_a_baixar_m2` (`area_real_m2 × quantidade`, com 4 casas decimais em `tabular-nums`), deixando claro que áreas mínimas comerciais (ex.: `0,25 m²`) não inflam a baixa física. Caso algum item tenha `vidro_tipo` sem `vidro_id` vinculado (material comprado sob encomenda), exibir nota informativa `"Sem chapa vinculada no estoque — sem débito automático"`.
3. **Alerta Não-Bloqueante de Ruptura:** quando qualquer material tiver `saldo_projetado < 0`, exibir badge/borda âmbar na linha do material e `.at-callout--warning` no rodapé. **O botão `Confirmar Baixa e Iniciar Produção` permanece ativo.**
4. **Pós-confirmação:** se a API retornar `alertas_ruptura` não vazio, exibir Toast persistente ou Banner no topo do `PedidoDetalhe` listando os materiais que ficaram negativos.
5. **Estado Vazio (Pedido Sem Insumos Físicos / `possui_insumos_estoque: false`):** quando `GET /pedidos/{id}/previsao-baixa` retornar `possui_insumos_estoque: false` (ex.: pedido composto apenas por `servico_livre` ou por itens sem vínculo de estoque físico), ocultar as listas de molduras/chapas e exibir um `Callout` informativo (`at-callout--info`) com a mensagem: *"Este pedido não possui molduras, vidros ou fundos vinculados ao estoque físico. Confirmar iniciará a produção sem baixa de materiais."* Nessa condição, manter o botão primário **`Iniciar Produção`** habilitado.

---

### 5.4 Visualização Limpa dos 3 Eixos no Kanban e na Lista

#### Colunas Oficiais do Kanban de Produção (Exclusivamente 6 Colunas)
O Kanban exibe **apenas os 6 estados do Eixo 2 (`status_producao`)** — **a coluna `entregue` é proibida no Kanban**:

1. `pendente` — **Pendente**
2. `aguardando_material` — **Aguard. Material**
3. `na_fila` — **Na Fila**
4. `em_producao` — **Em Produção**
5. `embalando` — **Embalando**
6. `pronto_entrega` — **Pronto p/ Entrega**

- **Regra de Visibilidade no Kanban Ativo vs. Visão Lista:**
  - Por padrão, o **Kanban ativo de produção** exibe **exclusivamente pedidos com `status_geral == 'confirmado'`** (não exibe `rascunho`, `entregue`, `arquivado` nem `cancelado`), mantendo na bancada da oficina apenas ordens confirmadas prontas para execução.
  - **Orçamentos (`rascunho`)**, além de pedidos **`entregue`**, **`arquivado`** e **`cancelado`**, ficam na visão **Lista** (com filtro rápido `.at-chip` no topo incluindo **`Orçamentos (Rascunho)`**, além de `Entregues`, `Arquivados` e `Cancelados` consultáveis por `status_geral`).
  - Somente pedidos confirmados (`status_geral == 'confirmado'`) entram na fila da oficina e podem disparar a **Baixa Assistida** para avançar para `em_producao`; orçamentos em `rascunho` devem ser confirmados antes de entrar em produção.

#### Anatomia do Card no Kanban (Sem Poluição Visual)

```text
+------------------------------------------+
| #202600001          Prazo: 05/12  [!]    |  <- Código tabular + Prazo (vermelho se vencido)
| Maria Silva · 2 itens                    |  <- Cliente + resumo de itens
+------------------------------------------+
| [✓ Confirmado]     [◐ Pgto. Parcial]     |  <- Máx. 2 badges (Eixo 1 + Eixo 3)
|                    Falta: R$ 214,30      |     Eixo 2 já é a coluna!
+------------------------------------------+
| Total: R$ 828,60   [ Baixar e Produzir ] |  <- Ação contextual primária da etapa (>=44px no mobile)
+------------------------------------------+
```

- **Por que no Kanban o Card mostra apenas 2 badges (Geral + Financeiro)?** Porque a **própria coluna** já comunica o `status_producao` (Eixo 2). Na visão em **Lista**, os 3 eixos aparecem em colunas/badges distintos com rótulos explícitos (`Geral`, `Produção`, `Financeiro`).
- **Ação "Marcar Entregue" (Fora da Progressão de Produção):**
  - Quando o card está na coluna `pronto_entrega` e `status_geral == confirmado`, o botão contextual do card (e do `PedidoDetalhe`) oferece **`Marcar Entregue`** (`PATCH /pedidos/{id}/status` com `eixo: "geral", novo_status: "entregue"`). Ao confirmar, o pedido sai do Kanban ativo da oficina e passa a constar como `Entregue` no histórico/lista.
- **Comportamento na Oficina Mobile (`<= 767 px`):**
  - Em vez de 6 colunas espremidas a `180 px` (como no `Pedidos.jsx:918` atual), o topo exibe uma **barra horizontal rolável de chips de estágio** com contadores:
    `[ Pendente (2) ] [ Aguard. Mat. (1) ] [ Na Fila (3) ] [ Em Prod. (4) ] [ Embalando (1) ] [ Pronto (2) ]`
  - Abaixo, exibe apenas os cards da etapa selecionada em **largura 100%**, mostrando medidas resumidas de corte ao tocar/expandir e botão de avanço com altura mínima de `44 px` na base do card.

---

## 6. Layout do PDF Único (`GET /pedidos/{id}/pdf`)

Documento **A4 Retrato (`210 × 297 mm`)**, gerado em memória via `fpdf2` (`app/services/gerador_pdf.py`), com fundo branco, alto contraste em tinta preta/cinza-escuro (`#111827` / `#4B5563`) para impressão econômica em impressora térmica/laser de balcão e leitura limpa na oficina.

### 6.1 Wireframe Estrutural A4

```text
+------------------------------------------------------------------------------+
|  ATIVIDROS — Molduras, Vidros e Espelhos                                     |
|  +------------------------------------------------------------------------+  |
|  |  [BANNER CONTEXTUAL]                                                   |  |
|  |  Se status_geral == rascunho:                                          |  |
|  |    ORÇAMENTO #202600001                Validade: 03/12/2026            |  |
|  |  Se status_geral in (confirmado, entregue, arquivado):                |  |
|  |    PEDIDO / ORDEM DE SERVIÇO #202600001   Prazo de Entrega: 05/12/2026 |  |
|  |  Se status_geral == cancelado:                                         |  |
|  |    PEDIDO CANCELADO #202600001         (Prazo de Entrega omitido)      |  |
|  +------------------------------------------------------------------------+  |
|  Emissão: 26/11/2026 15:30   |   Situação: Confirmado · Em Produção          |
|                                                                              |
|  DADOS DO CLIENTE E ENTREGA                                                  |
|  --------------------------------------------------------------------------  |
|  Cliente: Maria Silva                  Telefone: (11) 99999-9999             |
|  E-mail:  maria@exemplo.com            End. Cliente: Rua A, 50 - Centro      |
|  End. Entrega: Rua das Flores, 100 (CEP 01000-000)                           |
|                                                                              |
|  ITENS E MEDIDAS TÉCNICAS                                                    |
|  +--------------------------------------------+-----+----------+-----------+ |
|  | Item / Composição e Medidas de Corte (cm)  | Qtd | Unitário |  Subtotal | |
|  +--------------------------------------------+-----+----------+-----------+ |
|  | 1. Quadro 40x50cm | Paspatour 5cm |        |  2  | R$210,00 | R$ 420,00 | |
|  |    Vidro incolor | Moldura M01 + M02 | MDF |     |          |           | |
|  |    • Obra: 50,00 x 40,00 cm                |     |          |           | |
|  |    • Paspatour: 5,00 cm (Branco)           |     |          |           | |
|  |    • Vidro / Fundo: 60,00 x 50,00 cm       |     |          |           | |
|  |    • Molduras (int->ext):                  |     |          |           | |
|  |      1) M01 (3,0cm): corte 66,00 x 56,00 cm|     |          |           | |
|  |      2) M02 (4,0cm): corte 74,00 x 64,00 cm|     |          |           | |
|  |    • QUADRO FINAL: 74,00 x 64,00 cm        |     |          |           | |
|  +--------------------------------------------+-----+----------+-----------+ |
|  | 2. Vidro Avulso Espelho 30,00 x 40,00 cm   |  1  | R$ 45,00 | R$  45,00 | |
|  +--------------------------------------------+-----+----------+-----------+ |
|  | 3. Instalação na residência                |  1  | R$ 80,00 | R$  80,00 | |
|  +--------------------------------------------+-----+----------+-----------+ |
|                                                                              |
|  OBSERVAÇÕES                              RESUMO FINANCEIRO                  |
|  +----------------------------------+     +--------------------------------+ |
|  | Cliente prefere gancho serrilha. |     | Subtotal dos itens:  R$ 545,00 | |
|  |                                  |     | Frete (+):           R$  30,00 | |
|  |                                  |     | Desconto (- 10%):   -R$  54,50 | |
|  +----------------------------------+     | ------------------------------ | |
|                                           | TOTAL DO PEDIDO:     R$ 520,50 | |
|  PAGAMENTOS REGISTRADOS                   | Total Pago:          R$ 200,00 | |
|  26/11/2026 · PIX · R$ 200,00 (Sinal 50%) | SALDO DEVEDOR:       R$ 320,50 | |
|                                           +--------------------------------+ |
|                                                                              |
|  ____________________________________     _________________________________  |
|  Assinatura do Cliente / Aprovação        Conferência Oficina  |  ___/___/__ |
|                                                                              |
|  ATIVIDROS · Documento gerado em 26/11/2026 às 15:30          Página 1/1     |
+------------------------------------------------------------------------------+
```

### 6.2 Regras Visuais e de Conteúdo Obrigatórias do PDF
1. **Cabeçalho Adaptativo (`ADR-009`, alinhado à `ARQUITETURA.md §7.3`):**
   - `status_geral == 'rascunho'`: título **`ORÇAMENTO`** e destaque obrigatório para **`Data de Validade: DD/MM/AAAA`**.
   - `status_geral in ('confirmado', 'entregue', 'arquivado')`: título **`PEDIDO / ORDEM DE SERVIÇO`** e destaque obrigatório para **`Prazo de Entrega: DD/MM/AAAA`** (ou `"A combinar"` se nulo).
   - `status_geral == 'cancelado'`: banner destacado **`PEDIDO CANCELADO`** no cabeçalho (substituindo o banner padrão de Ordem de Serviço) e **omissão explícita de `Prazo de Entrega`**.
2. **Tabela de Itens e Medidas Técnicas:**
   - Usa exclusivamente dados imutáveis de `ItemPedido` (`descricao`, `quantidade`, `preco_unitario`, `subtotal`) e `snapshot_calculo` / `ItemPedidoMoldura`.
   - Para `quadro_sob_medida`, imprime obrigatoriamente todas as camadas propagadas: `Obra`, `Paspatour` (se ativo), `Vidro/Fundo`, lista ordenada de `Molduras` (da interna `0` para a externa `N-1`) e `QUADRO FINAL` em negrito para leitura rápida na bancada da oficina.
   - Quebra de linha automática (`multi_cell`) evitando truncamento de descrições longas e evitando quebra de página no meio de um mesmo item.
3. **Resumo Financeiro Completo:**
   - Exibe `Subtotal dos itens`, `Frete (+)` (exibir `R$ 0,00` quando zerado para transparência), `Desconto (-)` (indicando `%` quando `desconto_tipo == percentual`), `TOTAL DO PEDIDO` em negrito e lista resumida de `PagamentoPedido` / `Total Pago`.
   - Para pedidos não cancelados: exibe **`SALDO DEVEDOR`** em destaque.
   - Para `status_geral == 'cancelado'` (alinhado à `ARQUITETURA.md §7.3`): substitui **`SALDO DEVEDOR`** por **`STATUS: CANCELADO (SEM COBRANÇA ATIVA)`**, mantendo o registro de `Total Pago` e exibindo **nota de estorno pendente** sempre que `valor_pago > 0`.
4. **Regra Absoluta de Sigilo Comercial:**
   - `ItemPedido.valor_sugerido`, `abaixo_do_sugerido` e `Moldura.preco_custo` **jamais** podem ser impressos no PDF. O cliente vê apenas o `preco_unitario` praticado e o `subtotal`.

---

## 7. Glossário Canônico de UI (PT-BR)

| Termo Canônico na UI | Sentido no Domínio (`PRD.md` / `ARQUITETURA.md`) | Onde Usar | Evitar |
|---|---|---|---|
| **Orçamento (Rascunho)** | Pedido com `status_geral = rascunho` e `data_validade_orcamento` | Pedidos, PDF, Dashboard | "Simulação salva", "Pré-pedido" |
| **Pedido / Ordem de Serviço** | Pedido confirmado (`confirmado`+) com `prazo_entrega` e produção ativa | Pedidos, PDF | "Venda", "OS" solto sem número |
| **Obra** | Peça do cliente (tela, foto, gravura) medida em `largura × altura` (cm) | Calculadora, PDF | "Tamanho do quadro" (ambíguo) |
| **Paspatour** | Borda decorativa interna ao redor da obra (`tamanho_paspatour` cm/lado) | Calculadora, Tabelas de Preço, PDF | "Passe-partout" misturado com "Paspatour" |
| **Moldura** | Perfil em barra (`tamanho_barra` m, `largura_barra` cm, preço `R$/m`) | Estoque, Calculadora, Baixa, PDF | "Perfil" sem contexto |
| **Chapa** | Unidade de entrada de Vidro ou Fundo convertida para `m²` (`qtd × L × A / 10000`) | Estoque (Entrada de Chapas) | Baixar ou contar vidro por "unidade de chapa" na produção |
| **Suplemento** | Insumo acessório de controle 100% manual (cola, grampos, fita, embalagem) | Estoque | "Matéria-prima automática" |
| **Quadro sob medida** | Item `quadro_sob_medida` gerado pela Calculadora com snapshot técnico | Calculadora, Pedido | "Quadro personalizado" genérico |
| **Vidro avulso** | Item `vidro_avulso` (corte reto com regra de `area_minima_m2`) | Calculadora, Pedido | "Vidro solto" |
| **Serviço livre** | Item `servico_livre` com descrição e preço manual | Pedido | "Item avulso" (confunde com vidro) |
| **Mão de obra (`R$/un`)** | Valor unitário de serviço somado ao quadro (`ADR-002`) | Calculadora | "Taxa extra" ou valor diluído |
| **Baixa Assistida** | Confirmação de consumo de barras (ajustável) e `m²` reais ao ir para `em_producao` | Kanban, PedidoDetalhe | "Deduzir automático sem revisar" |
| **Ruptura de Estoque** | Saldo atual ou projetado `< 0` após baixa (alerta não-bloqueante) | Baixa Assistida, Dashboard | "Erro fatal de estoque" |
| **Pgto. Parcial** | Enum `pagamento_parcial` (`0 < valor_pago < valor_total`) | Badges Eixo Financeiro | "Sinal recebido" (`sinal_recebido` legado) |
| **Embalando** | Enum `embalando` no Eixo Produção | Kanban, Badges | "Para embalar" (`para_embalar` legado) |
| **Pronto p/ Entrega** | Fim do fluxo da Oficina no Eixo Produção (`pronto_entrega`) | Kanban (última coluna) | "Entregue" no Kanban de produção |
| **Entregue** | Conclusão comercial no Eixo Geral (`status_geral = entregue`) | Ação "Marcar Entregue", Lista | Coluna do Kanban de produção |

---

## 8. Checklist de Acessibilidade WCAG 2.2 AA (Por Categoria)

Legenda de verificação: **Projeto (Design)** = especificado neste documento; **A verificar em build/navegador** = obrigatório validar na implementação com `axe-core`/Lighthouse, teclado e dispositivo móvel real.

### 8.1 Contraste e Cor (`WCAG 1.4.1`, `1.4.3`, `1.4.11`)
- [x] Todos os pares de texto e superfícies da paleta `--at-color-*` validados com razão `>= 4,5:1` (menor razão em botões/badges: `4,83:1` em `danger`). *(Projeto — ver §3.6)*
- [x] Bordas de controles (`--at-color-border-strong`) e anel de foco (`--at-color-border-focus`) validados `>= 3,0:1` (`3,13:1` a `7,74:1`). *(Projeto — ver §3.6)*
- [ ] Nenhum componente usa cor hex literal ou `rgba()` fora de `src/styles/tokens.css`. *(A verificar em code review/lint CSS)*
- [ ] Nenhum status dos 3 eixos, alerta não-bloqueante ou erro de campo depende **apenas** de cor (ícone + rótulo + estilo de borda verificados em escala de cinza). *(A verificar em navegador)*

### 8.2 Teclado, Foco e Modais (`WCAG 2.1.1`, `2.1.2`, `2.4.3`, `2.4.7`, `2.4.11`)
- [ ] Fluxo completo do balcão (`Login`, `Calculadora`, `PedidoForm`, `ModalPagamento`, `ModalBaixaEstoque`) operável 100% via `Tab`, `Shift+Tab`, `Enter`, `Espaço`, setas (em abas) e `Esc`.
- [ ] `:focus-visible` visível (`2 px solid`, `offset 2 px`) em todos os controles interativos, nunca encoberto por barras *sticky* ou cabeçalho mobile.
- [ ] Todos os modais usam `<dialog>.showModal()` (ou equivalente com trap de foco): foco entra ao abrir, `Esc` fecha, clique fora não confirma ação destrutiva, e foco retorna ao elemento disparador ao fechar.
- [ ] Em diálogos destrutivos (`ConfirmDialog`), foco inicial cai obrigatoriamente no botão **Cancelar** (à esquerda).

### 8.3 Alvos de Toque e Responsividade Oficina (`WCAG 2.5.8`, `1.4.4`, `1.4.10`)
- [ ] Botões operacionais da oficina (setas/stepper `-/+` de barras na Baixa Assistida, chips de estágio do Kanban mobile, botões de ação rápida do card) com área mínima `>= 44 × 44 px`.
- [ ] Ações secundárias de tabela desktop com área mínima `>= 28 × 28 px` e espaçamento `>= 8 px`.
- [ ] Reflow funcional em `320 px` de largura sem scroll horizontal da janela principal e zoom de navegador até `200%` sem perda de conteúdo ou sobreposição.
- [ ] Inputs no mobile com `font-size >= 16 px` (`1rem`) para evitar zoom forçado no iOS/Android durante digitação na oficina.

### 8.4 Semântica, Leitores de Tela e Movimento (`WCAG 1.3.1`, `3.3.1`, `4.1.2`, `4.1.3`, `2.3.3`)
- [ ] Documento HTML com `lang="pt-BR"`, landmarks semânticas (`<nav>`, `<header>`, `<main>`) e exatamente um `<h1>` por página.
- [ ] Todo `<input>`, `<select>` e `<textarea>` possui `<label htmlFor>` associado; erros de validação usam `aria-invalid="true"` e `aria-describedby` apontando para a mensagem de erro.
- [ ] Todo botão apenas com ícone (`.at-btn--icon`) possui `aria-label` descritivo e ícone SVG marcado com `aria-hidden="true"`.
- [ ] Região de toasts usa `aria-live="polite"`; erros bloqueantes e alertas críticos usam `role="alert"`; botões em processamento usam `aria-busy="true"`.
- [ ] `@media (prefers-reduced-motion: reduce)` desativa transições/animações no `base.css`.

---

## 9. Resumo de Rastreabilidade para Implementação

1. **Saneamento CSS imediato:** criar `src/styles/tokens.css`, `base.css`, `layout.css`, `components.css`, eliminar todos os `<style>` inline e corrigir `--card-bg` / `--warning` / contraste `2,54:1` do botão primário.
2. **Primitivos e Refatoração:** implementar `src/components/ui/` antes de fatiar `Pedidos.jsx` (939 linhas) e atualizar `Layout.jsx`, `App.jsx` (`401` + Login real), `Dashboard.jsx`, `Estoque.jsx`, `TabelasPreco.jsx`, `Calculadora.jsx` e `Clientes.jsx`.
3. **PDF Único:** evoluir `backend/app/services/gerador_pdf.py` seguindo rigorosamente o wireframe da Seção 6 (`ORÇAMENTO` vs. `PEDIDO / ORDEM DE SERVIÇO`, medidas por camada, resumo financeiro completo e zero vazamento de `valor_sugerido`).
