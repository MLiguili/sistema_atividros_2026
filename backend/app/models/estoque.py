import enum

from sqlalchemy import Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TipoVidro(str, enum.Enum):
    incolor = "incolor"
    antireflexo = "antireflexo"
    espelho = "espelho"
    outro = "outro"

class Moldura(Base):
    """
    Modelo para Molduras.
    """
    __tablename__ = "molduras"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_custo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cor: Mapped[str] = mapped_column(String(50), nullable=False)
    tamanho_barra: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # metros
    largura_barra: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # cm
    marca: Mapped[str] = mapped_column(String(100), nullable=True)

class Vidro(Base):
    """
    Modelo para Vidros.
    """
    __tablename__ = "vidros"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    espessura: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # mm
    tipo: Mapped[TipoVidro] = mapped_column(Enum(TipoVidro), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    largura_chapa: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # cm
    altura_chapa: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # cm
    cor: Mapped[str] = mapped_column(String(50), nullable=True)

class Fundo(Base):
    """
    Modelo para Fundos.
    """
    __tablename__ = "fundos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    espessura: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # mm
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    largura: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # cm
    altura: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # cm
    cor: Mapped[str] = mapped_column(String(50), nullable=True)

class Suplemento(Base):
    """
    Modelo para Suplementos (Cola, Grampos, etc).
    """
    __tablename__ = "suplementos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    unidade: Mapped[str] = mapped_column(String(20), nullable=True) # Ex: ml, kg, un
