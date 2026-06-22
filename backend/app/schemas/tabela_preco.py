from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CriarTabelaPrecoVidro(BaseModel):
    tipo: str
    preco_por_m2: Decimal
    descricao: str = ""


class AtualizarTabelaPrecoVidro(BaseModel):
    preco_por_m2: Decimal
    descricao: str = ""


class RespostaTabelaPrecoVidro(CriarTabelaPrecoVidro):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CriarTabelaPrecoPaspatour(BaseModel):
    descricao: str
    preco_por_m2: Decimal


class AtualizarTabelaPrecoPaspatour(BaseModel):
    preco_por_m2: Decimal


class RespostaTabelaPrecoPaspatour(CriarTabelaPrecoPaspatour):
    id: int
    model_config = ConfigDict(from_attributes=True)
