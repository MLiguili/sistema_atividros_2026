from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.financeiro import StatusFinanceiro


class CriarContaReceber(BaseModel):
    pedido_id: int | None = None
    descricao: str
    valor: Decimal = Field(..., ge=0)
    data_vencimento: date
    observacao: str | None = None


class ReceberConta(BaseModel):
    valor_recebido: Decimal = Field(..., ge=0)
    data_recebimento: date | None = None


class RespostaContaReceber(BaseModel):
    id: int
    pedido_id: int | None
    descricao: str
    valor: Decimal
    valor_recebido: Decimal
    data_vencimento: date
    data_recebimento: date | None
    status: StatusFinanceiro
    observacao: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class CriarContaPagar(BaseModel):
    fornecedor_id: int | None = None
    descricao: str
    valor: Decimal = Field(..., ge=0)
    data_vencimento: date
    observacao: str | None = None


class PagarConta(BaseModel):
    valor_pago: Decimal = Field(..., ge=0)
    data_pagamento: date | None = None


class RespostaContaPagar(BaseModel):
    id: int
    fornecedor_id: int | None
    descricao: str
    valor: Decimal
    valor_pago: Decimal
    data_vencimento: date
    data_pagamento: date | None
    status: StatusFinanceiro
    observacao: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class FluxoCaixaItem(BaseModel):
    data: date
    tipo: str
    descricao: str
    valor: Decimal
    conta_id: int
    modelo: str


class ResumoFinanceiro(BaseModel):
    total_a_receber: Decimal = Decimal("0.00")
    total_recebido: Decimal = Decimal("0.00")
    total_a_pagar: Decimal = Decimal("0.00")
    total_pago: Decimal = Decimal("0.00")
    saldo_previsto: Decimal = Decimal("0.00")
    contas_receber_vencidas: int = 0
    contas_pagar_vencidas: int = 0
