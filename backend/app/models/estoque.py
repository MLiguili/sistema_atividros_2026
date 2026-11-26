from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TipoVidro(StrEnum):
    """
    Tipos de vidro comercializados e controlados no estoque.
    """

    incolor = "incolor"
    antireflexo = "antireflexo"
    espelho = "espelho"
    outro = "outro"


class Moldura(Base):
    """
    Modelo de estoque de molduras controladas por barras inteiras e precificadas em R$/m.
    """

    __tablename__ = "molduras"
    __table_args__ = (
        CheckConstraint("tamanho_barra > 0", name="ck_molduras_tamanho_barra_pos"),
        CheckConstraint("largura_barra > 0", name="ck_molduras_largura_barra_pos"),
        CheckConstraint("preco_custo >= 0", name="ck_molduras_preco_custo_nonneg"),
        CheckConstraint("preco_venda >= 0", name="ck_molduras_preco_venda_nonneg"),
        CheckConstraint("estoque_minimo >= 0", name="ck_molduras_estoque_minimo_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    preco_custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cor: Mapped[str] = mapped_column(String(50), nullable=False)
    tamanho_barra: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    largura_barra: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Vidro(Base):
    """
    Modelo de estoque contínuo de vidros e espelhos controlado em metros quadrados (m²).
    """

    __tablename__ = "vidros"
    __table_args__ = (
        CheckConstraint("espessura > 0", name="ck_vidros_espessura_pos"),
        CheckConstraint("estoque_minimo_m2 >= 0", name="ck_vidros_estoque_minimo_nonneg"),
        Index("ix_vidros_tipo_espessura_cor", "tipo", "espessura", "cor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoVidro] = mapped_column(Enum(TipoVidro, name="tipovidro"), index=True, nullable=False)
    espessura: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    area_disponivel_m2: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000"), nullable=False
    )
    estoque_minimo_m2: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("2.0000"), nullable=False
    )


class Fundo(Base):
    """
    Modelo de estoque contínuo de fundos (MDF, Eucatex, etc.) controlado em m².
    """

    __tablename__ = "fundos"
    __table_args__ = (
        CheckConstraint("espessura > 0", name="ck_fundos_espessura_pos"),
        CheckConstraint("estoque_minimo_m2 >= 0", name="ck_fundos_estoque_minimo_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    espessura: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    area_disponivel_m2: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000"), nullable=False
    )
    estoque_minimo_m2: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("2.0000"), nullable=False
    )


class Suplemento(Base):
    """
    Modelo de estoque manual de suplementos acessórios da oficina (cola, grampos, etc.).
    """

    __tablename__ = "suplementos"
    __table_args__ = (CheckConstraint("quantidade >= 0", name="ck_suplementos_quantidade_nonneg"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(20), nullable=True)
