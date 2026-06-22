import pytest
from httpx import AsyncClient
from app.services.autenticacao import obter_hash_senha
from app.models.usuario import Usuario
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_login_sucesso(client: AsyncClient, db_session: AsyncSession):
    # Criar usuário de teste manualmente
    senha_plana = "teste123"
    usuario = Usuario(
        nome_usuario="usuario_teste",
        senha_hash=obter_hash_senha(senha_plana),
        nome_completo="Usuário Teste",
        esta_ativo=True
    )
    db_session.add(usuario)
    await db_session.commit()

    # Tentar login
    resposta = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_teste", "password": senha_plana}
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert "token_acesso" in dados
    assert dados["tipo_token"] == "bearer"

@pytest.mark.asyncio
async def test_login_senha_incorreta(client: AsyncClient, db_session: AsyncSession):
    resposta = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_teste", "password": "senha_errada"}
    )
    assert resposta.status_code == 401

@pytest.mark.asyncio
async def test_obter_me(client: AsyncClient, db_session: AsyncSession):
    # Primeiro faz login para pegar o token
    senha_plana = "teste123"
    login_resp = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_teste", "password": senha_plana}
    )
    token = login_resp.json()["token_acesso"]

    # Chama /autenticacao/me com o token
    resposta = await client.get(
        "/autenticacao/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["nome_usuario"] == "usuario_teste"
