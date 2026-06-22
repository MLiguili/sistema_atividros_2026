import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_criar_conta_receber(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.post(
        "/financeiro/contas-receber",
        headers=cabecalho_autorizacao,
        json={"descricao": "Venda de quadro", "valor": 500.00, "data_vencimento": "2026-07-21"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pendente"


@pytest.mark.asyncio
async def test_listar_contas_receber(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/financeiro/contas-receber", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_receber_conta_parcial(client: AsyncClient, cabecalho_autorizacao: dict):
    criar = await client.post(
        "/financeiro/contas-receber",
        headers=cabecalho_autorizacao,
        json={"descricao": "Recebimento parcial", "valor": 1000.00, "data_vencimento": "2026-07-21"},
    )
    conta_id = criar.json()["id"]

    resp = await client.post(
        f"/financeiro/contas-receber/{conta_id}/receber",
        headers=cabecalho_autorizacao,
        json={"valor_recebido": 400.00},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "parcial"


@pytest.mark.asyncio
async def test_receber_conta_total(client: AsyncClient, cabecalho_autorizacao: dict):
    criar = await client.post(
        "/financeiro/contas-receber",
        headers=cabecalho_autorizacao,
        json={"descricao": "Recebimento total", "valor": 800.00, "data_vencimento": "2026-07-21"},
    )
    conta_id = criar.json()["id"]

    await client.post(
        f"/financeiro/contas-receber/{conta_id}/receber",
        headers=cabecalho_autorizacao,
        json={"valor_recebido": 800.00},
    )

    resp = await client.post(
        f"/financeiro/contas-receber/{conta_id}/receber",
        headers=cabecalho_autorizacao,
        json={"valor_recebido": 100.00},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_criar_conta_pagar(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.post(
        "/financeiro/contas-pagar",
        headers=cabecalho_autorizacao,
        json={"descricao": "Aluguel", "valor": 2000.00, "data_vencimento": "2026-07-10"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pendente"


@pytest.mark.asyncio
async def test_resumo_financeiro(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/financeiro/resumo", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_a_receber" in data
    assert "total_a_pagar" in data
    assert "saldo_previsto" in data


@pytest.mark.asyncio
async def test_fluxo_caixa(client: AsyncClient, cabecalho_autorizacao: dict):
    resp = await client.get("/financeiro/fluxo-caixa", headers=cabecalho_autorizacao)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
