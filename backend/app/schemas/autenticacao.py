
from pydantic import BaseModel, ConfigDict


class TokenAcesso(BaseModel):
    token_acesso: str
    tipo_token: str

class DadosToken(BaseModel):
    nome_usuario: str | None = None

class LoginUsuario(BaseModel):
    nome_usuario: str
    senha: str

class RespostaUsuario(BaseModel):
    id: int
    nome_usuario: str
    nome_completo: str | None
    esta_ativo: bool

    model_config = ConfigDict(from_attributes=True)

