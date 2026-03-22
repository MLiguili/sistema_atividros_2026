from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.estoque import TipoVidro


# Base para schemas comuns
class BaseEstoque(BaseModel):
    quantidade: int = Field(default=0, ge=0)

# --- Molduras ---
class BaseMoldura(BaseEstoque):
    codigo: str
    preco_venda: Decimal
    preco_custo: Decimal
    cor: str
    tamanho_barra: Decimal
    largura_barra: Decimal
    marca: str | None = None

class CriarMoldura(BaseMoldura):
    pass

class AtualizarMoldura(BaseModel):
    codigo: str | None = None
    quantidade: int | None = None
    preco_venda: Decimal | None = None
    preco_custo: Decimal | None = None
    cor: str | None = None
    tamanho_barra: Decimal | None = None
    largura_barra: Decimal | None = None
    marca: str | None = None

class RespostaMoldura(BaseMoldura):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Vidros ---
class BaseVidro(BaseEstoque):
    espessura: Decimal
    tipo: TipoVidro
    largura_chapa: Decimal
    altura_chapa: Decimal
    cor: str | None = None

class CriarVidro(BaseVidro):
    pass

class AtualizarVidro(BaseModel):
    espessura: Decimal | None = None
    tipo: TipoVidro | None = None
    quantidade: int | None = None
    largura_chapa: Decimal | None = None
    altura_chapa: Decimal | None = None
    cor: str | None = None

class RespostaVidro(BaseVidro):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Fundos ---
class BaseFundo(BaseEstoque):
    tipo: str
    espessura: Decimal
    largura: Decimal
    altura: Decimal
    cor: str | None = None

class CriarFundo(BaseFundo):
    pass

class AtualizarFundo(BaseModel):
    tipo: str | None = None
    espessura: Decimal | None = None
    quantidade: int | None = None
    largura: Decimal | None = None
    altura: Decimal | None = None
    cor: str | None = None

class RespostaFundo(BaseFundo):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Suplementos ---
class BaseSuplemento(BaseEstoque):
    nome: str
    unidade: str | None = None

class CriarSuplemento(BaseSuplemento):
    pass

class AtualizarSuplemento(BaseModel):
    nome: str | None = None
    quantidade: int | None = None
    unidade: str | None = None

class RespostaSuplemento(BaseSuplemento):
    id: int
    model_config = ConfigDict(from_attributes=True)
