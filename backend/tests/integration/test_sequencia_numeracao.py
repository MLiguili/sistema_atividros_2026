import asyncio
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import Base, configurar_pragmas_sqlite
from app.services.sequencia import gerar_numero_pedido


@pytest.mark.asyncio
async def test_sequencia_persiste_entre_restarts_e_vira_ano(tmp_path: Path):
    """
    Valida geração monotônica YYYYNNNNN, persistência após recriação de engine e virada de ano.
    """
    caminho_db = tmp_path / "seq_restart.db"
    url_db = f"sqlite+aiosqlite:///{caminho_db.as_posix()}"

    engine1 = create_async_engine(url_db)
    configurar_pragmas_sqlite(engine1)
    async with engine1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    fabrica1 = async_sessionmaker(engine1, expire_on_commit=False)
    async with fabrica1() as sessao:
        async with sessao.begin():
            n1 = await gerar_numero_pedido(sessao, ano=2026)
            n2 = await gerar_numero_pedido(sessao, ano=2026)
    await engine1.dispose()

    assert n1 == "202600001"
    assert n2 == "202600002"

    # Simula reinício completo do servidor com novo engine apontando para o mesmo arquivo SQLite
    engine2 = create_async_engine(url_db)
    configurar_pragmas_sqlite(engine2)
    fabrica2 = async_sessionmaker(engine2, expire_on_commit=False)
    async with fabrica2() as sessao:
        async with sessao.begin():
            n3 = await gerar_numero_pedido(sessao, ano=2026)
            n_ano_novo = await gerar_numero_pedido(sessao, ano=2027)
    await engine2.dispose()

    assert n3 == "202600003"
    assert n_ano_novo == "202700001"


@pytest.mark.asyncio
async def test_sequencia_concorrente_sem_colisao(tmp_path: Path):
    """
    Garante ausência de colisões ao gerar números de pedido concorrentemente via asyncio.gather.
    """
    caminho_db = tmp_path / "seq_concorrente.db"
    url_db = f"sqlite+aiosqlite:///{caminho_db.as_posix()}"

    engine = create_async_engine(url_db)
    configurar_pragmas_sqlite(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    fabrica = async_sessionmaker(engine, expire_on_commit=False)

    async def _gerar_um() -> str:
        async with fabrica() as sessao:
            async with sessao.begin():
                return await gerar_numero_pedido(sessao, ano=2026)

    numeros = await asyncio.gather(*[_gerar_um() for _ in range(15)])
    await engine.dispose()

    assert len(set(numeros)) == 15
    assert sorted(numeros) == [f"2026{i:05d}" for i in range(1, 16)]


@pytest.mark.asyncio
async def test_schema_v1_cria_15_tabelas(tmp_path: Path):
    """
    Confirma que os modelos SQLAlchemy criam todas as 15 tabelas esperadas na V1.0.
    """
    caminho_db = tmp_path / "schema_15.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{caminho_db.as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        tabelas = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    await engine.dispose()

    esperadas = {
        "usuarios",
        "clientes",
        "molduras",
        "vidros",
        "fundos",
        "suplementos",
        "tabela_preco_vidro",
        "tabela_preco_fundo",
        "tabela_preco_paspatour",
        "sequencia_numeracao",
        "pedidos",
        "itens_pedido",
        "itens_pedido_moldura",
        "pagamentos_pedido",
        "pedidos_eventos",
    }
    assert esperadas.issubset(tabelas)
