from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoVidro


@pytest.mark.asyncio
async def test_endpoints_legados_calculadora_removidos(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Garante que os endpoints legados /calculadora/ e /calculadora/simular foram removidos (404).
    """
    resp_raiz = await client.post(
        "/calculadora/",
        headers=cabecalho_autorizacao,
        json={"largura": 50, "altura": 40},
    )
    resp_simular = await client.post(
        "/calculadora/simular",
        headers=cabecalho_autorizacao,
        json={"largura": 50, "altura": 40},
    )
    assert resp_raiz.status_code == 404
    assert resp_simular.status_code == 404


@pytest.mark.asyncio
async def test_calculo_vidro_avulso_com_area_minima(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida o endpoint /calculadora/vidro-avulso aplicando regra de área mínima comercial.
    """
    vidro = Vidro(tipo="espelho", espessura=Decimal("4.00"), area_disponivel_m2=Decimal("5.0000"))
    tab_espelho = TabelaPrecoVidro(
        tipo="espelho_avulso",
        preco_por_m2=Decimal("160.00"),
        area_minima_m2=Decimal("0.2500"),
        descricao="Espelho 4mm",
    )
    db_session.add_all([vidro, tab_espelho])
    await db_session.commit()
    await db_session.refresh(vidro)

    # 30x40cm = 0.1200 m² reais, mas cobra 0.2500 m² * 160 = 40.00 + 10.00 mão de obra = 50.00
    resposta = await client.post(
        "/calculadora/vidro-avulso",
        headers=cabecalho_autorizacao,
        json={
            "largura": "30.00",
            "altura": "40.00",
            "quantidade": 2,
            "vidro_tipo": "espelho_avulso",
            "vidro_id": vidro.id,
            "mao_de_obra": "10.00",
        },
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["areas"]["area_real_m2"] == "0.1200"
    assert dados["areas"]["area_cobrada_vidro_m2"] == "0.2500"
    assert dados["valor_sugerido_unitario"] == "50.00"
    assert dados["total_sugerido"] == "100.00"


@pytest.mark.asyncio
async def test_quadro_perda_45_por_endpoint(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida o cálculo completo de moldura com perda 45° no endpoint /calculadora/quadro.
    """
    moldura = Moldura(
        codigo="CALC01",
        quantidade=10,
        preco_venda=Decimal("100.00"),
        preco_custo=Decimal("50.00"),
        cor="Dourada",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    db_session.add(moldura)
    await db_session.commit()
    await db_session.refresh(moldura)

    # Obra 100x100, barra 3cm -> camada 106x106 => perim 4.24 + perda 0.24 = 4.48m * 100 = 448.00
    resposta = await client.post(
        "/calculadora/quadro",
        headers=cabecalho_autorizacao,
        json={
            "obra_largura": "100.00",
            "obra_altura": "100.00",
            "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
            "paspatour": False,
            "quantidade": 1,
        },
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["dimensoes"]["molduras"][0]["metragem_total_m"] == "4.4800"
    assert dados["total_sugerido"] == "448.00"
