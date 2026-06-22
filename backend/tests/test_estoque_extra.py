import pytest
from httpx import AsyncClient

# === FUNDOS ===
@pytest.mark.asyncio
async def test_criar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "MDF",
            "espessura": 3.0,
            "quantidade": 20,
            "largura": 100.0,
            "altura": 200.0,
            "cor": "Branco"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "MDF"

@pytest.mark.asyncio
async def test_listar_fundos(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/estoque/fundos", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "MDF",
            "espessura": 3.0,
            "quantidade": 20,
            "largura": 100.0,
            "altura": 200.0
        }
    )
    fundo_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/estoque/fundos/{fundo_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 25}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 25

@pytest.mark.asyncio
async def test_deletar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "Acrilico",
            "espessura": 2.0,
            "quantidade": 10,
            "largura": 50.0,
            "altura": 50.0
        }
    )
    fundo_id = criar_resp.json()["id"]
    
    resp_del = await client.delete(f"/estoque/fundos/{fundo_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204

@pytest.mark.asyncio
async def test_fundo_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/estoque/fundos/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404

# === SUPLEMENTOS ===
@pytest.mark.asyncio
async def test_criar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Parafuso",
            "quantidade": 100,
            "unidade": "unidade"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Parafuso"

@pytest.mark.asyncio
async def test_listar_suplementos(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/estoque/suplementos", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Cola",
            "quantidade": 50,
            "unidade": "ml"
        }
    )
    sup_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/estoque/suplementos/{sup_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 100}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 100

@pytest.mark.asyncio
async def test_deletar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Prego",
            "quantidade": 200,
            "unidade": "unidade"
        }
    )
    sup_id = criar_resp.json()["id"]
    
    resp_del = await client.delete(f"/estoque/suplementos/{sup_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204

# === VIDROS ===
@pytest.mark.asyncio
async def test_atualizar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={
            "espessura": 4.0,
            "tipo": "espelho",
            "quantidade": 8,
            "largura_chapa": 150.0,
            "altura_chapa": 200.0,
            "cor": "Dourado"
        }
    )
    vidro_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/estoque/vidros/{vidro_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 12}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 12

@pytest.mark.asyncio
async def test_deletar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={
            "espessura": 2.0,
            "tipo": "incolor",
            "quantidade": 15,
            "largura_chapa": 100.0,
            "altura_chapa": 100.0
        }
    )
    vidro_id = criar_resp.json()["id"]
    
    resp_del = await client.delete(f"/estoque/vidros/{vidro_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204

@pytest.mark.asyncio
async def test_vidro_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/estoque/vidros/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404

# === MOLDURAS ===
@pytest.mark.asyncio
async def test_atualizar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_UPDATE",
            "quantidade": 10,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Azul",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0
        }
    )
    moldura_id = criar_resp.json()["id"]
    
    resp_put = await client.put(
        f"/estoque/molduras/{moldura_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 15}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 15

@pytest.mark.asyncio
async def test_deletar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_DELETE",
            "quantidade": 5,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Verde",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0
        }
    )
    moldura_id = criar_resp.json()["id"]
    
    resp_del = await client.delete(f"/estoque/molduras/{moldura_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204
