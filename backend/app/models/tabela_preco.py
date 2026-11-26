from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TabelaPrecoVidro(Base):
    """
    Tabela de preços por m² e área mínima comercial para vidros e espelhos.
    """

    __tablename__ = "tabela_preco_vidro"
    __table_args__ = (
        CheckConstraint("preco_por_m2 >= 0", name="ck_tabela_vidro_preco_nonneg"),
        CheckConstraint("area_minima_m2 >= 0", name="ck_tabela_vidro_area_min_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    preco_por_m2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    area_minima_m2: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.2500"), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TabelaPrecoFundo(Base):
    """
    Tabela de preços por m² para tipos de fundo utilizados na montagem de quadros.
    """

    __tablename__ = "tabela_preco_fundo"
    __table_args__ = (CheckConstraint("preco_por_m2 >= 0", name="ck_tabela_fundo_preco_nonneg"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    preco_por_m2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TabelaPrecoPaspatour(Base):
    """
    Tabela de preços por m² para opções de paspatour.
    """

    __tablename__ = "tabela_preco_paspatour"
    __table_args__ = (CheckConstraint("preco_por_m2 >= 0", name="ck_tabela_paspatour_preco_nonneg"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    descricao: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    preco_por_m2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
