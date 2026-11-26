import logging

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.main import app, lifespan
from app.models.usuario import Usuario
from app.services.autenticacao import obter_hash_senha
from scripts.create_admin import criar_administrador, obter_senha_inicial


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rota",
    [
        "/estoque/molduras",
        "/estoque/vidros",
        "/estoque/vidros/1",
        "/estoque/fundos",
        "/estoque/fundos/1",
        "/estoque/suplementos",
        "/calculadora/tabela-vidro",
        "/calculadora/tabela-paspatour",
    ],
)
async def test_rotas_get_estoque_e_tabelas_exigem_autenticacao(client: AsyncClient, rota: str):
    """
    Garante que todas as rotas GET de estoque e tabelas de preço exigem autenticação (HTTP 401).
    """
    resposta = await client.get(rota)
    assert resposta.status_code == 401


@pytest.mark.asyncio
async def test_login_nao_loga_senha(client: AsyncClient, db_session: AsyncSession, caplog: pytest.LogCaptureFixture):
    """
    Verifica que a tentativa de login em nível DEBUG nunca registra a senha do usuário nos logs.
    """
    senha_secreta = "SegredoSuperForte!999"
    usuario = Usuario(
        nome_usuario="usuario_log_teste",
        senha_hash=obter_hash_senha(senha_secreta),
        nome_completo="Usuário Log Teste",
        esta_ativo=True,
    )
    db_session.add(usuario)
    await db_session.commit()

    caplog.set_level(logging.DEBUG, logger="app.api.autenticacao")

    resp_ok = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_log_teste", "password": senha_secreta},
    )
    assert resp_ok.status_code == 200

    resp_falha = await client.post(
        "/autenticacao/entrar",
        data={"username": "usuario_log_teste", "password": "SenhaErrada!888"},
    )
    assert resp_falha.status_code == 401

    assert senha_secreta not in caplog.text
    assert "SenhaErrada!888" not in caplog.text
    assert "usuario_log_teste" in caplog.text


@pytest.mark.asyncio
async def test_lifespan_rejeita_chave_insegura_em_producao(monkeypatch: pytest.MonkeyPatch):
    """
    Garante que a inicialização falha com RuntimeError quando debug=False e chave_secreta é insegura.
    """
    from app import main as modulo_main

    monkeypatch.setattr(modulo_main.settings, "debug", False)
    monkeypatch.setattr(modulo_main.settings, "chave_secreta", "sua_chave_secreta_super_segura_aqui")

    with pytest.raises(RuntimeError, match="CHAVE_SECRETA insegura"):
        async with lifespan(app):
            pass

    monkeypatch.setattr(modulo_main.settings, "chave_secreta", "curta")
    with pytest.raises(RuntimeError, match="CHAVE_SECRETA insegura"):
        async with lifespan(app):
            pass

    monkeypatch.setattr(modulo_main.settings, "chave_secreta", "chave_producao_segura_com_mais_de_32_caracteres")
    async with lifespan(app):
        pass


def test_settings_cors_origins_csv():
    """
    Valida o parsing de string CSV e JSON array no campo cors_origins de Settings.
    """
    cfg_csv = Settings(cors_origins="http://localhost:5173, https://app.atividros.com ")
    assert cfg_csv.cors_origins == ["http://localhost:5173", "https://app.atividros.com"]

    cfg_json = Settings(cors_origins='["http://localhost:3000", "https://atividros.local"]')
    assert cfg_json.cors_origins == ["http://localhost:3000", "https://atividros.local"]


def test_create_admin_importavel(monkeypatch: pytest.MonkeyPatch):
    """
    Verifica que o script create_admin é importável e resolve a senha inicial por variável de ambiente.
    """
    assert callable(criar_administrador)
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "SenhaSeguraAdmin!2026")
    assert obter_senha_inicial() == "SenhaSeguraAdmin!2026"
