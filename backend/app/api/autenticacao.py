import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.usuario import Usuario
from app.schemas.autenticacao import RespostaUsuario, TokenAcesso
from app.services.autenticacao import criar_token_acesso, obter_usuario_atual, verificar_senha

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/autenticacao", tags=["autenticacao"])

@router.post("/entrar", response_model=TokenAcesso)
async def login(
    dados_form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(obter_db)
):
    logger.debug("Tentativa de login para usuario: %s", dados_form.username, dados_form.password)
    resultado = await db.execute(select(Usuario).where(Usuario.nome_usuario == dados_form.username))
    usuario = resultado.scalar_one_or_none()

    if not usuario or not verificar_senha(dados_form.password, usuario.senha_hash):
        logger.debug("Login falhou para usuario: %s", dados_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.esta_ativo:
        logger.debug("Login rejeitado - usuario inativo: %s", dados_form.username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")

    logger.debug("Login bem-sucedido para usuario: %s", dados_form.username)
    token_acesso = criar_token_acesso(dados={"sub": usuario.nome_usuario})
    return {"token_acesso": token_acesso, "tipo_token": "bearer"}

@router.get("/me", response_model=RespostaUsuario)
async def ler_usuario_atual(usuario_atual: Usuario = Depends(obter_usuario_atual)):
    """
    Retorna os dados do usuário autenticado.
    """
    return usuario_atual
