from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

import app.models  # noqa: F401
from app.db.session import Base
from app.models.pedido import SequenciaNumeracao


def test_postgres_asyncpg_e_compilacao_ddl_15_tabelas():
    """
    Garante que o driver asyncpg está disponível e todas as 15 tabelas compilam DDL válido para PostgreSQL.
    """
    import asyncpg  # noqa: F401

    pg_dialect = postgresql.dialect()
    tabelas = list(Base.metadata.sorted_tables)
    assert len(tabelas) == 15

    for tabela in tabelas:
        ddl = str(CreateTable(tabela).compile(dialect=pg_dialect))
        assert f"CREATE TABLE {tabela.name}" in ddl


def test_postgres_upsert_sequencia_numeracao_compila():
    """
    Valida que a instrução atômica ON CONFLICT DO UPDATE de numeração compila corretamente no dialeto PostgreSQL.
    """
    stmt = postgresql.insert(SequenciaNumeracao).values(ano=2026, ultimo_valor=1)
    upsert = stmt.on_conflict_do_update(
        index_elements=["ano"],
        set_={"ultimo_valor": SequenciaNumeracao.ultimo_valor + 1},
    ).returning(SequenciaNumeracao.ultimo_valor)

    sql_compilado = str(upsert.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (ano) DO UPDATE" in sql_compilado
    assert "RETURNING sequencia_numeracao.ultimo_valor" in sql_compilado
