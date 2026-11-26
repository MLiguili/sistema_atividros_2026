from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.estoque import calcular_area_chapas_m2


def test_calcular_area_chapas_m2_precisao():
    """
    Valida conversão (quantidade × largura_cm × altura_cm) / 10000 com 4 casas decimais.
    """
    assert calcular_area_chapas_m2(3, Decimal("240.00"), Decimal("180.00")) == Decimal("12.9600")
    assert calcular_area_chapas_m2(1, Decimal("33.33"), Decimal("33.33")) == Decimal("0.1111")


@pytest.mark.asyncio
async def test_entrada_chapas_e_ajuste_m2_vidro_e_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida entrada por chapas somando m² e ajuste manual (inclusive saldo negativo) em vidros e fundos.
    """
    resp_v = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={"tipo": "incolor", "espessura": "4.00", "area_disponivel_m2": "5.5000"},
    )
    assert resp_v.status_code == 201
    vidro_id = resp_v.json()["id"]

    resp_in = await client.post(
        f"/estoque/vidros/{vidro_id}/entrada-chapas",
        headers=cabecalho_autorizacao,
        json={"quantidade_chapas": 3, "largura_cm": "240.00", "altura_cm": "180.00"},
    )
    assert resp_in.status_code == 200
    assert resp_in.json()["area_adicionada_m2"] == "12.9600"
    assert resp_in.json()["area_disponivel_m2"] == "18.4600"

    resp_aj = await client.post(
        f"/estoque/vidros/{vidro_id}/ajuste-m2",
        headers=cabecalho_autorizacao,
        json={"nova_area_m2": "-0.5000", "motivo": "Quebra"},
    )
    assert resp_aj.status_code == 200
    assert resp_aj.json()["area_disponivel_m2"] == "-0.5000"

    resp_f = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={"tipo": "Eucatex", "espessura": "3.00", "area_disponivel_m2": "1.0000"},
    )
    assert resp_f.status_code == 201
    fundo_id = resp_f.json()["id"]

    resp_f_in = await client.post(
        f"/estoque/fundos/{fundo_id}/entrada-chapas",
        headers=cabecalho_autorizacao,
        json={"quantidade_chapas": 2, "largura_cm": "100.00", "altura_cm": "200.00"},
    )
    assert resp_f_in.status_code == 200
    assert resp_f_in.json()["area_adicionada_m2"] == "4.0000"
    assert resp_f_in.json()["area_disponivel_m2"] == "5.0000"
