import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_buscar_pedido_por_id(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": 1, "itens": []}
    )
    pedido_id = criar_resp.json()["id"]
    
    resposta = await client.get(f"/pedidos/{pedido_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert resposta.json()["id"] == pedido_id

@pytest.mark.asyncio
async def test_pedido_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    resposta = await client.get("/pedidos/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404

@pytest.mark.asyncio
async def test_transicao_status_invalida(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": 1, "itens": []}
    )
    pedido_id = criar_resp.json()["id"]
    
    resp_patch = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "entregue"}
    )
    assert resp_patch.status_code == 400

@pytest.mark.asyncio
async def test_fluxo_completo_pedido(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": 1,
            "itens": [{"descricao": "Teste", "largura": 30, "altura": 40, "quantidade": 1, "preco_unitario": 100.0}],
            "valor_sinal": 50.0
        }
    )
    assert criar_resp.status_code == 201
    pedido = criar_resp.json()
    assert pedido["status_geral"] == "rascunho"
    
    pedido_id = pedido["id"]
    
    resp_confirmar = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"}
    )
    assert resp_confirmar.status_code == 200
    assert resp_confirmar.json()["status_geral"] == "confirmado"
    
    resp_sinal = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "financeiro", "novo_status": "sinal_recebido", "valor_sinal": 50.0}
    )
    assert resp_sinal.status_code == 200
    assert resp_sinal.json()["status_financeiro"] == "sinal_recebido"
    
    resp_producao = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "em_producao"}
    )
    assert resp_producao.status_code == 200
    assert resp_producao.json()["status_producao"] == "em_producao"

@pytest.mark.asyncio
async def test_listar_eventos_pedido(client: AsyncClient, cabecalho_autorizacao: dict):
    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": 1, "itens": []}
    )
    pedido_id = criar_resp.json()["id"]
    
    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"}
    )
    
    resp_eventos = await client.get(f"/pedidos/{pedido_id}/eventos", headers=cabecalho_autorizacao)
    assert resp_eventos.status_code == 200
    assert len(resp_eventos.json()) >= 2
