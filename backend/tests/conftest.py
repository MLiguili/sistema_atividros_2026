import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db.session import Base, obter_db

# Banco de dados de teste em memoria para evitar I/O errors no WSL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Removida a fixture event_loop customizada (depreciada no pytest-asyncio 0.23+)


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    SessaoAsync = async_sessionmaker(engine, expire_on_commit=False)
    async with SessaoAsync() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _obter_db_override():
        yield db_session

    app.dependency_overrides[obter_db] = _obter_db_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def cabecalho_autorizacao(db_session: AsyncSession):
    from app.models.usuario import Usuario
    from app.services.autenticacao import obter_hash_senha, criar_token_acesso
    from sqlalchemy import select

    nome_usuario = "admin_teste"
    resultado = await db_session.execute(select(Usuario).where(Usuario.nome_usuario == nome_usuario))
    usuario = resultado.scalar_one_or_none()

    if not usuario:
        usuario = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=obter_hash_senha("senha123"),
            nome_completo="Admin Teste",
            esta_ativo=True
        )
        db_session.add(usuario)
        await db_session.commit()
    
    token = criar_token_acesso(dados={"sub": nome_usuario})
    return {"Authorization": f"Bearer {token}"}

