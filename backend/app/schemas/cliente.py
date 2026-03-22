from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class BaseCliente(BaseModel):
    nome: str
    sobrenome: str
    telefone: str
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        return v if v else None

class CriarCliente(BaseCliente):
    pass

class AtualizarCliente(BaseModel):
    nome: str | None = None
    sobrenome: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None

class RespostaCliente(BaseCliente):
    id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)
