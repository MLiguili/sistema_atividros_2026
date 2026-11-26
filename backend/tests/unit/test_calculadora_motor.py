from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoPaspatour, TabelaPrecoVidro
from app.services.calculadora import (
    arredondar_2,
    calcular_area_m2,
    calcular_barras_sugeridas,
    calcular_dimensoes,
    calcular_perda_45_m,
    calcular_perimetro_m,
)


def test_propagacao_dimensoes_0_1_e_3_molduras():
    """
    Valida propagação dimensional de dentro para fora com 0, 1 e 3 molduras com/sem paspatour.
    """
    sem_moldura = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("0"), [])
    assert sem_moldura["vidro"] == {"altura": Decimal("40.00"), "largura": Decimal("50.00")}
    assert sem_moldura["quadro_final"] == {"altura": Decimal("40.00"), "largura": Decimal("50.00")}

    uma_moldura = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("5"), [("M1", Decimal("3"))])
    assert uma_moldura["vidro"] == {"altura": Decimal("50.00"), "largura": Decimal("60.00")}
    assert uma_moldura["molduras"][0] == {"codigo": "M1", "altura": Decimal("56.00"), "largura": Decimal("66.00")}

    tres_molduras = calcular_dimensoes(
        Decimal("40"),
        Decimal("50"),
        Decimal("5"),
        [("M1", Decimal("2")), ("M2", Decimal("3")), ("M3", Decimal("4"))],
    )
    assert tres_molduras["molduras"][0]["altura"] == Decimal("54.00")
    assert tres_molduras["molduras"][1]["altura"] == Decimal("60.00")
    assert tres_molduras["molduras"][2]["altura"] == Decimal("68.00")
    assert tres_molduras["quadro_final"] == {"altura": Decimal("68.00"), "largura": Decimal("78.00")}


def test_perda_45_e_barras_sugeridas():
    """
    Valida fórmula de perda técnica 45° (8 × largura_barra_cm / 100) e arredondamento de barras.
    """
    perimetro = calcular_perimetro_m(Decimal("66"), Decimal("56"))  # 2.4400 m
    perda = calcular_perda_45_m(Decimal("3"))  # 0.2400 m
    assert perimetro == Decimal("2.4400")
    assert perda == Decimal("0.2400")

    metragem_total = perimetro + perda  # 2.6800 m
    assert calcular_barras_sugeridas(metragem_total, 1, Decimal("2.70")) == 1
    assert calcular_barras_sugeridas(metragem_total, 2, Decimal("2.70")) == 2
    assert calcular_barras_sugeridas(Decimal("1.4000"), 1, Decimal("2.70")) == 1


def test_arredondamento_decimal_half_up():
    """
    Garante arredondamento determinístico ROUND_HALF_UP em centavos e áreas.
    """
    assert arredondar_2(Decimal("10.005")) == Decimal("10.01")
    assert arredondar_2(Decimal("10.004")) == Decimal("10.00")
    assert calcular_area_m2(Decimal("33.33"), Decimal("33.33")) == Decimal("0.1111")


@pytest.mark.asyncio
async def test_motor_quadro_completo_area_minima_fundo_e_mao_de_obra(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida cálculo integrado com paspatour, perda 45°, área mínima vidro, fundo pela medida do vidro e mão de obra R$/un.
    """
    moldura = Moldura(
        codigo="M_MOTOR",
        quantidade=10,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("25.00"),
        cor="Preta",
        tamanho_barra=Decimal("2.70"),
        largura_barra=Decimal("3.00"),
    )
    vidro = Vidro(
        tipo="incolor",
        espessura=Decimal("3.00"),
        area_disponivel_m2=Decimal("10.0000"),
        estoque_minimo_m2=Decimal("2.0000"),
    )
    fundo = Fundo(
        tipo="MDF_MOTOR",
        espessura=Decimal("3.00"),
        area_disponivel_m2=Decimal("10.0000"),
        estoque_minimo_m2=Decimal("2.0000"),
    )
    tab_vidro = TabelaPrecoVidro(
        tipo="incolor_motor",
        preco_por_m2=Decimal("100.00"),
        area_minima_m2=Decimal("0.2500"),
        descricao="Incolor motor",
    )
    tab_fundo = TabelaPrecoFundo(tipo="MDF_MOTOR", preco_por_m2=Decimal("40.00"), descricao="MDF 3mm")
    tab_pasp = TabelaPrecoPaspatour(descricao="Pasp Motor Branco", preco_por_m2=Decimal("80.00"))
    db_session.add_all([moldura, vidro, fundo, tab_vidro, tab_fundo, tab_pasp])
    await db_session.commit()
    for obj in (moldura, vidro, fundo, tab_pasp):
        await db_session.refresh(obj)

    # Obra 20x20cm + Paspatour 5cm => Vidro/Fundo = 30x30cm = 0.0900 m²
    # Vidro cobra área mínima 0.2500 * 100 = 25.00
    # Paspatour cobra área real 0.0900 * 80 = 7.20
    # Fundo cobra área vidro 0.0900 * 40 = 3.60
    # Moldura (barra 3cm): camada 36x36cm => perim 1.44 + perda 45 (0.24) = 1.68m * 50 = 84.00
    # Mão de obra: 20.00/un
    # Unitário esperado = 25.00 + 7.20 + 3.60 + 84.00 + 20.00 = 139.80 | Qtd 2 => 279.60
    resp = await client.post(
        "/calculadora/quadro",
        headers=cabecalho_autorizacao,
        json={
            "obra_largura": "20.00",
            "obra_altura": "20.00",
            "quantidade": 2,
            "paspatour": True,
            "tamanho_paspatour": "5.00",
            "paspatour_id": tab_pasp.id,
            "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
            "vidro_tipo": "incolor_motor",
            "vidro_id": vidro.id,
            "fundo_id": fundo.id,
            "mao_de_obra": "20.00",
        },
    )
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["areas"]["area_real_m2"] == "0.0900"
    assert dados["areas"]["area_cobrada_vidro_m2"] == "0.2500"
    assert dados["areas"]["area_fundo_m2"] == "0.0900"
    assert dados["dimensoes"]["molduras"][0]["metragem_total_m"] == "1.6800"
    assert dados["dimensoes"]["molduras"][0]["barras_sugeridas"] == 2
    assert dados["valor_sugerido_unitario"] == "139.80"
    assert dados["total_sugerido"] == "279.60"
