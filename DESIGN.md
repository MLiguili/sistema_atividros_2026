# Design System — Atividros (Identidade Clara de Molduraria & Galeria)

## 1. Direção Visual e Princípios

Sistema operacional web em **modo claro editorial** alinhado às referências oficiais em `mockups/`: superfícies luminosas para leitura confortável no balcão da loja e na bancada da oficina, combinando tipografia editorial nos títulos com controles táteis limpos e contraste mínimo **WCAG 2.1 AA**.

## 2. Arquitetura CSS (3 Camadas sem Tailwind no Bundle Final)

Arquivos modulares importados em ordem determinística via `frontend/src/main.jsx`:
1. `src/styles/tokens.css` — Primitivos da marca, neutros, estados semânticos e tipografia.
2. `src/styles/base.css` — Reset, seleção de texto, foco acessível, tipografia e `prefers-reduced-motion`.
3. `src/styles/layout.css` — Shell lateral responsivo, logotipo oficial, login e grids operacionais.
4. `src/styles/components.css` — Primitivos `.at-*` (botões pill, cards, formulários, tabelas, badges 3 eixos, callouts, `<dialog>`, toasts e motif circular de KPIs).
5. `src/styles/pages/{pedidos,calculadora,estoque}.css` — Layout de Kanban, baixa assistida, resumo de cálculo e busca de estoque.

## 3. Paleta e Contraste

- **Fundos:** Canvas `#F8FAFB` (`--at-color-bg-canvas`), Superfícies/Cards `#FFFFFF` (`--at-color-bg-surface`), Subtile `#EEF8F9` (`--at-color-bg-subtle`), Destaque Azul-Gelo `#DCF0F2` (`--at-color-bg-ice`).
- **Tinta e Bordas:** Primário Carvão `#1F2426`, Secundário `#475257`, Muted `#59656B`, Borda sutil `#E2ECEE`, Borda forte `#C5D5D9`, Foco Azul Celeste `#76A5C5`.
- **Assinatura das 6 Molduras:** Bronze `#8E734B`, Champagne `#B5A385`, Dourado `#C88A36`, Lilás `#8C6DA8`, Azul Celeste `#76A5C5`.
- **Ação Primária:** Pill sólido Carvão `#1F2426` com texto branco `#FFFFFF`.

## 4. Tipografia

- **Marca (`LogoAtividros`):** `Dancing Script` (`--at-font-script`).
- **Títulos (`h1`, `h2` e total calculado):** `Playfair Display` (`--at-font-serif`), com `text-wrap: balance` e tracking `-0.02em`.
- **Interface e Dados:** `Plus Jakarta Sans` (`--at-font-sans`) e numerais tabulares `.at-num` (`tabular-nums`).

## 5. Componentes Assinatura e Acessibilidade

- **Motif Circular de KPI (`StatCard`):** Container `#DCF0F2` com círculo interno `#FFFFFF` e ícone em traço fino (`lucide-react`).
- **Máquina de Estados em 3 Eixos (`StatusBadge`):** Distinção visual simultânea por cor acessível, ícone e estilo de borda (tracejada em rascunho/pendente/parcial, pontilhada em aguardando material/arquivado/estornado, sólida nos demais estados).
- **Alvos Táteis e Modais:** Botões principais e steppers de Baixa Assistida com altura mínima `44px`; diálogos nativos HTML5 `<dialog>` com `ConfirmDialog` iniciando o foco no botão **Cancelar**.
