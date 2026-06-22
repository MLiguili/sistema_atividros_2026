# AGENTS — Sistema Atividros

Monorepo: `backend/` (Python 3.12+, FastAPI, Poetry) + `frontend/` (React 19, Vite 8, npm).

## Commands

| Context | Command |
|---------|---------|
| Backend dev | `cd backend && poetry run uvicorn app.main:app --reload` |
| Backend test | `cd backend && poetry run pytest` |
| Backend test (single) | `cd backend && poetry run pytest tests/test_foo.py -k test_name -v` |
| Backend lint | `cd backend && poetry run ruff check .` |
| Backend lint+fix | `cd backend && poetry run ruff check --fix .` |
| Frontend dev | `cd frontend && npm run dev` |
| Frontend build | `cd frontend && npm run build` |
| Frontend lint | `cd frontend && npm run lint` |

## Architecture

```
FastAPI routers → Services (business logic) → Models (ORM) / Schemas (Pydantic)
```

- **Routers** (`app/api/`): validation + orchestration only
- **Services** (`app/services/`): pure business logic, no HTTP imports
- **Models** (`app/models/`): SQLAlchemy async ORM
- **Schemas** (`app/schemas/`): Pydantic v2 request/response

## Business rules (non-negotiable)

1. **3-axis order status** — each `Pedido` has three independent axes:
   - `status_geral`: rascunho → confirmado → cancelado/entregue/arquivado
   - `status_producao`: pendente → aguardando_material → em_producao → para_embalar → pronto_entrega → entregue
   - `status_financeiro`: sem_pagamento → sinal_recebido → pago_total → estornado
   - Transitions are validated per-axis by the service; all transitions log to `PedidoEvento`.
2. **Stock write-off** — triggered on `na_fila → em_producao`, requires explicit API call (`POST /{id}/baixa-estoque`). Also reverts on cancel (restock with deposit flag).
3. **Dimension propagation** — calculator propagates inside-out: obra → paspatour → molduras → quadro_final. Prices are suggested, user can override.
4. **Order numbering** — auto-generated `{year}/{5-digit sequential}`, immutable after creation.

## Database

- Dev: `backend/test_atividros.db` (SQLite via aiosqlite)
- Migrations: Alembic (`backend/alembic.ini` + `backend/migrations/`)
- Never remove migration files
- Key entities: Usuario, Cliente, Moldura, Vidro, Fundo, Suplemento, Pedido, ItemPedido, PedidoEvento, TabelaPrecoVidro, TabelaPrecoPaspatour

## Testing

- `pytest` with `asyncio_mode = auto` (async tests auto-detected)
- httpx `AsyncClient` with `ASGITransport` for API tests (see `tests/conftest.py`)
- Coverage target: `>=80%` (CI fails below 50%)

## Style

- Python: type hints everywhere, avoid `Any`, small functions, Ruff (line-length 120, target py312)
- Frontend: ESLint + react-hooks + react-refresh rules
- API: REST, Pydantic validation, consistent error responses
- Commit: `{type}: {description}`

## Detailed docs

| File | Content |
|------|---------|
| `docs/PROJECT.md` | Stack overview, modules |
| `docs/DOMAIN.md` | Business rules (pedido, estoque) |
| `docs/ARCHITECTURE.md` | Layer responsibilities |
| `docs/CODING_STANDARDS.md` | Code conventions |
| `docs/DATABASE.md` | Entity conventions |
| `docs/API.md` | REST conventions |
| `docs/ROADMAP.md` | Done / upcoming |
| `docs/DECISIONS.md` | Architecture Decision Records |
