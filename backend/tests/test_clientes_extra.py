import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pedido import Pedido


@pytest.mark.asyncio
async def test_buscar_cliente_por_id(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida busca de cliente por ID.
    """
    criar_resp = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={"nome": "Cliente ID", "sobrenome": "Teste", "telefone": "11999990000"},
    )
    cliente_id = criar_resp.json()["id"]

    resposta = await client.get(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cliente ID"


@pytest.mark.asyncio
async def test_cliente_nao_encontrado(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida 404 para cliente inexistente.
    """
    resposta = await client.get("/clientes/99999", headers=cabecalho_autorizacao)
    assert resposta.status_code == 404


@pytest.mark.asyncio
async def test_criar_cliente_sem_email(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida criação de cliente sem e-mail informado.
    """
    resposta = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={"nome": "Sem", "sobrenome": "Email", "telefone": "11999991111"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["email"] is None


@pytest.mark.asyncio
async def test_criar_e_atualizar_cliente_strings_vazias_para_none(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida normalização de strings vazias em email, endereco e cep na criação e atualização.
    """
    resposta = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={
            "nome": "Email",
            "sobrenome": "Vazio",
            "telefone": "11999992222",
            "email": "   ",
            "endereco": "",
            "cep": " ",
        },
    )
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["email"] is None
    assert dados["endereco"] is None
    assert dados["cep"] is None

    resp_put = await client.put(
        f"/clientes/{dados['id']}",
        headers=cabecalho_autorizacao,
        json={"email": "", "endereco": "  ", "cep": ""},
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["email"] is None
    assert resp_put.json()["endereco"] is None
    assert resp_put.json()["cep"] is None


@pytest.mark.asyncio
async def test_busca_clientes_e_historico_filtrado_e_conflito_delete(
    client: AsyncClient,
    cabecalho_autorizacao: dict,
    db_session: AsyncSession,
):
    """
    Valida busca ?q=, histórico GET /clientes/{id}/pedidos e 409 ao deletar cliente com pedido.
    """
    c1 = (
        await client.post(
            "/clientes/",
            headers=cabecalho_autorizacao,
            json={"nome": "Fernanda", "sobrenome": "Almeida", "telefone": "11977776666"},
        )
    ).json()
    await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={"nome": "Carlos", "sobrenome": "Silva", "telefone": "11955554444"},
    )

    resp_q = await client.get("/clientes/?q=almeida", headers=cabecalho_autorizacao)
    assert resp_q.status_code == 200
    assert len(resp_q.json()) == 1
    assert resp_q.json()[0]["id"] == c1["id"]

    pedido_db = Pedido(cliente_id=c1["id"], numero_pedido="202699001")
    db_session.add(pedido_db)
    await db_session.commit()

    resp_hist = await client.get(f"/clientes/{c1['id']}/pedidos", headers=cabecalho_autorizacao)
    assert resp_hist.status_code == 200
    assert len(resp_hist.json()) == 1
    assert resp_hist.json()[0]["numero_pedido"] == "202699001"

    resp_hist_404 = await client.get("/clientes/99999/pedidos", headers=cabecalho_autorizacao)
    assert resp_hist_404.status_code == 404

    resp_del_409 = await client.delete(f"/clientes/{c1['id']}", headers=cabecalho_autorizacao)
    assert resp_del_409.status_code == 409


@pytest.mark.asyncio
async def test_deletar_cliente(client: AsyncClient, cabecalho_autorizacao: dict):
    """
    Valida exclusão de cliente sem pedidos vinculados.
    """
    criar_resp = await client.post(
        "/clientes/",
        headers=cabecalho_autorizacao,
        json={"nome": "ParaDeletar", "sobrenome": "Teste", "telefone": "11999993333"},
    )
    cliente_id = criar_resp.json()["id"]

    resposta = await client.delete(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert resposta.status_code == 204

    verificar = await client.get(f"/clientes/{cliente_id}", headers=cabecalho_autorizacao)
    assert verificar.status_code == 404
