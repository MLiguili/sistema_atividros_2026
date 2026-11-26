from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.estoque import TipoVidro


class BaseMoldura(BaseModel):
    """
    Campos comuns para cadastro e exibição de molduras (preços em R$/m).
    """

    codigo: str = Field(..., min_length=1, max_length=50)
    quantidade: int = Field(default=0)
    estoque_minimo: int = Field(default=5, ge=0)
    preco_venda: Decimal = Field(..., ge=0)
    preco_custo: Decimal = Field(..., ge=0)
    cor: str = Field(..., min_length=1, max_length=50)
    tamanho_barra: Decimal = Field(..., gt=0)
    largura_barra: Decimal = Field(..., gt=0)
    marca: str | None = Field(default=None, max_length=100)


class CriarMoldura(BaseMoldura):
    """
    Payload de criação de moldura no estoque.
    """

    quantidade: int = Field(default=0, ge=0)


class AtualizarMoldura(BaseModel):
    """
    Payload de atualização parcial de moldura.
    """

    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    quantidade: int | None = None
    estoque_minimo: int | None = Field(default=None, ge=0)
    preco_venda: Decimal | None = Field(default=None, ge=0)
    preco_custo: Decimal | None = Field(default=None, ge=0)
    cor: str | None = Field(default=None, min_length=1, max_length=50)
    tamanho_barra: Decimal | None = Field(default=None, gt=0)
    largura_barra: Decimal | None = Field(default=None, gt=0)
    marca: str | None = Field(default=None, max_length=100)


class RespostaMoldura(BaseMoldura):
    """
    Representação de moldura retornada pela API.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class BaseVidro(BaseModel):
    """
    Campos comuns para vidros e espelhos controlados por m².
    """

    tipo: TipoVidro
    espessura: Decimal = Field(..., gt=0)
    cor: str | None = Field(default=None, max_length=50)
    area_disponivel_m2: Decimal = Field(default=Decimal("0.0000"))
    estoque_minimo_m2: Decimal = Field(default=Decimal("2.0000"), ge=0)


class CriarVidro(BaseVidro):
    """
    Payload de criação de vidro no estoque contínuo em m².
    """


class AtualizarVidro(BaseModel):
    """
    Payload de atualização parcial de vidro.
    """

    tipo: TipoVidro | None = None
    espessura: Decimal | None = Field(default=None, gt=0)
    cor: str | None = Field(default=None, max_length=50)
    area_disponivel_m2: Decimal | None = None
    estoque_minimo_m2: Decimal | None = Field(default=None, ge=0)


class RespostaVidro(BaseVidro):
    """
    Representação de vidro retornada pela API.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class BaseFundo(BaseModel):
    """
    Campos comuns para fundos (MDF, Eucatex, etc.) controlados por m².
    """

    tipo: str = Field(..., min_length=1, max_length=50)
    espessura: Decimal = Field(..., gt=0)
    cor: str | None = Field(default=None, max_length=50)
    area_disponivel_m2: Decimal = Field(default=Decimal("0.0000"))
    estoque_minimo_m2: Decimal = Field(default=Decimal("2.0000"), ge=0)


class CriarFundo(BaseFundo):
    """
    Payload de criação de fundo no estoque contínuo em m².
    """


class AtualizarFundo(BaseModel):
    """
    Payload de atualização parcial de fundo.
    """

    tipo: str | None = Field(default=None, min_length=1, max_length=50)
    espessura: Decimal | None = Field(default=None, gt=0)
    cor: str | None = Field(default=None, max_length=50)
    area_disponivel_m2: Decimal | None = None
    estoque_minimo_m2: Decimal | None = Field(default=None, ge=0)


class RespostaFundo(BaseFundo):
    """
    Representação de fundo retornada pela API.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class EntradaChapas(BaseModel):
    """
    Payload do conversor automático de entrada por chapas (vidros e fundos).
    """

    quantidade_chapas: int = Field(..., ge=1)
    largura_cm: Decimal = Field(..., gt=0)
    altura_cm: Decimal = Field(..., gt=0)


class RespostaEntradaChapas(BaseModel):
    """
    Retorno do cálculo e soma de área após entrada de chapas no estoque.
    """

    id: int
    area_adicionada_m2: Decimal
    area_disponivel_m2: Decimal


class AjusteAreaM2(BaseModel):
    """
    Payload para ajuste manual direto do saldo disponível em m².
    """

    nova_area_m2: Decimal
    motivo: str | None = Field(default=None, max_length=255)


class BaseSuplemento(BaseModel):
    """
    Campos comuns para suplementos de controle manual.
    """

    nome: str = Field(..., min_length=1, max_length=100)
    quantidade: int = Field(default=0, ge=0)
    unidade: str | None = Field(default=None, max_length=20)


class CriarSuplemento(BaseSuplemento):
    """
    Payload de criação de suplemento.
    """


class AtualizarSuplemento(BaseModel):
    """
    Payload de atualização parcial de suplemento.
    """

    nome: str | None = Field(default=None, min_length=1, max_length=100)
    quantidade: int | None = Field(default=None, ge=0)
    unidade: str | None = Field(default=None, max_length=20)


class RespostaSuplemento(BaseSuplemento):
    """
    Representação de suplemento retornada pela API.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)
