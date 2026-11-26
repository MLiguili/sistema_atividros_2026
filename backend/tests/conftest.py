from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import Base, configurar_pragmas_sqlite, obter_db
from app.main import app
from app.models.usuario import Usuario
from app.services.autenticacao import criar_token_acesso, obter_hash_senha

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def engine():
    """
    Cria engine SQLite em memória com PRAGMA foreign_keys=ON para toda a sessão de testes.
    """
    engine_teste = create_async_engine(TEST_DATABASE_URL)
    configurar_pragmas_sqlite(engine_teste)
    async with engine_teste.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine_teste
    async with engine_teste.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_teste.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Fornece uma sessão assíncrona isolada com rollback ao final de cada teste.
    """
    sessao_async = async_sessionmaker(engine, expire_on_commit=False)
    async with sessao_async() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fornece cliente HTTP assíncrono ligado à sessão de testes via dependency override.
    """

    async def _obter_db_override():
        yield db_session

    app.dependency_overrides[obter_db] = _obter_db_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def cabecalho_autorizacao(db_session: AsyncSession) -> dict[str, str]:
    """
    Garante um usuário administrador de teste e retorna cabeçalho Bearer JWT válido.
    """
    nome_usuario = "admin_teste"
    resultado = await db_session.execute(select(Usuario).where(Usuario.nome_usuario == nome_usuario))
    usuario = resultado.scalar_one_or_none()

    if not usuario:
        usuario = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=obter_hash_senha("senha123"),
            nome_completo="Admin Teste",
            esta_ativo=True,
        )
        db_session.add(usuario)
        await db_session.commit()

    token = criar_token_acesso(dados={"sub": nome_usuario})
    return {"Authorization": f"Bearer {token}"}
