from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.pedido import Eixo, StatusFinanceiro, StatusGeral, StatusProducao


class BaseItemPedido(BaseModel):
    descricao: str = ""
    moldura_id: int | None = None
    vidro_id: int | None = None
    fundo_id: int | None = None
    quantidade: int = Field(default=1, ge=1)
    largura: Decimal = Field(..., ge=0)
    altura: Decimal = Field(..., ge=0)
    preco_unitario: Decimal = Field(default=Decimal("0.00"), ge=0)


class CriarItemPedido(BaseItemPedido):
    pass


class RespostaItemPedido(BaseItemPedido):
    id: int
    subtotal: Decimal
    model_config = ConfigDict(from_attributes=True)


class BasePedido(BaseModel):
    cliente_id: int


class CriarPedido(BasePedido):
    itens: list[CriarItemPedido]
    valor_sinal: Decimal = Field(default=Decimal("0.00"), ge=0)
    endereco_entrega: str | None = None
    frete: Decimal = Field(default=Decimal("0.00"), ge=0)


class AtualizarStatusPedido(BaseModel):
    eixo: Eixo
    novo_status: str
    observacao: str | None = None
    valor_sinal: Decimal | None = None


class RespostaEventoPedido(BaseModel):
    id: int
    eixo: Eixo
    status_anterior: str | None
    status_novo: str
    observacao: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class RespostaPedido(BasePedido):
    id: int
    numero_pedido: str
    status_geral: StatusGeral
    status_producao: StatusProducao
    status_financeiro: StatusFinanceiro
    valor_total: Decimal
    valor_sinal: Decimal
    saldo_devedor: Decimal
    endereco_entrega: str | None
    frete: Decimal
    criado_em: datetime
    atualizado_em: datetime
    itens: list[RespostaItemPedido]
    eventos: list[RespostaEventoPedido] = []
    model_config = ConfigDict(from_attributes=True)
