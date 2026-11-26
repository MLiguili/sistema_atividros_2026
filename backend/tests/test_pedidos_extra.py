import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente


@pytest.mark.asyncio
async def test_buscar_pedido_por_id(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida busca detalhada de pedido por ID.
    """
    cliente = Cliente(nome="Busca", sobrenome="Pedido", telefone="11966660001")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Troca", "quantidade": 1, "preco_unitario": "60.00"}],
        },
    )
    pedido_id = criar_resp.json()["id"]

    resposta = await client.get(f"/pedidos/{pedido_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert resposta.json()["id"] == pedido_id


@pytest.mark.asyncio
async def test_pedido_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida retorno 404 para pedido inexistente.
    """
    resposta = await client.get("/pedidos/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404


@pytest.mark.asyncio
async def test_transicao_status_invalida(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida bloqueio de transição inválida no eixo geral (rascunho -> entregue).
    """
    cliente = Cliente(nome="Transicao", sobrenome="Invalida", telefone="11966660002")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Quadro", "quantidade": 1, "preco_unitario": "100.00"}],
        },
    )
    pedido_id = criar_resp.json()["id"]

    resp_patch = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "entregue"},
    )
    assert resp_patch.status_code == 400


@pytest.mark.asyncio
async def test_fluxo_completo_pedido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida fluxo completo entre os 3 eixos saneados (sem entregue na produção e sem PATCH direto para em_producao).
    """
    cliente = Cliente(nome="Fluxo", sobrenome="Completo", telefone="11966660003")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Teste", "quantidade": 1, "preco_unitario": "100.00"}],
        },
    )
    assert criar_resp.status_code == 201
    pedido_id = criar_resp.json()["id"]

    # Pagamento parcial confirma automaticamente e atualiza financeiro
    resp_pag = await client.post(
        f"/pedidos/{pedido_id}/pagamentos",
        headers=cabecalho_autorizacao,
        json={"valor": "50.00", "forma_pagamento": "pix"},
    )
    assert resp_pag.status_code == 201
    assert resp_pag.json()["status_geral"] == "confirmado"
    assert resp_pag.json()["status_financeiro"] == "pagamento_parcial"

    # PATCH direto para em_producao é bloqueado; exige Baixa Assistida
    resp_prod_direto = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "em_producao"},
    )
    assert resp_prod_direto.status_code == 400

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    assert resp_baixa.json()["pedido"]["status_producao"] == "em_producao"

    # Avança produção até pronto_entrega (entregue não existe em producao)
    resp_emb = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "embalando"},
    )
    assert resp_emb.status_code == 200

    resp_pronto = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "pronto_entrega"},
    )
    assert resp_pronto.status_code == 200

    resp_prod_entregue = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "entregue"},
    )
    assert resp_prod_entregue.status_code == 400


@pytest.mark.asyncio
async def test_listar_eventos_pedido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida trilha cronológica de eventos após criação e confirmação.
    """
    cliente = Cliente(nome="Eventos", sobrenome="Teste", telefone="11966660004")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Item", "quantidade": 1, "preco_unitario": "40.00"}],
        },
    )
    pedido_id = criar_resp.json()["id"]

    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )

    resp_eventos = await client.get(f"/pedidos/{pedido_id}/eventos", headers=cabecalho_autorizacao)
    assert resp_eventos.status_code == 200
    assert len(resp_eventos.json()) >= 2
