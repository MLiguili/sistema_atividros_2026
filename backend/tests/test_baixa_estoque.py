from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Moldura


@pytest.mark.asyncio
async def test_baixa_estoque_sucesso(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida Baixa Assistida bem-sucedida avançando pedido para em_producao.
    """
    cliente = Cliente(nome="Teste", sobrenome="Silva", telefone="11999999999")
    moldura = Moldura(
        codigo="M01",
        quantidade=10,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("25.00"),
        cor="Dourada",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "descricao": "Quadro",
                    "obra_largura": 30,
                    "obra_altura": 40,
                    "quantidade": 2,
                    "preco_unitario": 100.0,
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                }
            ],
        },
    )
    pedido_id = criar_resp.json()["id"]

    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )
    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "na_fila"},
    )

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    assert resp_baixa.json()["pedido"]["status_producao"] == "em_producao"


@pytest.mark.asyncio
async def test_baixa_estoque_insuficiente_alerta_sem_bloquear(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida regra V1.0 onde ruptura de estoque permite saldo negativo (200 OK) com alertas_ruptura.
    """
    cliente = Cliente(nome="Teste2", sobrenome="Silva", telefone="11988888888")
    moldura = Moldura(
        codigo="M02",
        quantidade=1,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("25.00"),
        cor="Prata",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "descricao": "Quadro",
                    "obra_largura": 30,
                    "obra_altura": 40,
                    "quantidade": 5,
                    "preco_unitario": 100.0,
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                }
            ],
        },
    )
    pedido_id = criar_resp.json()["id"]

    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )
    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "producao", "novo_status": "na_fila"},
    )

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    dados = resp_baixa.json()
    assert dados["pedido"]["status_producao"] == "em_producao"
    assert dados["materiais_baixados"][0]["em_ruptura"] is True
    assert float(dados["materiais_baixados"][0]["saldo_atual"]) < 0
    assert len(dados["alertas_ruptura"]) == 1


@pytest.mark.asyncio
async def test_baixa_estoque_status_invalido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida que pedido em rascunho não pode executar baixa de estoque (400).
    """
    cliente = Cliente(nome="Teste3", sobrenome="Silva", telefone="11977777777")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Item", "quantidade": 1, "preco_unitario": "50.00"}],
        },
    )
    pedido_id = criar_resp.json()["id"]

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 400


@pytest.mark.asyncio
async def test_cancelamento_com_pagamento_sinaliza_estorno(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida que cancelar pedido com pagamento lançado sinaliza requer_estorno=True até estorno explícito.
    """
    cliente = Cliente(nome="Teste4", sobrenome="Silva", telefone="11966666666")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    criar_resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "descricao": "Quadro",
                    "obra_largura": 30,
                    "obra_altura": 40,
                    "quantidade": 1,
                    "preco_unitario": 200.0,
                }
            ],
        },
    )
    pedido_id = criar_resp.json()["id"]

    resp_pag = await client.post(
        f"/pedidos/{pedido_id}/pagamentos",
        headers=cabecalho_autorizacao,
        json={"valor": 50.0, "forma_pagamento": "pix"},
    )
    pag_id = resp_pag.json()["pagamentos"][0]["id"]

    resp_cancelar = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "cancelado"},
    )
    assert resp_cancelar.status_code == 200
    assert resp_cancelar.json()["status_geral"] == "cancelado"
    assert resp_cancelar.json()["requer_estorno"] is True

    resp_estornar = await client.post(
        f"/pedidos/{pedido_id}/pagamentos/{pag_id}/estornar",
        headers=cabecalho_autorizacao,
        json={"motivo": "Cancelamento"},
    )
    assert resp_estornar.status_code == 200
    assert resp_estornar.json()["status_financeiro"] == "estornado"
