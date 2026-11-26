from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.estoque import Fundo, Moldura, Vidro
    from app.models.tabela_preco import TabelaPrecoPaspatour


class StatusGeral(StrEnum):
    """
    Ciclo de vida comercial do pedido (Eixo 1).
    """

    rascunho = "rascunho"
    confirmado = "confirmado"
    entregue = "entregue"
    arquivado = "arquivado"
    cancelado = "cancelado"


class StatusProducao(StrEnum):
    """
    Etapas lineares de execução na oficina (Eixo 2, sem 'entregue' duplicado).
    """

    pendente = "pendente"
    aguardando_material = "aguardando_material"
    na_fila = "na_fila"
    em_producao = "em_producao"
    embalando = "embalando"
    pronto_entrega = "pronto_entrega"


class StatusFinanceiro(StrEnum):
    """
    Situação financeira derivada dos lançamentos de pagamento (Eixo 3).
    """

    sem_pagamento = "sem_pagamento"
    pagamento_parcial = "pagamento_parcial"
    pago_total = "pago_total"
    estornado = "estornado"


class Eixo(StrEnum):
    """
    Dimensões auditáveis na trilha de eventos do pedido.
    """

    geral = "geral"
    producao = "producao"
    financeiro = "financeiro"
    estoque = "estoque"


class TipoItemPedido(StrEnum):
    """
    Tipos de itens suportados em um pedido ou orçamento.
    """

    quadro_sob_medida = "quadro_sob_medida"
    vidro_avulso = "vidro_avulso"
    servico_livre = "servico_livre"


class TipoDesconto(StrEnum):
    """
    Modalidades de desconto aplicáveis ao pedido.
    """

    valor = "valor"
    percentual = "percentual"


class FormaPagamento(StrEnum):
    """
    Formas de pagamento suportadas nos lançamentos financeiros.
    """

    pix = "pix"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    dinheiro = "dinheiro"
    outro = "outro"


class SequenciaNumeracao(Base):
    """
    Tabela de controle atômico para geração sequencial anual de números de pedido.
    """

    __tablename__ = "sequencia_numeracao"
    __table_args__ = (CheckConstraint("ultimo_valor >= 0", name="ck_sequencia_ultimo_valor_nonneg"),)

    ano: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo_valor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Pedido(Base):
    """
    Entidade central de orçamento e pedido/ordem de serviço do Atividros.
    """

    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint("frete >= 0", name="ck_pedidos_frete_nonneg"),
        CheckConstraint("desconto_valor >= 0", name="ck_pedidos_desconto_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    numero_pedido: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    status_geral: Mapped[StatusGeral] = mapped_column(
        Enum(StatusGeral, name="statusgeral"), default=StatusGeral.rascunho, index=True, nullable=False
    )
    status_producao: Mapped[StatusProducao] = mapped_column(
        Enum(StatusProducao, name="statusproducao"), default=StatusProducao.pendente, index=True, nullable=False
    )
    status_financeiro: Mapped[StatusFinanceiro] = mapped_column(
        Enum(StatusFinanceiro, name="statusfinanceiro"),
        default=StatusFinanceiro.sem_pagamento,
        index=True,
        nullable=False,
    )

    data_validade_orcamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    prazo_entrega: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    endereco_entrega: Mapped[str | None] = mapped_column(String(255), nullable=True)

    frete: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    desconto_valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    desconto_tipo: Mapped[TipoDesconto] = mapped_column(
        Enum(TipoDesconto, name="tipodesconto"), default=TipoDesconto.valor, nullable=False
    )
    subtotal_itens: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    saldo_devedor: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True, nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    cliente: Mapped["Cliente"] = relationship("Cliente")
    itens: Mapped[list["ItemPedido"]] = relationship(
        "ItemPedido", back_populates="pedido", cascade="all, delete-orphan"
    )
    pagamentos: Mapped[list["PagamentoPedido"]] = relationship(
        "PagamentoPedido", back_populates="pedido", cascade="all, delete-orphan"
    )
    eventos: Mapped[list["PedidoEvento"]] = relationship(
        "PedidoEvento", back_populates="pedido", cascade="all, delete-orphan"
    )


