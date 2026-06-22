import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_buscar_cliente_por_id(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Cliente ID",
            "sobrenome": "Teste",
            "telefone": "11999990000"
        }
    )
    cliente_id = criar_resp.json()["id"]
    
    resposta = await client.get(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cliente ID"

@pytest.mark.asyncio
async def test_cliente_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/clientes/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404

@pytest.mark.asyncio
async def test_criar_cliente_sem_email(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Sem",
            "sobrenome": "Email",
            "telefone": "11999991111"
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["email"] is None

@pytest.mark.asyncio
async def test_criar_cliente_email_vazio(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Email",
            "sobrenome": "Vazio",
            "telefone": "11999992222",
            "email": ""
        }
    )
    assert resposta.status_code == 201
    assert resposta.json()["email"] is None

@pytest.mark.asyncio
async def test_deletar_cliente(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "ParaDeletar",
            "sobrenome": "Teste",
            "telefone": "11999993333"
        }
    )
    cliente_id = criar_resp.json()["id"]
    
    resposta = await client.delete(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 204
    
    verificar = await client.get(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert verificar.status_code == 404
