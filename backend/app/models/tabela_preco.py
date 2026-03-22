from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TabelaPrecoVidro(Base):
    __tablename__ = "tabela_preco_vidro"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    preco_por_m2: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=True)


class TabelaPrecoPaspatour(Base):
    __tablename__ = "tabela_preco_paspatour"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    preco_por_m2: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
