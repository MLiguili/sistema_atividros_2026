import logging
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import obter_db
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

contexto_senha = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="autenticacao/entrar")


def verificar_senha(senha_plana, senha_hash):
    return contexto_senha.verify(senha_plana, senha_hash)

def obter_hash_senha(senha):
    return contexto_senha.hash(senha)

def criar_token_acesso(dados: dict, expira_delta: timedelta | None = None):
    para_codificar = dados.copy()
    if expira_delta:
        expira = datetime.now(UTC) + expira_delta
    else:
        expira = datetime.now(UTC) + timedelta(minutes=settings.minutos_expiracao_token)
    para_codificar.update({"exp": expira})
    jwt_codificado = jwt.encode(para_codificar, settings.chave_secreta, algorithm=settings.algoritmo_jwt)
    return jwt_codificado

async def obter_usuario_atual(token: str = Depends(esquema_oauth2), db: AsyncSession = Depends(obter_db)):
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.chave_secreta, algorithms=[settings.algoritmo_jwt])
        nome_usuario: str = payload.get("sub")
        if nome_usuario is None:
            raise excecao_credenciais
    except JWTError:
        raise excecao_credenciais

    resultado = await db.execute(select(Usuario).where(Usuario.nome_usuario == nome_usuario))
    usuario = resultado.scalar_one_or_none()

    if usuario is None:
        raise excecao_credenciais
    return usuario
