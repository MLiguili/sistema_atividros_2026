from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)

SessaoAsyncLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def obter_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência para injetar a sessão do banco de dados nas rotas.
    """
    async with SessaoAsyncLocal() as sessao:
        yield sessao
