from decimal import Decimal

from pydantic import BaseModel, Field


class MolduraEntrada(BaseModel):
    """
    Referência a uma moldura e sua ordem de montagem (0 = mais interna).
    """

    moldura_id: int
    ordem: int = Field(default=0, ge=0, description="Ordem da moldura, 0 = mais interna")


class EntradaCalculoQuadro(BaseModel):
    """
    Parâmetros de entrada para cálculo determinístico de quadro sob medida.
    """

    obra_largura: Decimal = Field(..., gt=0, description="Largura da obra em cm")
    obra_altura: Decimal = Field(..., gt=0, description="Altura da obra em cm")
    quantidade: int = Field(default=1, ge=1, description="Quantidade de quadros")
    paspatour: bool = Field(default=False, description="Se deve usar paspatour")
    tamanho_paspatour: Decimal = Field(default=Decimal("0"), ge=0, description="Borda do paspatour em cm")
    paspatour_id: int | None = Field(default=None, description="ID na tabela de preços de paspatour")
    molduras: list[MolduraEntrada] = Field(default_factory=list, description="Lista ordenada de molduras")
    vidro_tipo: str | None = Field(default=None, description="Tipo de vidro: incolor, antireflexo, espelho, outro")
    vidro_id: int | None = Field(default=None, description="ID da chapa de vidro para baixa física opcional")
    fundo_id: int | None = Field(default=None, description="ID do fundo em estoque para baixa física opcional")
    fundo_tipo: str | None = Field(default=None, description="Tipo de fundo na tabela de preços")
    mao_de_obra: Decimal = Field(default=Decimal("0.00"), ge=0, description="Mão de obra em R$ por unidade")


class EntradaCalculoVidroAvulso(BaseModel):
    """
    Parâmetros de entrada para cálculo determinístico de corte de vidro ou espelho avulso.
    """

    largura: Decimal = Field(..., gt=0, description="Largura da peça em cm")
    altura: Decimal = Field(..., gt=0, description="Altura da peça em cm")
    quantidade: int = Field(default=1, ge=1, description="Quantidade de peças")
    vidro_tipo: str = Field(..., min_length=1, description="Tipo de vidro/espelho na tabela de preços")
    vidro_id: int | None = Field(default=None, description="ID da chapa de vidro para baixa física opcional")
    mao_de_obra: Decimal = Field(default=Decimal("0.00"), ge=0, description="Mão de obra em R$ por unidade")


class Medida2D(BaseModel):
    """
    Dimensão bidimensional em centímetros.
    """

    altura: Decimal
    largura: Decimal


class DimensaoMolduraCalculada(BaseModel):
    """
    Detalhamento dimensional e de consumo calculado para cada camada de moldura.
    """

    moldura_id: int
    ordem: int
    codigo: str
    largura_barra_cm: Decimal
    tamanho_barra_m: Decimal
    preco_m_aplicado: Decimal
    altura: Decimal
    largura: Decimal
    perimetro_seco_m: Decimal
    perda_45_m: Decimal
    metragem_total_m: Decimal
    barras_sugeridas: int


class DimensoesQuadro(BaseModel):
    """
    Propagação completa de dimensões de dentro para fora (Obra -> Vidro -> Molduras -> Quadro Final).
    """

    obra: Medida2D
    vidro: Medida2D
    molduras: list[DimensaoMolduraCalculada]
    quadro_final: Medida2D


class AreasCalculo(BaseModel):
    """
    Áreas reais (para baixa física) e cobradas (com área mínima comercial) em m².
    """

    area_real_m2: Decimal
    area_cobrada_vidro_m2: Decimal
    area_minima_vidro_m2: Decimal
    area_fundo_m2: Decimal


class ItemCustoQuadro(BaseModel):
    """
    Linha unitária de custo discriminado no resultado do cálculo.
    """

    nome: str
    tipo: str
    medida: Decimal
    unidade: str
    preco_unitario: Decimal
    subtotal: Decimal


class ResultadoCalculoQuadro(BaseModel):
    """
    Resposta completa do motor único de cálculo pronta para exibição e snapshot imutável.
    """

    dimensoes: DimensoesQuadro
    areas: AreasCalculo
    custos: list[ItemCustoQuadro]
    valor_sugerido_unitario: Decimal
    total_sugerido: Decimal
    total_final: Decimal
    descricao_sugerida: str
