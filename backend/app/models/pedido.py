import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StatusGeral(str, enum.Enum):
    rascunho = "rascunho"
    confirmado = "confirmado"
    cancelado = "cancelado"
    entregue = "entregue"
    arquivado = "arquivado"


class StatusProducao(str, enum.Enum):
    pendente = "pendente"
    aguardando_material = "aguardando_material"
    em_producao = "em_producao"
    para_embalar = "para_embalar"
    pronto_entrega = "pronto_entrega"
    entregue = "entregue"


class StatusFinanceiro(str, enum.Enum):
    sem_pagamento = "sem_pagamento"
    sinal_recebido = "sinal_recebido"
    pago_total = "pago_total"
    estornado = "estornado"


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    numero_pedido: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    status_geral: Mapped[StatusGeral] = mapped_column(Enum(StatusGeral), default=StatusGeral.rascunho)
    status_producao: Mapped[StatusProducao] = mapped_column(Enum(StatusProducao), default=StatusProducao.pendente)
    status_financeiro: Mapped[StatusFinanceiro] = mapped_column(Enum(StatusFinanceiro), default=StatusFinanceiro.sem_pagamento)

    valor_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    valor_sinal: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    saldo_devedor: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    endereco_entrega: Mapped[str | None] = mapped_column(String(255), nullable=True)
    frete: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    cliente: Mapped["Cliente"] = relationship("Cliente")
    itens: Mapped[list["ItemPedido"]] = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    eventos: Mapped[list["PedidoEvento"]] = relationship("PedidoEvento", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)

    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2))

    moldura_id: Mapped[int | None] = mapped_column(ForeignKey("molduras.id"))
    vidro_id: Mapped[int | None] = mapped_column(ForeignKey("vidros.id"))
    fundo_id: Mapped[int | None] = mapped_column(ForeignKey("fundos.id"))

    largura: Mapped[float] = mapped_column(Numeric(10, 2))
    altura: Mapped[float] = mapped_column(Numeric(10, 2))

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    moldura: Mapped["Moldura"] = relationship("Moldura")
    vidro: Mapped["Vidro"] = relationship("Vidro")
    fundo: Mapped["Fundo"] = relationship("Fundo")


class Eixo(str, enum.Enum):
    geral = "geral"
    producao = "producao"
    financeiro = "financeiro"


class PedidoEvento(Base):
    __tablename__ = "pedidos_eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    eixo: Mapped[Eixo] = mapped_column(Enum(Eixo), nullable=False)
    status_anterior: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_novo: Mapped[str] = mapped_column(String(50), nullable=False)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="eventos")
