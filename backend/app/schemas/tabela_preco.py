from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CriarTabelaPrecoVidro(BaseModel):
    """
    Payload de criação de faixa de preço de vidro ou espelho por m².
    """

    tipo: str = Field(..., min_length=1, max_length=50)
    preco_por_m2: Decimal = Field(..., ge=0)
    area_minima_m2: Decimal = Field(default=Decimal("0.2500"), ge=0)
    descricao: str | None = Field(default="", max_length=255)


class AtualizarTabelaPrecoVidro(BaseModel):
    """
    Payload de atualização da tabela de preços de vidro.
    """

    preco_por_m2: Decimal = Field(..., ge=0)
    area_minima_m2: Decimal | None = Field(default=None, ge=0)
    descricao: str | None = Field(default=None, max_length=255)


class RespostaTabelaPrecoVidro(BaseModel):
    """
    Representação de preço de vidro retornada pela API.
    """

    id: int
    tipo: str
    preco_por_m2: Decimal
    area_minima_m2: Decimal
    descricao: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CriarTabelaPrecoFundo(BaseModel):
    """
    Payload de criação de faixa de preço de fundo por m².
    """

    tipo: str = Field(..., min_length=1, max_length=50)
    preco_por_m2: Decimal = Field(..., ge=0)
    descricao: str | None = Field(default="", max_length=255)


class AtualizarTabelaPrecoFundo(BaseModel):
    """
    Payload de atualização da tabela de preços de fundo.
    """

    tipo: str | None = Field(default=None, min_length=1, max_length=50)
    preco_por_m2: Decimal = Field(..., ge=0)
    descricao: str | None = Field(default=None, max_length=255)


class RespostaTabelaPrecoFundo(BaseModel):
    """
    Representação de preço de fundo retornada pela API.
    """

    id: int
    tipo: str
    preco_por_m2: Decimal
    descricao: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CriarTabelaPrecoPaspatour(BaseModel):
    """
    Payload de criação de opção de preço de paspatour por m².
    """

    descricao: str = Field(..., min_length=1, max_length=255)
    preco_por_m2: Decimal = Field(..., ge=0)


class AtualizarTabelaPrecoPaspatour(BaseModel):
    """
    Payload de atualização de opção de paspatour.
    """

    descricao: str | None = Field(default=None, min_length=1, max_length=255)
    preco_por_m2: Decimal = Field(..., ge=0)


class RespostaTabelaPrecoPaspatour(BaseModel):
    """
    Representação de preço de paspatour retornada pela API.
    """

    id: int
    descricao: str
    preco_por_m2: Decimal
    model_config = ConfigDict(from_attributes=True)
