import pytest
from httpx import AsyncClient

# === TABELA PREÇO VIDRO ===
@pytest.mark.asyncio
async def test_criar_preco_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "antireflexo",
            "preco_por_m2": 150.0,
            "descricao": "Vidro antireflexo premium"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "antireflexo"
    assert float(resposta.json()["preco_por_m2"]) == 150.0

@pytest.mark.asyncio
async def test_listar_tabela_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/calculadora/tabela-vidro")
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_preco_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "incolor",
            "preco_por_m2": 80.0
        }
    )
    vidro_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/calculadora/tabela-vidro/{vidro_id}",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 95.0, "descricao": "Vidro incolor atualizado"}
    )
    assert resp_put.status_code == 200
    assert float(resp_put.json()["preco_por_m2"]) == 95.0

@pytest.mark.asyncio
async def test_preco_vidro_ja_existe(client: AsyncClient, cabecalho_autorizacao: dict):
    await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "espelho",
            "preco_por_m2": 120.0
        }
    )
    
    resposta = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "espelho",
            "preco_por_m2": 130.0
        }
    )
    assert resposta.status_code == 400

# === TABELA PREÇO PASPATOUR ===
@pytest.mark.asyncio
async def test_criar_preco_paspatour(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/calculadora/tabela-paspatour",
        headers=cabecalho_autorizacao,
        json={
            "descricao": "Paspatour branco 3cm",
            "preco_por_m2": 25.0
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["descricao"] == "Paspatour branco 3cm"

@pytest.mark.asyncio
async def test_listar_tabela_paspatour(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/calculadora/tabela-paspatour")
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_preco_paspatour(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/calculadora/tabela-paspatour",
        headers=cabecalho_autorizacao,
        json={
            "descricao": "Paspatour preto 2cm",
            "preco_por_m2": 20.0
        }
    )
    paspatour_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/calculadora/tabela-paspatour/{paspatour_id}",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 28.0}
    )
    assert resp_put.status_code == 200
    assert float(resp_put.json()["preco_por_m2"]) == 28.0

@pytest.mark.asyncio
async def test_paspatour_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.put(
        "/calculadora/tabela-paspatour/99999",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 30.0}
    )
    assert resposta.status_code == 404

@pytest.mark.asyncio
async def test_vidro_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.put(
        "/calculadora/tabela-vidro/99999",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 30.0}
    )
    assert resposta.status_code == 404
