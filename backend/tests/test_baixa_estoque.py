import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.estoque import Moldura, Vidro, Fundo
from app.models.cliente import Cliente


@pytest.mark.asyncio
async def test_baixa_estoque_sucesso(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Teste", sobrenome="Silva", telefone="11999999999")
    moldura = Moldura(codigo="M01", quantidade=10, preco_venda=50.0, preco_custo=25.0, cor="Dourada", tamanho_barra=3.0, largura_barra=3.0)
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    criar_resp = await client.post("/pedidos/", headers=cabecalho_autorizacao, json={
        "cliente_id": cliente.id,
        "itens": [{"descricao": "Quadro", "largura": 30, "altura": 40, "quantidade": 2, "preco_unitario": 100.0, "moldura_id": moldura.id}]
    })
    pedido_id = criar_resp.json()["id"]

    await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "geral", "novo_status": "confirmado"})
    await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "producao", "novo_status": "na_fila"})

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    assert resp_baixa.json()["status_producao"] == "em_producao"


@pytest.mark.asyncio
async def test_baixa_estoque_estoque_insuficiente(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Teste2", sobrenome="Silva", telefone="11988888888")
    moldura = Moldura(codigo="M02", quantidade=1, preco_venda=50.0, preco_custo=25.0, cor="Prata", tamanho_barra=3.0, largura_barra=3.0)
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    criar_resp = await client.post("/pedidos/", headers=cabecalho_autorizacao, json={
        "cliente_id": cliente.id,
        "itens": [{"descricao": "Quadro", "largura": 30, "altura": 40, "quantidade": 5, "preco_unitario": 100.0, "moldura_id": moldura.id}]
    })
    pedido_id = criar_resp.json()["id"]

    await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "geral", "novo_status": "confirmado"})
    await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "producao", "novo_status": "na_fila"})

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 400
    assert "insuficiente" in resp_baixa.json()["detail"].lower()


@pytest.mark.asyncio
async def test_baixa_estoque_status_invalido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Teste3", sobrenome="Silva", telefone="11977777777")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post("/pedidos/", headers=cabecalho_autorizacao, json={
        "cliente_id": cliente.id, "itens": []
    })
    pedido_id = criar_resp.json()["id"]

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code in [200, 400]


@pytest.mark.asyncio
async def test_cancelamento_com_sinal_estorna(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    cliente = Cliente(nome="Teste4", sobrenome="Silva", telefone="11966666666")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post("/pedidos/", headers=cabecalho_autorizacao, json={
        "cliente_id": cliente.id,
        "itens": [{"descricao": "Quadro", "largura": 30, "altura": 40, "quantidade": 1, "preco_unitario": 200.0}],
        "valor_sinal": 50.0
    })
    pedido_id = criar_resp.json()["id"]

    await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "financeiro", "novo_status": "sinal_recebido", "valor_sinal": 50.0})

    resp_cancelar = await client.patch(f"/pedidos/{pedido_id}/status", headers=cabecalho_autorizacao, json={"eixo": "geral", "novo_status": "cancelado"})
    assert resp_cancelar.status_code == 200
    assert resp_cancelar.json()["status_geral"] == "cancelado"
    assert resp_cancelar.json()["status_financeiro"] == "estornado"
