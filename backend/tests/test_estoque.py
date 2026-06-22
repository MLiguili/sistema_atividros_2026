import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.estoque import Moldura

@pytest.mark.asyncio
async def test_criar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_TESTE",
            "quantidade": 10,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Preto",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["codigo"] == "M_TESTE"

@pytest.mark.asyncio
async def test_listar_molduras(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/estoque/molduras", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_criar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={
            "espessura": 3.0,
            "tipo": "incolor",
            "quantidade": 5,
            "largura_chapa": 100.0,
            "altura_chapa": 150.0,
            "cor": "Verde"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "incolor"
