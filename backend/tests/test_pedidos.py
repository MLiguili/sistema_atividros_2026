from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoVidro


@pytest.mark.asyncio
async def test_criar_pedido_completo(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida criação de pedido completo com quadro sob medida e status iniciais saneados.
    """
    cliente = Cliente(nome="Pedro", sobrenome="Pedidos", telefone="11955550001")
    moldura = Moldura(
        codigo="M_ORDEM",
        quantidade=10,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("20.00"),
        cor="Preta",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("2.00"),
    )
    vidro = Vidro(espessura=Decimal("3.00"), tipo="incolor", area_disponivel_m2=Decimal("5.0000"))
    fundo = Fundo(tipo="Eucatex_Ped", espessura=Decimal("3.00"), area_disponivel_m2=Decimal("10.0000"))
    tab_v = TabelaPrecoVidro(tipo="incolor", preco_por_m2=Decimal("100.00"), area_minima_m2=Decimal("0.2500"))
    tab_f = TabelaPrecoFundo(tipo="Eucatex_Ped", preco_por_m2=Decimal("30.00"))
    db_session.add_all([cliente, moldura, vidro, fundo, tab_v, tab_f])
    await db_session.commit()
    for obj in (cliente, moldura, vidro, fundo):
        await db_session.refresh(obj)

    resposta = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                    "vidro_id": vidro.id,
                    "vidro_tipo": "incolor",
                    "fundo_id": fundo.id,
                    "quantidade": 1,
                    "obra_largura": "50.00",
                    "obra_altura": "50.00",
                    "preco_unitario": "100.00",
                }
            ],
        },
    )
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["status_geral"] == "rascunho"
    assert dados["status_producao"] == "pendente"
    assert dados["status_financeiro"] == "sem_pagamento"


@pytest.mark.asyncio
async def test_listar_pedidos(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida listagem autenticada de pedidos.
    """
    resposta = await client.get("/pedidos/", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


@pytest.mark.asyncio
async def test_atualizar_status_pedido(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida criação com item mínimo obrigatório e transição no eixo geral.
    """
    cliente = Cliente(nome="Ana", sobrenome="Status", telefone="11955550002")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    resp_vazio = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={"cliente_id": cliente.id, "itens": []},
    )
    assert resp_vazio.status_code == 422

    resp_post = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Serviço", "quantidade": 1, "preco_unitario": "50.00"}],
        },
    )
    pedido_id = resp_post.json()["id"]

    resp_patch = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status_geral"] == "confirmado"
