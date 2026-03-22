import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_criar_cliente(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "João",
            "sobrenome": "Teste",
            "telefone": "11999999999",
            "email": "joao_teste@exemplo.com",
            "endereco": "Rua Teste, 123",
            "cep": "01001-000"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "João"

@pytest.mark.asyncio
async def test_listar_clientes(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/clientes/", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_cliente(client: AsyncClient, cabecalho_autorizacao: dict):
    # Criar cliente primeiro
    criar_resp = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Maria",
            "sobrenome": "Atualizar",
            "telefone": "11888888888"
        }
    )
    cliente_id = criar_resp.json()["id"]

    # Atualizar telefone
    resp_put = await client.put(
        f"/clientes/{cliente_id}",
        headers=cabecalho_autorizacao,
        json={"telefone": "11000000000"}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["telefone"] == "11000000000"