class ItemPedido(Base):
    """
    Item pertencente a um pedido, suportando quadro sob medida, vidro avulso ou serviço livre.
    """

    __tablename__ = "itens_pedido"
    __table_args__ = (
        CheckConstraint("quantidade >= 1", name="ck_itens_quantidade_pos"),
        CheckConstraint("preco_unitario >= 0", name="ck_itens_preco_unitario_nonneg"),
        CheckConstraint("subtotal >= 0", name="ck_itens_subtotal_nonneg"),
        CheckConstraint("tamanho_paspatour >= 0", name="ck_itens_paspatour_nonneg"),
        CheckConstraint("mao_de_obra >= 0", name="ck_itens_mao_de_obra_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tipo_item: Mapped[TipoItemPedido] = mapped_column(
        Enum(TipoItemPedido, name="tipoitempedido"), nullable=False
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_sugerido: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    obra_largura: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    obra_altura: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    paspatour: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tamanho_paspatour: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    paspatour_id: Mapped[int | None] = mapped_column(
        ForeignKey("tabela_preco_paspatour.id", ondelete="SET NULL"), nullable=True
    )

    vidro_id: Mapped[int | None] = mapped_column(ForeignKey("vidros.id", ondelete="RESTRICT"), nullable=True)
    vidro_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fundo_id: Mapped[int | None] = mapped_column(ForeignKey("fundos.id", ondelete="RESTRICT"), nullable=True)
    fundo_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mao_de_obra: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    snapshot_calculo: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    molduras: Mapped[list["ItemPedidoMoldura"]] = relationship(
        "ItemPedidoMoldura",
        back_populates="item_pedido",
        cascade="all, delete-orphan",
        order_by="ItemPedidoMoldura.ordem",
    )
    paspatour_ref: Mapped["TabelaPrecoPaspatour | None"] = relationship("TabelaPrecoPaspatour")
    vidro: Mapped["Vidro | None"] = relationship("Vidro")
    fundo: Mapped["Fundo | None"] = relationship("Fundo")


class ItemPedidoMoldura(Base):
    """
    Composição ordenada (interna para externa) de molduras aplicadas a um item do pedido.
    """

    __tablename__ = "itens_pedido_moldura"
    __table_args__ = (
        UniqueConstraint("item_pedido_id", "ordem", name="uq_item_pedido_moldura_ordem"),
        CheckConstraint("ordem >= 0", name="ck_item_moldura_ordem_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_pedido_id: Mapped[int] = mapped_column(
        ForeignKey("itens_pedido.id", ondelete="CASCADE"), index=True, nullable=False
    )
    moldura_id: Mapped[int] = mapped_column(
        ForeignKey("molduras.id", ondelete="RESTRICT"), nullable=False
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    codigo_moldura_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    largura_barra_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tamanho_barra_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    preco_m_aplicado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    altura_calculada_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    largura_calculada_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metragem_total_m: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    barras_sugeridas: Mapped[int] = mapped_column(Integer, nullable=False)

    item_pedido: Mapped["ItemPedido"] = relationship("ItemPedido", back_populates="molduras")
    moldura: Mapped["Moldura"] = relationship("Moldura")


class PagamentoPedido(Base):
    """
    Lançamento financeiro individual (sinal, parcela ou quitação) vinculado a um pedido.
    """

    __tablename__ = "pagamentos_pedido"
    __table_args__ = (CheckConstraint("valor > 0", name="ck_pagamentos_valor_pos"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    forma_pagamento: Mapped[FormaPagamento] = mapped_column(
        Enum(FormaPagamento, name="formapagamento"), nullable=False
    )
    data_pagamento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estornado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="pagamentos")


class PedidoEvento(Base):
    """
    Registro imutável de auditoria para transições de status, pagamentos e baixas de estoque.
    """

    __tablename__ = "pedidos_eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    eixo: Mapped[Eixo] = mapped_column(Enum(Eixo, name="eixo"), nullable=False)
    status_anterior: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_novo: Mapped[str] = mapped_column(String(50), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True, nullable=False
    )

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="eventos")
