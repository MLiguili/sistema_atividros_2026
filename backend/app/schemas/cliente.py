from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


def normalizar_string_vazia(valor: object) -> object:
    """
    Converte strings vazias ou compostas apenas de espaços em None.
    """
    if isinstance(valor, str):
        limpo = valor.strip()
        return limpo if limpo else None
    return valor


class BaseCliente(BaseModel):
    """
    Campos comuns para cadastro e resposta de clientes.
    """

    nome: str
    sobrenome: str
    telefone: str
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None

    @field_validator("email", "endereco", "cep", mode="before")
    @classmethod
    def empty_str_to_none(cls, valor: object) -> object:
        """
        Normaliza campos opcionais vazios para None.
        """
        return normalizar_string_vazia(valor)


class CriarCliente(BaseCliente):
    """
    Payload de criação de cliente.
    """


class AtualizarCliente(BaseModel):
    """
    Payload de atualização parcial de cliente com normalização de strings vazias.
    """

    nome: str | None = None
    sobrenome: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None

    @field_validator("email", "endereco", "cep", mode="before")
    @classmethod
    def empty_str_to_none(cls, valor: object) -> object:
        """
        Normaliza campos opcionais vazios para None durante atualização.
        """
        return normalizar_string_vazia(valor)


class RespostaCliente(BaseCliente):
    """
    Representação de cliente retornada pela API.
    """

    id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)
