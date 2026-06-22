import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_usuario_inexistente(client: AsyncClient):
    resposta = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_inexistente", "password": "qualquer"}
    )
    assert resposta.status_code == 401

@pytest.mark.asyncio
async def test_login_sem_password(client: AsyncClient):
    resposta = await client.post(
        "/autenticacao/entrar",
        data={"username": "admin"}
    )
    assert resposta.status_code in [422, 400]
