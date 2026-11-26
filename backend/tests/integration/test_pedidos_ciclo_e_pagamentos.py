from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoPaspatour, TabelaPrecoVidro


@pytest.mark.asyncio
async def test_ciclo_pedido_mix_3_itens_desconto_frete_pagamentos_e_estorno(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida criação multi-item, preço abaixo do sugerido, frete+desconto, pagamentos parciais, confirmação e estorno.
    """
    cliente = Cliente(nome="Marina", sobrenome="Costa", telefone="11991234567")
    moldura = Moldura(
        codigo="M_CICLO",
        quantidade=10,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("20.00"),
        cor="Preta",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    vidro = Vidro(tipo="incolor", espessura=Decimal("3.00"), area_disponivel_m2=Decimal("8.0000"))
    fundo = Fundo(tipo="MDF_CICLO", espessura=Decimal("3.00"), area_disponivel_m2=Decimal("8.0000"))
    tab_v = TabelaPrecoVidro(tipo="incolor_ciclo", preco_por_m2=Decimal("100.00"), area_minima_m2=Decimal("0.2500"))
    tab_f = TabelaPrecoFundo(tipo="MDF_CICLO", preco_por_m2=Decimal("30.00"))
    tab_p = TabelaPrecoPaspatour(descricao="Pasp Ciclo", preco_por_m2=Decimal("60.00"))
    db_session.add_all([cliente, moldura, vidro, fundo, tab_v, tab_f, tab_p])
    await db_session.commit()
    for obj in (cliente, moldura, vidro, fundo, tab_p):
        await db_session.refresh(obj)

    resp_criar = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "frete": "30.00",
            "desconto_valor": "10.00",
            "desconto_tipo": "percentual",
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 1,
                    "obra_largura": "40.00",
                    "obra_altura": "50.00",
                    "paspatour": True,
                    "tamanho_paspatour": "5.00",
                    "paspatour_id": tab_p.id,
                    "vidro_tipo": "incolor_ciclo",
                    "vidro_id": vidro.id,
                    "fundo_id": fundo.id,
                    "mao_de_obra": "20.00",
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                    "preco_unitario": "150.00",
                },
                {
                    "tipo_item": "vidro_avulso",
                    "quantidade": 1,
                    "obra_largura": "30.00",
                    "obra_altura": "40.00",
                    "vidro_tipo": "incolor_ciclo",
                    "vidro_id": vidro.id,
                },
                {
                    "tipo_item": "servico_livre",
                    "descricao": "Instalação na residência",
                    "quantidade": 1,
                    "preco_unitario": "80.00",
                },
            ],
        },
    )
    assert resp_criar.status_code == 201
    pedido = resp_criar.json()
    pedido_id = pedido["id"]
    assert pedido["status_geral"] == "rascunho"
    assert pedido["data_validade_orcamento"] is not None
    assert pedido["itens"][0]["abaixo_do_sugerido"] is True
    assert pedido["tem_item_abaixo_do_sugerido"] is True
    assert pedido["itens"][1]["preco_unitario"] == "25.00"  # area_min 0.25 * 100
    # Subtotal = 150 + 25 + 80 = 255.00; desconto 10% = 25.50; + frete 30.00 = 259.50
    assert pedido["subtotal_itens"] == "255.00"
    assert pedido["valor_total"] == "259.50"
    assert pedido["saldo_devedor"] == "259.50"

    # Alterar manualmente status financeiro via PATCH /status é bloqueado
    resp_fin_manual = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "financeiro", "novo_status": "pago_total"},
    )
    assert resp_fin_manual.status_code == 400

    # 1o pagamento em PIX confirma rascunho automaticamente
    resp_pag1 = await client.post(
        f"/pedidos/{pedido_id}/pagamentos",
        headers=cabecalho_autorizacao,
        json={"valor": "100.00", "forma_pagamento": "pix", "observacao": "Sinal"},
    )
    assert resp_pag1.status_code == 201
    p_pag1 = resp_pag1.json()
    assert p_pag1["status_geral"] == "confirmado"
    assert p_pag1["status_financeiro"] == "pagamento_parcial"
    assert p_pag1["valor_pago"] == "100.00"
    assert p_pag1["saldo_devedor"] == "159.50"

    # PUT em pedido já confirmado é bloqueado
    resp_put_block = await client.put(
        f"/pedidos/{pedido_id}",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Outro", "quantidade": 1, "preco_unitario": "10.00"}],
        },
    )
    assert resp_put_block.status_code == 400

    # Pagamento acima do saldo devedor é bloqueado
    resp_excede = await client.post(
        f"/pedidos/{pedido_id}/pagamentos",
        headers=cabecalho_autorizacao,
        json={"valor": "200.00", "forma_pagamento": "dinheiro"},
    )
    assert resp_excede.status_code == 400

    # Cancelar pedido com valor pago > 0 sinaliza requer_estorno=True e permite estorno posterior
    resp_cancelar = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "cancelado"},
    )
    assert resp_cancelar.status_code == 200
    assert resp_cancelar.json()["requer_estorno"] is True
    assert resp_cancelar.json()["status_financeiro"] == "pagamento_parcial"

    pag_id = resp_cancelar.json()["pagamentos"][0]["id"]
    resp_estorno = await client.post(
        f"/pedidos/{pedido_id}/pagamentos/{pag_id}/estornar",
        headers=cabecalho_autorizacao,
        json={"motivo": "Cancelamento comercial"},
    )
    assert resp_estorno.status_code == 200
    assert resp_estorno.json()["status_financeiro"] == "estornado"
    assert resp_estorno.json()["valor_pago"] == "0.00"
    assert resp_estorno.json()["requer_estorno"] is False

    # Estornar novamente o mesmo pagamento falha com 400
    resp_estorno_dup = await client.post(
        f"/pedidos/{pedido_id}/pagamentos/{pag_id}/estornar",
        headers=cabecalho_autorizacao,
    )
    assert resp_estorno_dup.status_code == 400


@pytest.mark.asyncio
async def test_desconto_100_porcento_deriva_pago_total_ao_confirmar(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida borda onde pedido com valor_total=0.00 deriva status_financeiro='pago_total' ao confirmar.
    """
    cliente = Cliente(nome="Cortesia", sobrenome="Zero", telefone="11911110000")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    resp = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "desconto_valor": "100.00",
            "desconto_tipo": "percentual",
            "itens": [{"tipo_item": "servico_livre", "descricao": "Ajuste cortesia", "quantidade": 1, "preco_unitario": "50.00"}],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["valor_total"] == "0.00"
    assert resp.json()["status_financeiro"] == "sem_pagamento"

    pedido_id = resp.json()["id"]
    resp_conf = await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )
    assert resp_conf.status_code == 200
    assert resp_conf.json()["status_financeiro"] == "pago_total"
