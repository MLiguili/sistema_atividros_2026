import pytest
from decimal import Decimal
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
    assert calcular_area_m2(Decimal("100"), Decimal("50")) == Decimal("0.5000")
    assert calcular_area_m2(Decimal("30"), Decimal("40")) == Decimal("0.1200")


def test_calcular_perimetro_m():
    assert calcular_perimetro_m(Decimal("30"), Decimal("40")) == Decimal("1.40")
    assert calcular_perimetro_m(Decimal("100"), Decimal("50")) == Decimal("3.00")


def test_calcular_dimensoes_somente_moldura():
    molduras = [("M01", Decimal("3"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("0"), molduras)
    assert resultado["obra"]["altura"] == Decimal("40")
    assert resultado["obra"]["largura"] == Decimal("50")
    assert resultado["vidro"]["altura"] == Decimal("40")
    assert resultado["vidro"]["largura"] == Decimal("50")
    assert len(resultado["molduras"]) == 1
    assert resultado["molduras"][0]["altura"] == Decimal("46")
    assert resultado["molduras"][0]["largura"] == Decimal("56")
    assert resultado["quadro_final"]["altura"] == Decimal("46")
    assert resultado["quadro_final"]["largura"] == Decimal("56")


def test_calcular_dimensoes_paspatour_e_moldura():
    molduras = [("M01", Decimal("3"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("5"), molduras)
    assert resultado["vidro"]["altura"] == Decimal("50")
    assert resultado["vidro"]["largura"] == Decimal("60")
    assert resultado["molduras"][0]["altura"] == Decimal("56")
    assert resultado["molduras"][0]["largura"] == Decimal("66")
    assert resultado["quadro_final"]["altura"] == Decimal("56")
    assert resultado["quadro_final"]["largura"] == Decimal("66")


def test_calcular_dimensoes_multiplas_molduras():
    molduras = [("M01", Decimal("3")), ("M02", Decimal("4"))]
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("5"), molduras)
    assert resultado["molduras"][0]["altura"] == Decimal("56")
    assert resultado["molduras"][0]["largura"] == Decimal("66")
    assert resultado["molduras"][1]["altura"] == Decimal("64")
    assert resultado["molduras"][1]["largura"] == Decimal("74")
    assert resultado["quadro_final"]["altura"] == Decimal("64")
    assert resultado["quadro_final"]["largura"] == Decimal("74")


def test_calcular_dimensoes_sem_paspatour():
    molduras = []
    resultado = calcular_dimensoes(Decimal("40"), Decimal("50"), Decimal("0"), molduras)
    assert resultado["vidro"]["altura"] == Decimal("40")
    assert resultado["vidro"]["largura"] == Decimal("50")
    assert len(resultado["molduras"]) == 0
    assert resultado["quadro_final"]["altura"] == Decimal("40")
    assert resultado["quadro_final"]["largura"] == Decimal("50")


@pytest.mark.asyncio
async def test_endpoint_calculadora_quadro(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    moldura = Moldura(codigo="MCALC01", quantidade=10, preco_venda=50.0, preco_custo=25.0, cor="Dourada", tamanho_barra=3.0, largura_barra=3.0)
    tabela_vidro = TabelaPrecoVidro(tipo="cristal", preco_por_m2=120.0)
    tabela_paspatour = TabelaPrecoPaspatour(descricao="Paspatour premium", preco_por_m2=80.0)
    db_session.add_all([moldura, tabela_vidro, tabela_paspatour])
    await db_session.commit()
    await db_session.refresh(moldura)

    resp = await client.post("/calculadora/quadro", headers=cabecalho_autorizacao, json={
        "obra_largura": 50,
        "obra_altura": 40,
        "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
        "paspatour": True,
        "tamanho_paspatour": 5,
        "vidro_tipo": "cristal",
        "quantidade": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["dimensoes"]["vidro"]["altura"] == "50"
    assert data["dimensoes"]["vidro"]["largura"] == "60"
    assert float(data["dimensoes"]["quadro_final"]["altura"]) == 56
    assert float(data["dimensoes"]["quadro_final"]["largura"]) == 66
    assert len(data["custos"]) >= 2
    assert float(data["total_sugerido"]) > 0


@pytest.mark.asyncio
async def test_endpoint_calculadora_quadro_sem_paspatour(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    resp = await client.post("/calculadora/quadro", headers=cabecalho_autorizacao, json={
        "obra_largura": 50,
        "obra_altura": 40,
        "molduras": [],
        "paspatour": False,
        "vidro_tipo": "incolor",
        "quantidade": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["dimensoes"]["vidro"]["altura"] == "40"
    assert data["dimensoes"]["vidro"]["largura"] == "50"
