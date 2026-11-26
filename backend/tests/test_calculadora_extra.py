import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_criar_preco_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida criação de preço de vidro com área mínima configurável.
    """
    resposta = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={
            "tipo": "antireflexo",
            "preco_por_m2": 150.0,
            "area_minima_m2": "0.3000",
            "descricao": "Vidro antireflexo premium",
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "antireflexo"
    assert resposta.json()["area_minima_m2"] == "0.3000"


@pytest.mark.asyncio
async def test_listar_tabela_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida listagem autenticada da tabela de preços de vidro.
    """
    resposta = await client.get("/calculadora/tabela-vidro", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


@pytest.mark.asyncio
async def test_atualizar_e_deletar_preco_vidro(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida atualização e exclusão na tabela de preços de vidro.
    """
    criar_resp = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={"tipo": "incolor", "preco_por_m2": 80.0},
    )
    vidro_id = criar_resp.json()["id"]

    resp_put = await client.put(
        f"/calculadora/tabela-vidro/{vidro_id}",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 95.0, "area_minima_m2": "0.2500", "descricao": "Vidro incolor atualizado"},
    )
    assert resp_put.status_code == 200
    assert float(resp_put.json()["preco_por_m2"]) == 95.0

    resp_del = await client.delete(f"/calculadora/tabela-vidro/{vidro_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_preco_vidro_ja_existe(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida rejeição de tipo de vidro duplicado na tabela de preços.
    """
    await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={"tipo": "espelho", "preco_por_m2": 120.0},
    )
    resposta = await client.post(
        "/calculadora/tabela-vidro",
        headers=cabecalho_autorizacao,
        json={"tipo": "espelho", "preco_por_m2": 130.0},
    )
    assert resposta.status_code == 400


@pytest.mark.asyncio
async def test_crud_tabela_fundo(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida CRUD completo da nova tabela de preços de fundo (GET, POST, PUT, DELETE).
    """
    resp_create = await client.post(
        "/calculadora/tabela-fundo",
        headers=cabecalho_autorizacao,
        json={"tipo": "MDF", "preco_por_m2": "35.00", "descricao": "MDF 3mm"},
    )
    assert resp_create.status_code == 201
    fundo_id = resp_create.json()["id"]

    resp_dup = await client.post(
        "/calculadora/tabela-fundo",
        headers=cabecalho_autorizacao,
        json={"tipo": "mdf", "preco_por_m2": "40.00"},
    )
    assert resp_dup.status_code == 400

    resp_list = await client.get("/calculadora/tabela-fundo", headers=cabecalho_autorizacao)
    assert resp_list.status_code == 200
    assert any(item["id"] == fundo_id for item in resp_list.json())

    resp_put = await client.put(
        f"/calculadora/tabela-fundo/{fundo_id}",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": "42.50", "descricao": "MDF 3mm atualizado"},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["preco_por_m2"] == "42.50"

    resp_del = await client.delete(f"/calculadora/tabela-fundo/{fundo_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_crud_preco_paspatour(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida criação, listagem, atualização e exclusão na tabela de preços de paspatour.
    """
    resposta = await client.post(
        "/calculadora/tabela-paspatour",
        headers=cabecalho_autorizacao,
        json={"descricao": "Paspatour branco 3cm", "preco_por_m2": 25.0},
    )
    assert resposta.status_code == 201
    pasp_id = resposta.json()["id"]

    resp_list = await client.get("/calculadora/tabela-paspatour", headers=cabecalho_autorizacao)
    assert resp_list.status_code == 200

    resp_put = await client.put(
        f"/calculadora/tabela-paspatour/{pasp_id}",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 28.0},
    )
    assert resp_put.status_code == 200
    assert float(resp_put.json()["preco_por_m2"]) == 28.0

    resp_del = await client.delete(f"/calculadora/tabela-paspatour/{pasp_id}", headers=cabecalho_autorizacao)
    assert resp_del.status_code == 204


@pytest.mark.asyncio
async def test_precos_nao_encontrados(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida retorno 404 para IDs inexistentes nas três tabelas de preço.
    """
    resp_p = await client.put(
        "/calculadora/tabela-paspatour/99999",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 30.0},
    )
    resp_v = await client.put(
        "/calculadora/tabela-vidro/99999",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 30.0},
    )
    resp_f = await client.put(
        "/calculadora/tabela-fundo/99999",
        headers=cabecalho_autorizacao,
        json={"preco_por_m2": 30.0},
    )
    assert resp_p.status_code == 404
    assert resp_v.status_code == 404
    assert resp_f.status_code == 404
