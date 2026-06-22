from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.compra import StatusCompra, TipoProduto


class BaseItemCompra(BaseModel):
    produto_tipo: TipoProduto
    produto_id: int
    quantidade_solicitada: int = Field(..., ge=1)
    preco_unitario: Decimal = Field(..., ge=0)


class CriarItemCompra(BaseItemCompra):
    pass


class RespostaItemCompra(BaseItemCompra):
    id: int
    quantidade_recebida: int
    model_config = ConfigDict(from_attributes=True)


class CriarFornecedor(BaseModel):
    nome: str
    contato: str | None = None
    telefone: str
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None


class AtualizarFornecedor(BaseModel):
    nome: str | None = None
    contato: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
    cep: str | None = None


class RespostaFornecedor(BaseModel):
    id: int
    nome: str
    contato: str | None
    telefone: str
    email: str | None
    endereco: str | None
    cep: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class CriarOrdemCompra(BaseModel):
    fornecedor_id: int
    itens: list[CriarItemCompra]
    data_prevista: datetime | None = None
    observacao: str | None = None


class ReceberItem(BaseModel):
    item_id: int
    quantidade_recebida: int = Field(..., ge=1)


class ReceberOrdemCompra(BaseModel):
    itens: list[ReceberItem]


class RespostaOrdemCompra(BaseModel):
    id: int
    fornecedor_id: int
    status: StatusCompra
    data_emissao: datetime
    data_prevista: datetime | None
    observacao: str | None
    criado_em: datetime
    atualizado_em: datetime
    itens: list[RespostaItemCompra] = []
    model_config = ConfigDict(from_attributes=True)


class SugestaoCompra(BaseModel):
    produto_tipo: TipoProduto
    produto_id: int
    nome: str
    quantidade_atual: int
    quantidade_sugerida: int
    motivo: str
