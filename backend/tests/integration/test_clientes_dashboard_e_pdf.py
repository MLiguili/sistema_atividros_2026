import re
import zlib
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoVidro


def extrair_texto_pdf(pdf_bytes: bytes) -> str:
    """
    Extrai literais de texto de streams comprimidos FlateDecode de PDFs gerados pelo FPDF2.
    """
    textos: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, flags=re.DOTALL):
        bloco = match.group(1)
        try:
            dec = zlib.decompress(bloco).decode("latin-1", errors="ignore")
        except zlib.error:
            dec = bloco.decode("latin-1", errors="ignore")
        textos.extend(re.findall(r"\((.*?)\)", dec))
    return " ".join(textos)


@pytest.mark.asyncio
async def test_delete_materiais_vinculados_retorna_409_e_dashboard_e_pdf_contextual(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida 409 ON DELETE RESTRICT, KPIs do /dashboard/resumo e conteúdo contextual/sigiloso do PDF Único.
    """
    cliente = Cliente(nome="Helena", sobrenome="Dashboard", telefone="11944445555")
    moldura = Moldura(
        codigo="M_RESTR",
        quantidade=-1,
        estoque_minimo=5,
        preco_venda=Decimal("80.00"),
        preco_custo=Decimal("30.00"),
        cor="Preta",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    vidro = Vidro(
        tipo="incolor",
        espessura=Decimal("3.00"),
        area_disponivel_m2=Decimal("1.0000"),
        estoque_minimo_m2=Decimal("2.0000"),
    )
    fundo = Fundo(
        tipo="MDF_RESTR",
        espessura=Decimal("3.00"),
        area_disponivel_m2=Decimal("0.5000"),
        estoque_minimo_m2=Decimal("2.0000"),
    )
    tab_v = TabelaPrecoVidro(tipo="incolor_restr", preco_por_m2=Decimal("120.00"), area_minima_m2=Decimal("0.2500"))
    tab_f = TabelaPrecoFundo(tipo="MDF_RESTR", preco_por_m2=Decimal("40.00"))
    db_session.add_all([cliente, moldura, vidro, fundo, tab_v, tab_f])
    await db_session.commit()
    for obj in (cliente, moldura, vidro, fundo):
        await db_session.refresh(obj)

    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    # Pedido rascunho (não deve compor receita confirmada) com preço editado abaixo do sugerido
    resp_rasc = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "prazo_entrega": ontem.isoformat(),
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 1,
                    "obra_largura": "50.00",
                    "obra_altura": "50.00",
                    "vidro_tipo": "incolor_restr",
                    "vidro_id": vidro.id,
                    "fundo_id": fundo.id,
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                    "preco_unitario": "111.11",
                }
            ],
        },
    )
    assert resp_rasc.status_code == 201
    ped_rasc = resp_rasc.json()
    valor_sugerido_secreto = ped_rasc["itens"][0]["valor_sugerido"]
    assert valor_sugerido_secreto != "111.11"

    # ON DELETE RESTRICT -> 409
    assert (await client.delete(f"/estoque/molduras/{moldura.id}", headers=cabecalho_autorizacao)).status_code == 409
    assert (await client.delete(f"/estoque/vidros/{vidro.id}", headers=cabecalho_autorizacao)).status_code == 409
    assert (await client.delete(f"/estoque/fundos/{fundo.id}", headers=cabecalho_autorizacao)).status_code == 409

    # PDF em rascunho -> ORÇAMENTO e sigilo absoluto do valor_sugerido
    pdf_rasc = await client.get(f"/pedidos/{ped_rasc['id']}/pdf", headers=cabecalho_autorizacao)
    assert pdf_rasc.status_code == 200
    texto_rasc = extrair_texto_pdf(pdf_rasc.content)
    assert "ORÇAMENTO" in texto_rasc
    assert "Validade:" in texto_rasc
    assert "QUADRO FINAL" in texto_rasc
    assert valor_sugerido_secreto.replace(".", ",") not in texto_rasc
    assert valor_sugerido_secreto not in texto_rasc

    # Confirma pedido e baixa PDF como ORDEM DE SERVIÇO
    await client.patch(
        f"/pedidos/{ped_rasc['id']}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "confirmado"},
    )
    pdf_os = await client.get(f"/pedidos/{ped_rasc['id']}/pdf", headers=cabecalho_autorizacao)
    texto_os = extrair_texto_pdf(pdf_os.content)
    assert "ORDEM DE SERVIÇO" in texto_os
    assert "Prazo de Entrega:" in texto_os
    assert "SALDO DEVEDOR:" in texto_os

    # Verifica dashboard
    resp_dash = await client.get("/dashboard/resumo", headers=cabecalho_autorizacao)
    assert resp_dash.status_code == 200
    dash = resp_dash.json()
    assert Decimal(dash["receita_confirmada"]) >= Decimal("111.11")
    assert dash["pedidos_prazo_vencido"] >= 1
    assert any(m["codigo"] == "M_RESTR" for m in dash["alertas_estoque"]["molduras_criticas"])
    assert any(v["id"] == vidro.id for v in dash["alertas_estoque"]["vidros_criticos"])
    assert any(f["id"] == fundo.id for f in dash["alertas_estoque"]["fundos_criticos"])

    # Cancela pedido e valida PDF CANCELADO sem Prazo de Entrega e sem SALDO DEVEDOR ativo
    await client.patch(
        f"/pedidos/{ped_rasc['id']}/status",
        headers=cabecalho_autorizacao,
        json={"eixo": "geral", "novo_status": "cancelado"},
    )
    pdf_canc = await client.get(f"/pedidos/{ped_rasc['id']}/pdf", headers=cabecalho_autorizacao)
    texto_canc = extrair_texto_pdf(pdf_canc.content)
    assert "PEDIDO CANCELADO" in texto_canc
    assert "Prazo de Entrega:" not in texto_canc
    assert "SALDO DEVEDOR:" not in texto_canc
    assert "SEM COBRANÇA ATIVA" in texto_canc
