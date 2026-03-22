from decimal import Decimal

from pydantic import BaseModel, Field


class EntradaCalculo(BaseModel):
    largura: Decimal = Field(..., ge=0, description="Largura em cm")
    altura: Decimal = Field(..., ge=0, description="Altura em cm")
    moldura_id: int | None = None
    vidro_id: int | None = None
    fundo_id: int | None = None


class DetalheCalculo(BaseModel):
    nome: str
    tipo: str # moldura, vidro, fundo
    medida_calculada: Decimal # metros ou m2
    unidade: str # m, m2
    preco_estimado: Decimal


class ResultadoCalculo(BaseModel):
    itens: list[DetalheCalculo]
    total_estimado: Decimal


class MolduraEntrada(BaseModel):
    moldura_id: int
    ordem: int = Field(default=0, ge=0, description="Ordem da moldura, 0 = mais interna")


class EntradaCalculoQuadro(BaseModel):
    obra_largura: Decimal = Field(..., gt=0, description="Largura da obra em cm")
    obra_altura: Decimal = Field(..., gt=0, description="Altura da obra em cm")
    molduras: list[MolduraEntrada] = Field(default_factory=list, description="Lista ordenada de molduras")
    paspatour: bool = Field(default=False, description="Se deve usar paspatour")
    tamanho_paspatour: Decimal = Field(default=0, ge=0, description="Tamanho do paspatour em cm")
    vidro_tipo: str = Field(default="incolor", description="Tipo de vidro: incolor, antireflexo, espelho, outro")
    fundo_id: int | None = None
    quantidade: int = Field(default=1, ge=1, description="Quantidade de quadros")


class ItemCustoQuadro(BaseModel):
    nome: str
    tipo: str
    medida: Decimal
    unidade: str
    preco_unitario: Decimal
    subtotal: Decimal


class DimensoesQuadro(BaseModel):
    obra: dict
    vidro: dict
    molduras: list[dict]
    quadro_final: dict


class ResultadoCalculoQuadro(BaseModel):
    dimensoes: DimensoesQuadro
    custos: list[ItemCustoQuadro]
    total_sugerido: Decimal
    total_final: Decimal
