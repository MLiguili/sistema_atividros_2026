import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_criar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida cadastro de fundo com controle em m².
    """
    resposta = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "MDF",
            "espessura": 3.0,
            "area_disponivel_m2": "12.0000",
            "estoque_minimo_m2": "3.0000",
            "cor": "Branco",
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "MDF"
    assert resposta.json()["area_disponivel_m2"] == "12.0000"


@pytest.mark.asyncio
async def test_listar_fundos(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida listagem e filtro crítico de fundos.
    """
    resposta = await client.get("/estoque/fundos", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


@pytest.mark.asyncio
async def test_atualizar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida atualização de saldo em m² de um fundo existente.
    """
    criar_resp = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={"tipo": "MDF", "espessura": 3.0, "area_disponivel_m2": "10.0000"},
    )
    fundo_id = criar_resp.json()["id"]

    resp_put = await client.put(
        f"/estoque/fundos/{fundo_id}",
        headers=cabecalho_autorizacao,
        json={"area_disponivel_m2": "15.2500"},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["area_disponivel_m2"] == "15.2500"


@pytest.mark.asyncio
async def test_deletar_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida remoção de fundo sem vínculo com pedido.
    """
    criar_resp = await client.post(
        "/estoque/fundos",
        headers=cabecalho_autorizacao,
        json={"tipo": "Acrilico", "espessura": 2.0, "area_disponivel_m2": "2.5000"},
    )
    fundo_id = criar_resp.json()["id"]

    resp_del = await client.delete(f"/estoque/fundos/{fundo_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_fundo_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida 404 para fundo inexistente.
    """
    resposta = await client.get("/estoque/fundos/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404


@pytest.mark.asyncio
async def test_criar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida CRUD manual de suplementos.
    """
    resposta = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={"nome": "Parafuso", "quantidade": 100, "unidade": "unidade"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Parafuso"


@pytest.mark.asyncio
async def test_listar_suplementos(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida listagem autenticada de suplementos.
    """
    resposta = await client.get("/estoque/suplementos", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


@pytest.mark.asyncio
async def test_atualizar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida atualização de quantidade de suplemento.
    """
    criar_resp = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={"nome": "Cola", "quantidade": 50, "unidade": "ml"},
    )
    sup_id = criar_resp.json()["id"]

    resp_put = await client.put(
        f"/estoque/suplementos/{sup_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 100},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 100


@pytest.mark.asyncio
async def test_deletar_suplemento(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida exclusão de suplemento.
    """
    criar_resp = await client.post(
        "/estoque/suplementos",
        headers=cabecalho_autorizacao,
        json={"nome": "Prego", "quantidade": 200, "unidade": "unidade"},
    )
    sup_id = criar_resp.json()["id"]

    resp_del = await client.delete(f"/estoque/suplementos/{sup_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_atualizar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida atualização de vidro em m².
    """
    criar_resp = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={"espessura": 4.0, "tipo": "espelho", "area_disponivel_m2": "8.0000", "cor": "Dourado"},
    )
    vidro_id = criar_resp.json()["id"]

    resp_put = await client.put(
        f"/estoque/vidros/{vidro_id}",
        headers=cabecalho_autorizacao,
        json={"area_disponivel_m2": "12.5000"},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["area_disponivel_m2"] == "12.5000"


@pytest.mark.asyncio
async def test_deletar_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida exclusão de vidro sem vínculo em pedido.
    """
    criar_resp = await client.post(
        "/estoque/vidros",
        headers=cabecalho_autorizacao,
        json={"espessura": 2.0, "tipo": "incolor", "area_disponivel_m2": "5.0000"},
    )
    vidro_id = criar_resp.json()["id"]

    resp_del = await client.delete(f"/estoque/vidros/{vidro_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_vidro_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida 404 para vidro inexistente.
    """
    resposta = await client.get("/estoque/vidros/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida atualização de quantidade de barras de moldura.
    """
    criar_resp = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_UPDATE",
            "quantidade": 10,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Azul",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0,
        },
    )
    moldura_id = criar_resp.json()["id"]

    resp_put = await client.put(
        f"/estoque/molduras/{moldura_id}",
        headers=cabecalho_autorizacao,
        json={"quantidade": 15},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["quantidade"] == 15


@pytest.mark.asyncio
async def test_deletar_moldura(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida exclusão de moldura sem vínculo em pedido.
    """
    criar_resp = await client.post(
        "/estoque/molduras",
        headers=cabecalho_autorizacao,
        json={
            "codigo": "M_DELETE",
            "quantidade": 5,
            "preco_venda": 50.0,
            "preco_custo": 20.0,
            "cor": "Verde",
            "tamanho_barra": 3.0,
            "largura_barra": 2.0,
        },
    )
    moldura_id = criar_resp.json()["id"]

    resp_del = await client.delete(f"/estoque/molduras/{moldura_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204
