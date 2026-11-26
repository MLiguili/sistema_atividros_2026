from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Moldura
from app.models.tabela_preco import TabelaPrecoPaspatour, TabelaPrecoVidro
from app.services.calculadora import (
    calcular_area_m2,
    calcular_dimensoes,
    calcular_perimetro_m,
)


def test_calcular_area_m2():
    """
    Valida cálculo de área em m² a partir de cm.
    """
    assert calcular_area_m2(Decimal("100"), Decimal("50")) == Decimal("0.5000")
    assert calcular_area_m2(Decimal("30"), Decimal("40")) == Decimal("0.1200")


def test_calcular_perimetro_m():
    """
    Valida cálculo de perímetro seco em metros.
    """
    assert calcular_perimetro_m(Decimal("30"), Decimal("40")) == Decimal("1.4000")
    assert calcular_perimetro_m(Decimal("100"), Decimal("50")) == Decimal("3.0000")


def test_calcular_dimensoes_somente_moldura():
    """
    Valida propagação dimensional apenas com moldura.
    """
    molduras = [("M01", Decimal("3"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("0"), molduras)
    assert resultado["obra"]["altura"] == Decimal("40.00")
    assert resultado["obra"]["largura"] == Decimal("50.00")
    assert resultado["vidro"]["altura"] == Decimal("40.00")
    assert resultado["vidro"]["largura"] == Decimal("50.00")
    assert len(resultado["molduras"]) == 1
    assert resultado["molduras"][0]["altura"] == Decimal("46.00")
    assert resultado["molduras"][0]["largura"] == Decimal("56.00")


def test_calcular_dimensoes_paspatour_e_moldura():
    """
    Valida propagação com paspatour e 1 moldura.
    """
    molduras = [("M01", Decimal("3"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("5"), molduras)
    assert resultado["vidro"]["altura"] == Decimal("50.00")
    assert resultado["vidro"]["largura"] == Decimal("60.00")
    assert resultado["molduras"][0]["altura"] == Decimal("56.00")
    assert resultado["molduras"][0]["largura"] == Decimal("66.00")


def test_calcular_dimensoes_multiplas_molduras():
    """
    Valida propagação com paspatour e múltiplas molduras ordenadas.
    """
    molduras = [("M01", Decimal("3")), ("M02", Decimal("4"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("5"), molduras)
    assert resultado["molduras"][0]["altura"] == Decimal("56.00")
    assert resultado["molduras"][0]["largura"] == Decimal("66.00")
    assert resultado["molduras"][1]["altura"] == Decimal("64.00")
    assert resultado["molduras"][1]["largura"] == Decimal("74.00")
    assert resultado["quadro_final"]["altura"] == Decimal("64.00")
    assert resultado["quadro_final"]["largura"] == Decimal("74.00")


def test_calcular_dimensoes_sem_paspatour():
    """
    Valida cálculo sem paspatour e sem moldura.
    """
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("0"), [])
    assert resultado["vidro"]["altura"] == Decimal("40.00")
    assert resultado["vidro"]["largura"] == Decimal("50.00")
    assert len(resultado["molduras"]) == 0


@pytest.mark.asyncio
async def test_endpoint_calculadora_quadro(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida endpoint /calculadora/quadro com paspatour, moldura e vidro cadastrados.
    """
    moldura = Moldura(
        codigo="MCALC01",
        quantidade=10,
        preco_venda=Decimal("50.00"),
        preco_custo=Decimal("25.00"),
        cor="Dourada",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    tabela_vidro = TabelaPrecoVidro(tipo="cristal", preco_por_m2=Decimal("120.00"), area_minima_m2=Decimal("0.2500"))
    tabela_paspatour = TabelaPrecoPaspatour(descricao="Paspatour premium", preco_por_m2=Decimal("80.00"))
    db_session.add_all([moldura, tabela_vidro, tabela_paspatour])
    await db_session.commit()
    await db_session.refresh(moldura)
    await db_session.refresh(tabela_paspatour)

    resp = await client.post(
        "/calculadora/quadro",
        headers=cabecalho_autorizacao,
        json={
            "obra_largura": 50,
            "obra_altura": 40,
            "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
            "paspatour": True,
            "tamanho_paspatour": 5,
            "paspatour_id": tabela_paspatour.id,
            "vidro_tipo": "cristal",
            "quantidade": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["dimensoes"]["vidro"]["altura"]) == 50
    assert float(data["dimensoes"]["vidro"]["largura"]) == 60
    assert float(data["dimensoes"]["quadro_final"]["altura"]) == 56
    assert float(data["dimensoes"]["quadro_final"]["largura"]) == 66
    assert len(data["custos"]) >= 2
    assert float(data["total_sugerido"]) > 0


@pytest.mark.asyncio
async def test_endpoint_calculadora_quadro_sem_paspatour(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida cálculo sem paspatour e sem vidro (somente dimensões da obra).
    """
    resp = await client.post(
        "/calculadora/quadro",
        headers=cabecalho_autorizacao,
        json={
            "obra_largura": 50,
            "obra_altura": 40,
            "molduras": [],
            "paspatour": False,
            "quantidade": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["dimensoes"]["vidro"]["altura"]) == 40
    assert float(data["dimensoes"]["vidro"]["largura"]) == 50
