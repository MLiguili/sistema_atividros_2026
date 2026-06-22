import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.estoque import Moldura
from app.models.cliente import Cliente

@pytest.mark.asyncio
async def test_gerar_pdf_pedido_sucesso(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    # 1. Preparar dados: Cliente e Moldura
    cliente = Cliente(nome="Carlos", sobrenome="PDF", telefone="11988887777")
    db_session.add(cliente)
    await db_session.flush()

    moldura = Moldura(codigo="M_PDF", quantidade=5, preco_venda=100.0, preco_custo=40.0, 
                      cor="Prata", tamanho_barra=3.0, largura_barra=3.0)
    db_session.add(moldura)
    await db_session.commit()
    await db_session.refresh(cliente)
    await db_session.refresh(moldura)

    # 2. Criar um pedido
    resp_post = await client.post(
        "/pedidos/",
        headers=cabecalho_autorizacao,
        json={
            "cliente_id": cliente.id,
            "itens": [
                {
                    "moldura_id": moldura.id,
                    "quantidade": 2,
                    "largura": 40.0,
                    "altura": 60.0
                }
            ]
        }
    )
    assert resp_post.status_code == 201
    pedido_id = resp_post.json()["id"]

    # 3. Tentar baixar o PDF
    resposta = await client.get(f"/pedidos/{pedido_id}/pdf", headers=cabecalho_autorizacao)
    
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/pdf"
    # Verificar assinatura de arquivo PDF
    assert resposta.content.startswith(b"%PDF-")
