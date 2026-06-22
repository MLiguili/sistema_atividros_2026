import enum
from datetime import datetime, timezone, date

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StatusFinanceiro(str, enum.Enum):
    pendente = "pendente"
    parcial = "parcial"
    recebido = "recebido"
    pago = "pago"
    cancelado = "cancelado"


class ContaReceber(Base):
    __tablename__ = "contas_receber"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_recebido: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_recebimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusFinanceiro] = mapped_column(Enum(StatusFinanceiro), default=StatusFinanceiro.pendente)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    pedido: Mapped["Pedido"] = relationship("Pedido")


class ContaPagar(Base):
    __tablename__ = "contas_pagar"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fornecedor_id: Mapped[int | None] = mapped_column(ForeignKey("fornecedores.id"), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_pago: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusFinanceiro] = mapped_column(Enum(StatusFinanceiro), default=StatusFinanceiro.pendente)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    fornecedor: Mapped["Fornecedor"] = relationship("Fornecedor")
