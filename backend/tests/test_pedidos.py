import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.estoque import Moldura, Vidro, Fundo

@pytest.mark.asyncio
async def test_criar_pedido_completo(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    moldura = Moldura(codigo="M_ORDEM", quantidade=10, preco_venda=50.0, preco_custo=20.0, 
                      cor="Preta", tamanho_barra=3.0, largura_barra=2.0)
    vidro = Vidro(espessura=3.0, tipo="incolor", quantidade=5, largura_chapa=100, altura_chapa=100)
    fundo = Fundo(tipo="Eucatex", espessura=3.0, largura=100, altura=100, quantidade=10)
    
    db_session.add_all([moldura, vidro, fundo])
    await db_session.commit()
    await db_session.refresh(moldura)
    await db_session.refresh(vidro)
    await db_session.refresh(fundo)

    resposta = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": 1,
            "itens": [
                {
                    "moldura_id": moldura.id,
                    "vidro_id": vidro.id,
                    "fundo_id": fundo.id,
                    "quantidade": 1,
                    "largura": 50.0,
                    "altura": 50.0,
                    "preco_unitario": 100.0
                }
            ]
        }
    )
    
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["status_geral"] == "rascunho"
    assert dados["status_producao"] == "pendente"
    assert dados["status_financeiro"] == "sem_pagamento"

@pytest.mark.asyncio
async def test_listar_pedidos(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/pedidos/", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)

@pytest.mark.asyncio
async def test_atualizar_status_pedido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    resp_post = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": 1,
            "itens": []
        }
    )
    pedido_id = resp_post.json()["id"]

    resp_patch = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={
            "eixo": "geral",
            "novo_status": "confirmado"
        }
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status_geral"] == "confirmado"
