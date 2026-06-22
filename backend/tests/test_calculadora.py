import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.estoque import Moldura, Vidro, Fundo

@pytest.mark.asyncio
async def test_calculadora_simulacao(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    # 1. Preparar stock para IDs válidos
    moldura = Moldura(codigo="CALC01", quantidade=10, preco_venda=100.0, preco_custo=50.0, 
                      cor="Dourada", tamanho_barra=3.0, largura_barra=3.0)
    db_session.add(moldura)
    await db_session.commit()
    await db_session.refresh(moldura)

    # 2. Simular cálculo de um quadro 100x100 cm (Perímetro 4m)
    # Total esperado: 4m * 100 reais = 400 reais
    resposta = await client.post(
        "/calculadora/",
        headers=cabecalho_autorizacao,
        json={
            "largura": 100.0,
            "altura": 100.0,
            "moldura_id": moldura.id
        }
    )
    
    assert resposta.status_code == 200
    dados = resposta.json()
    assert float(dados["total_estimado"]) == 400.0
    assert len(dados["itens"]) == 1
    assert dados["itens"][0]["tipo"] == "moldura"
    assert float(dados["itens"][0]["medida_calculada"]) == 4.0

@pytest.mark.asyncio
async def test_calculadora_area_vidro(client: AsyncClient, cabecalho_autorizacao: dict, db_session: AsyncSession):
    # Vidro 100x100 cm = 1m2
    # Preço fixo simulado no service: 100 reais/m2
    vidro = Vidro(espessura=2.0, tipo="antireflexo", quantidade=5, largura_chapa=100, altura_chapa=100)
    db_session.add(vidro)

    await db_session.commit()
    await db_session.refresh(vidro)

    resposta = await client.post(
        "/calculadora/",
        headers=cabecalho_autorizacao,
        json={
            "largura": 100.0,
            "altura": 100.0,
            "vidro_id": vidro.id
        }
    )
    
    assert resposta.status_code == 200
    dados = resposta.json()
    # 1m2 * 100.0 = 100.0
    assert float(dados["total_estimado"]) == 100.0
