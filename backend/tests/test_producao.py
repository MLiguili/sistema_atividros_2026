import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Moldura
from app.models.cliente import Cliente


@pytest.mark.asyncio
async def test_listar_fila_producao(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/producao/fila", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_resumo_producao(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/producao/resumo", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    data = resp.json()
    assert "pendente" in data
    assert "em_producao" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_avancar_pedido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Prod", sobrenome="Teste", telefone="11955555555")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": cliente.id, "itens": [{"descricao": "Teste", "largura": 30, "altura": 40, "quantidade": 1, "preco_unitario": 100.0}]},
    )
    pedido_id = criar_resp.json()["id"]

    resp = await client.post(f"/producao/{pedido_id}/avancar", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert resp.json()["status_producao"] == "em_producao"


@pytest.mark.asyncio
async def test_avancar_pedido_inexistente(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.post("/producao/99999/avancar", headers=cabecalho_autorizacao)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_iniciar_lote_vazio(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.post("/producao/iniciar", headers=cabecalho_autorizacao, json={"pedido_ids": []})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_iniciar_lote_com_estoque(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Lote", sobrenome="Teste", telefone="11944444444")
    moldura = Moldura(codigo="MLOTE", quantidade=10, preco_venda=50.0, preco_custo=20.0, cor="Preta", tamanho_barra=3.0, largura_barra=2.0)
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"moldura_id": moldura.id, "largura": 30, "altura": 40, "quantidade": 2, "preco_unitario": 100.0}],
        },
    )
    pedido_id = criar_resp.json()["id"]

    resp = await client.post("/producao/iniciar", headers=cabecalho_autorizacao, json={"pedido_ids": [pedido_id]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_processados"] == 1
    assert data["total_erros"] == 0
    assert data["resultados"][0]["sucesso"] is True


@pytest.mark.asyncio
async def test_avancar_fluxo_completo(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Fluxo", sobrenome="Teste", telefone="11933333333")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": cliente.id, "itens": [{"descricao": "Teste", "largura": 30, "altura": 40, "quantidade": 1, "preco_unitario": 100.0}]},
    )
    pedido_id = criar_resp.json()["id"]

    await client.post(f"/producao/{pedido_id}/avancar", headers=cabecalho_autorizacao)

    resp2 = await client.post(f"/producao/{pedido_id}/avancar", headers=cabecalho_autorizacao)
    assert resp2.status_code == 200
    assert resp2.json()["status_producao"] == "para_embalar"

    resp3 = await client.post(f"/producao/{pedido_id}/avancar", headers=cabecalho_autorizacao)
    assert resp3.status_code == 200
    assert resp3.json()["status_producao"] == "pronto_entrega"

    resp4 = await client.post(f"/producao/{pedido_id}/avancar", headers=cabecalho_autorizacao)
    assert resp4.status_code == 200
    assert resp4.json()["status_producao"] == "entregue"
    assert resp4.json()["status_geral"] == "entregue"
