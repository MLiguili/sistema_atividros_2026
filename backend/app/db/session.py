from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def configurar_pragmas_sqlite(engine_alvo: AsyncEngine) -> None:
    """
    Configura PRAGMAs essenciais do SQLite (foreign_keys, busy_timeout e WAL) em novas conexões.
    """
    if engine_alvo.url.get_backend_name() != "sqlite":
        return

    banco_em_memoria = engine_alvo.url.database in (None, "", ":memory:")

    @event.listens_for(engine_alvo.sync_engine, "connect")
    def _ao_conectar_sqlite(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        if not banco_em_memoria:
            cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


engine = create_async_engine(settings.database_url, echo=settings.debug)
configurar_pragmas_sqlite(engine)

SessaoAsyncLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Classe base declarativa para todos os modelos SQLAlchemy da aplicação.
    """


async def obter_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência FastAPI para injetar uma sessão assíncrona do banco de dados por requisição.
    """
    async with SessaoAsyncLocal() as sessao:
        yield sessao
