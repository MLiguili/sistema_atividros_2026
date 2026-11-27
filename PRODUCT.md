# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Equipe operacional interna da molduraria e vidraçaria Atividros: atendentes de balcão (orçamentos, cadastro de clientes, recebimento de pagamentos, emissão de PDF) e marceneiros/vidraceiros de oficina (fila de produção no Kanban, baixa assistida de barras e m², controle de estoque).

## Product Purpose

Centralizar o ciclo completo de venda sob medida e produção da Atividros — da simulação determinística de quadros/vidros avulsos até a entrega e arquivamento — garantindo precisão financeira (`Decimal`), rastreabilidade de insumos e agilidade operacional em balcão desktop e oficina mobile/tablet.

## Positioning

ERP artesanal sob medida para molduraria fina e vidraçaria: unifica propagação geométrica 45° + paspatour + área mínima comercial em uma única calculadora conectada ao Kanban em 6 etapas e à Baixa Assistida não bloqueante por barras inteiras e área real em m².

## Operating Context

- Uso híbrido entre balcão bem iluminado (desktop) e bancada/oficina (tablet e celular, com alvos de toque >= 44px para mãos com luvas/sujas de pó).
- Banco SQLite local em desenvolvimento e PostgreSQL (`asyncpg`) em produção via FastAPI.
- O sistema interno opera autenticado por JWT; não há portal público na V1.0.

## Capabilities and Constraints

- Calculadora unificada (Quadro Sob Medida e Vidro/Espelho Avulso) com vínculo automático de chapa física e aviso de compra quando ausente no estoque.
- Pedidos com máquina de estados em 3 eixos independentes (`geral`, `producao`, `financeiro`), confirmação automática no primeiro pagamento e Baixa Assistida obrigatória para iniciar produção.
- PDF único A4 sanitizado sem exposição de preço sugerido, margem ou preço de custo.
- Alerta persistente não bloqueante quando preço praticado ficar abaixo do sugerido ou quando houver ruptura de estoque.
- Exclusões explícitas V1.0: sem WhatsApp API, sem NF-e, sem RBAC granular e sem otimizador de plano de corte/aparas.

## Brand Commitments

- Identidade oficial definida em `mockups/`: logotipo com as 6 molduras retangulares entrelaçadas (dourado `#C88A36`, bronze `#8E734B`, champagne `#B5A385`, lilás `#8C6DA8`, azul celeste `#76A5C5`), assinatura em `Dancing Script`, títulos editoriais em `Playfair Display`, UI em `Plus Jakarta Sans`, paleta clara (`#FFFFFF`, `#F8FAFB`, `#DCF0F2`) e CTA principal em carvão (`#1F2426`).
- Ícones em moldura circular azul-gelo (`#DCF0F2`) com círculo interno branco e traço fino carvão (`#1F2426`).

## Evidence on Hand

- Ativos e HTML de referência em `mockups/` (`atividros_molduraria_vidra_aria_decora_o.html` e referências visuais `.jpg`).
- Massa de demonstração idempotente em `backend/scripts/seed_demo.py`.
- Suíte de testes automatizados cobrindo API (`backend/tests/`), componentes (`frontend/src/__tests__/`) e E2E browser (`frontend/e2e/jornada-principal.spec.js`).

## Product Principles

- Clareza operacional sob iluminação clara de balcão: superfícies limpas, hierarquia editorial nítida e alto contraste WCAG AA.
- Precisão matemática sem bloqueio humano: avisar divergências de preço ou estoque de forma persistente sem travar a oficina.
- Continuidade entre orçamento e bancada: dados fluem da Calculadora para o Pedido, Baixa Assistida e Histórico do Cliente sem retrabalho.
- Rótulos acessíveis estáveis: preservar semântica HTML/ARIA para suportar evolução contínua da interface e validação E2E.

## Accessibility & Inclusion

- Conformidade mínima WCAG 2.1 AA (contraste >= 4.5:1 em textos e badges), alvos táteis >= 44px no fluxo de oficina/Kanban/steppers, navegação completa por teclado em `<dialog>` e suporte a `prefers-reduced-motion`.
