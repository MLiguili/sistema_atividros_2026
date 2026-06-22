# Arquitetura

Frontend (React)
↓
API (FastAPI)
↓
Services
↓
Repositories/ORM
↓
PostgreSQL

## Responsabilidades
- API: validação e orquestração.
- Services: regras de negócio.
- Repositories: acesso a dados.
- Models: persistência.
- Schemas: entrada/saída.
