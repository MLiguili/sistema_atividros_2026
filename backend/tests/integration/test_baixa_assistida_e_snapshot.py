from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoVidro


@pytest.mark.asyncio
async def test_baixa_assistida_ajuste_manual_ruptura_e_imutabilidade_snapshot(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida previsão, exigência de confirmado, ajuste manual, ruptura não-bloqueante e snapshot imutável.
    """
    cliente = Cliente(nome="Oficina", sobrenome="Tester", telefone="11922223333")
    moldura = Moldura(
        codigo="M_BAIXA",
        quantidade=1,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("20.00"),
        cor="Imbuia",
        tamanho_barra=Decimal("2.70"),
        largura_barra=Decimal("3.00"),
    )
    vidro = Vidro(tipo="incolor", espessura=Decimal("3.00"), area_disponivel_m2=Decimal("0.2000"))
    fundo = Fundo(tipo="EUC_BAIXA", espessura=Decimal("3.00"), area_disponivel_m2=Decimal("1.0000"))
    tab_v = TabelaPrecoVidro(tipo="incolor_baixa", preco_por_m2=Decimal("100.00"), area_minima_m2=Decimal("0.2500"))
    tab_f = TabelaPrecoFundo(tipo="EUC_BAIXA", preco_por_m2=Decimal("25.00"))
    db_session.add_all([cliente, moldura, vidro, fundo, tab_v, tab_f])
    await db_session.commit()
    for obj in (cliente, moldura, vidro, fundo):
        await db_session.refresh(obj)

    resp_ped = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 2,
                    "obra_largura": "40.00",
                    "obra_altura": "50.00",
                    "vidro_tipo": "incolor_baixa",
                    "vidro_id": vidro.id,
                    "fundo_id": fundo.id,
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                }
            ],
        },
    )
    assert resp_ped.status_code == 201
    pedido = resp_ped.json()
    pedido_id = pedido["id"]
    preco_original = pedido["itens"][0]["preco_unitario"]

    # Rascunho não pode prever nem baixar estoque
    resp_prev_rascunho = await client.get(f"/pedidos/{pedido_id}/previsao-baixa", headers=cabecalho_autorizacao)
    assert resp_prev_rascunho.status_code == 400

    # Confirma e move na produção para na_fila (para testar status_anterior real no PedidoEvento)
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

    resp_prev = await client.get(f"/pedidos/{pedido_id}/previsao-baixa", headers=cabecalho_autorizacao)
    assert resp_prev.status_code == 200
    prev = resp_prev.json()
    assert prev["possui_insumos_estoque"] is True
    assert prev["molduras"][0]["barras_sugeridas"] == 2
    assert prev["molduras"][0]["em_ruptura"] is True
    assert prev["vidros"][0]["area_a_baixar_m2"] == "0.4000"  # 2 * 0.2000m² reais (não usa 0.25 área mínima)
    assert prev["vidros"][0]["em_ruptura"] is True  # 0.2000 - 0.4000 = -0.2000

    # Altera preço da moldura no cadastro para testar imutabilidade do snapshot do pedido existente
    await client.put(
        f"/estoque/molduras/{moldura.id}",
        headers=cabecalho_autorizacao,
        json={"preco_venda": "120.00"},
    )

    # Baixa assistida ajustando moldura para 3 barras e permitindo saldo negativo sem bloquear
    resp_baixa = await client.post(
        f"/pedidos/{pedido_id}/baixa-estoque",
        headers=cabecalho_autorizacao,
        json={
            "ajustes_molduras": [{"moldura_id": moldura.id, "barras_baixadas": 3}],
            "observacao": "Corte realizado na bancada 2",
        },
    )
    assert resp_baixa.status_code == 200
    baixa = resp_baixa.json()
    assert baixa["pedido"]["status_producao"] == "em_producao"
    assert len(baixa["alertas_ruptura"]) == 2
    assert baixa["pedido"]["itens"][0]["preco_unitario"] == preco_original
    assert baixa["pedido"]["itens"][0]["molduras"][0]["preco_m_aplicado"] == "50.00"

    # Confirma gravação do status_anterior real ("na_fila") no evento de produção
    eventos_prod = [e for e in baixa["pedido"]["eventos"] if e["eixo"] == "producao" and e["status_novo"] == "em_producao"]
    assert eventos_prod[-1]["status_anterior"] == "na_fila"


@pytest.mark.asyncio
async def test_baixa_assistida_servico_livre_sem_insumos_fisicos(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida fluxo completo quando o pedido não possui insumos físicos vinculados (possui_insumos_estoque=False).
    """
    cliente = Cliente(nome="Servico", sobrenome="Livre", telefone="11933334444")
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)

    resp_ped = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [{"tipo_item": "servico_livre", "descricao": "Instalação", "quantidade": 1, "preco_unitario": "90.00"}],
        },
    )
    pedido_id = resp_ped.json()["id"]
    await client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )

    resp_prev = await client.get(f"/pedidos/{pedido_id}/previsao-baixa", headers=cabecalho_autorizacao)
    assert resp_prev.status_code == 200
    assert resp_prev.json()["possui_insumos_estoque"] is False

    resp_baixa = await client.post(f"/pedidos/{pedido_id}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    assert resp_baixa.json()["pedido"]["status_producao"] == "em_producao"
    assert resp_baixa.json()["materiais_baixados"] == []
    assert resp_baixa.json()["alertas_ruptura"] == []


@pytest.mark.asyncio
async def test_vinculo_automatico_por_tipo_e_aviso_compra_sem_estoque(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida que informar apenas o tipo vincula automaticamente a chapa em estoque (quando existe)
    e alerta necessidade de compra na Baixa Assistida quando o material não está cadastrado.
    """
    cliente = Cliente(nome="Compra", sobrenome="Auto", telefone="11944445555")
    vidro = Vidro(tipo="espelho", espessura=Decimal("4.00"), area_disponivel_m2=Decimal("2.5000"))
    tab_v = TabelaPrecoVidro(tipo="espelho", preco_por_m2=Decimal("200.00"), area_minima_m2=Decimal("0.2500"))
    tab_f = TabelaPrecoFundo(tipo="FOAM_COMPRA", preco_por_m2=Decimal("90.00"))
    db_session.add_all([cliente, vidro, tab_v, tab_f])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(vidro)

    resp_ped = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 1,
                    "obra_largura": "50.00",
                    "obra_altura": "40.00",
                    "vidro_tipo": "espelho",
                    "fundo_tipo": "FOAM_COMPRA",
                }
            ],
        },
    )
    assert resp_ped.status_code == 201
    ped = resp_ped.json()
    assert ped["itens"][0]["vidro_id"] == vidro.id
    assert ped["itens"][0]["fundo_id"] is None

    await client.patch(
        f"/pedidos/{ped['id']}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )

    resp_prev = await client.get(f"/pedidos/{ped['id']}/previsao-baixa", headers=cabecalho_autorizacao)
    assert resp_prev.status_code == 200
    prev = resp_prev.json()
    assert len(prev["vidros"]) == 1
    assert any("FOAM_COMPRA" in msg and "comprado" in msg for msg in prev["materiais_para_compra"])

    resp_baixa = await client.post(f"/pedidos/{ped['id']}/baixa-estoque", headers=cabecalho_autorizacao)
    assert resp_baixa.status_code == 200
    assert any("FOAM_COMPRA" in msg for msg in resp_baixa.json()["alertas_ruptura"])
