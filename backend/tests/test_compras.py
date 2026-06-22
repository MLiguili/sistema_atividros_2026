import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Moldura


@pytest.mark.asyncio
async def test_criar_fornecedor(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.post(
        "/compras/fornecedores",
        headers=cabecalho_autorizacao,
        json={"nome": "Fornecedor Teste", "telefone": "11911111111"},
    )
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Fornecedor Teste"


@pytest.mark.asyncio
async def test_listar_fornecedores(client: AsyncClient, cabecalho_autorizacao: dict):
    await client.post(
        "/compras/fornecedores",
        headers=cabecalho_autorizacao,
        json={"nome": "Fornecedor A", "telefone": "11922222222"},
    )
    resp = await client.get("/compras/fornecedores", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_criar_ordem_compra(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    resp_forn = await client.post(
        "/compras/fornecedores",
        headers=cabecalho_autorizacao,
        json={"nome": "Fornecedor OC", "telefone": "11933333333"},
    )
    forn_id = resp_forn.json()["id"]

    moldura = Moldura(codigo="COMPRA_TESTE", quantidade=0, preco_venda=50, preco_custo=20, cor="Azul", tamanho_barra=3, largura_barra=2)
    db_session.add(moldura)
    await db_session.commit()
    await db_session.refresh(moldura)

    resp = await client.post(
        "/compras/ordens",
        headers=cabecalho_autorizacao,
        json={
            "fornecedor_id": forn_id,
            "itens": [{"produto_tipo": "moldura", "produto_id": moldura.id, "quantidade_solicitada": 10, "preco_unitario": 25.0}],
        },
    )
    assert resp.status_code == 201
    dados = resp.json()
    assert dados["status"] == "pendente"
    assert len(dados["itens"]) == 1


@pytest.mark.asyncio
async def test_listar_ordens(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/compras/ordens", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_sugerir_compras(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/compras/sugerir", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_receber_ordem(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    resp_forn = await client.post(
        "/compras/fornecedores",
        headers=cabecalho_autorizacao,
        json={"nome": "Fornecedor Receb", "telefone": "11944444444"},
    )
    forn_id = resp_forn.json()["id"]

    moldura = Moldura(codigo="RECEBER_TESTE", quantidade=0, preco_venda=50, preco_custo=20, cor="Verde", tamanho_barra=3, largura_barra=2)
    db_session.add(moldura)
    await db_session.commit()
    await db_session.refresh(moldura)

    resp_ordem = await client.post(
        "/compras/ordens",
        headers=cabecalho_autorizacao,
        json={
            "fornecedor_id": forn_id,
            "itens": [{"produto_tipo": "moldura", "produto_id": moldura.id, "quantidade_solicitada": 5, "preco_unitario": 25.0}],
        },
    )
    ordem_id = resp_ordem.json()["id"]
    item_id = resp_ordem.json()["itens"][0]["id"]

    resp_receber = await client.post(
        f"/compras/ordens/{ordem_id}/receber",
        headers=cabecalho_autorizacao,
        json={"itens": [{"item_id": item_id, "quantidade_recebida": 5}]},
    )
    assert resp_receber.status_code == 200
    assert resp_receber.json()["status"] == "recebida"

    await db_session.refresh(moldura)
    assert moldura.quantidade == 5
