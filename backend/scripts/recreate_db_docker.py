"""Drop all tables on Docker PostgreSQL and recreate from current models + seed admin."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.session import Base
from app.models import *  # noqa: F401,F403 - register all models

DATABASE_URL = "postgresql+asyncpg://atividros:atividros_secret@localhost:5432/atividros"


async def main():
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("Dropped and recreated public schema")
    await engine.dispose()

    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created from current models")

    # Add pedido's StatusFinanceiro values (collision: financeiro.py registers first)
    async with engine.begin() as conn:
        from app.models.pedido import StatusFinanceiro as PedidoStatus
        for v in PedidoStatus:
            await conn.execute(
                text(f"ALTER TYPE statusfinanceiro ADD VALUE '{v.value}'")
            )
    print("Added pedido StatusFinanceiro values")

    from app.services.autenticacao import obter_hash_senha
    from app.models.usuario import Usuario

    Sessao = async_sessionmaker(engine, class_=AsyncSession)
    async with Sessao() as session:
        admin = await session.get(Usuario, 1)
        if not admin:
            session.add(Usuario(
                nome_usuario="admin",
                senha_hash=obter_hash_senha("admin123"),
                nome_completo="Administrador",
                esta_ativo=True,
            ))
            await session.commit()
            print("Admin user seeded")
        else:
            print("Admin already exists")

    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
