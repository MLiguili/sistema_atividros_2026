import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_criar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida cadastro de moldura com preço por metro e estoque mínimo.
    """
    resposta = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_TESTE",
            "quantidade": 10,
            "estoque_minimo": 4,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Preto",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0,
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["codigo"] == "M_TESTE"
    assert resposta.json()["estoque_minimo"] == 4


@pytest.mark.asyncio
async def test_listar_molduras(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida listagem autenticada de molduras e filtro de estoque crítico.
    """
    resposta = await client.get("/estoque/molduras", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

    criticas = await client.get("/estoque/molduras?critico=true", headers=cabecalho_autorizacao)
    assert criticas.status_code == 200


@pytest.mark.asyncio
async def test_criar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida criação de vidro com saldo contínuo em m².
    """
    resposta = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={
            "espessura": 3.0,
            "tipo": "incolor",
            "area_disponivel_m2": "7.5000",
            "estoque_minimo_m2": "2.0000",
            "cor": "Verde",
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "incolor"
    assert resposta.json()["area_disponivel_m2"] == "7.5000"
