from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.estoque import Moldura


@pytest.mark.asyncio
async def test_gerar_pdf_pedido_sucesso(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    """
    Valida geração de PDF binário válido para pedido com moldura sob medida.
    """
    cliente = Cliente(nome="Carlos", sobrenome="PDF", telefone="11988887777")
    moldura = Moldura(
        codigo="M_PDF",
        quantidade=5,
        preco_venda=Decimal("100.00"),
        preco_custo=Decimal("40.00"),
        cor="Prata",
        tamanho_barra=Decimal("3.00"),
        largura_barra=Decimal("3.00"),
    )
    db_session.add_all([cliente, moldura])
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    resp_post = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "molduras": [{"moldura_id": moldura.id, "ordem": 0}],
                    "quantidade": 2,
                    "obra_largura": 40.0,
                    "obra_altura": 60.0,
                }
            ],
        },
    )
    assert resp_post.status_code == 201
    pedido_id = resp_post.json()["id"]

    resposta = await client.get(f"/pedidos/{pedido_id}/pdf", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/pdf"
    assert resposta.content.startswith(b"%PDF-")
