import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StatusCompra(str, enum.Enum):
    pendente = "pendente"
    enviada = "enviada"
    parcial = "parcial"
    recebida = "recebida"
    cancelada = "cancelada"


class TipoProduto(str, enum.Enum):
    moldura = "moldura"
    vidro = "vidro"
    fundo = "fundo"
    suplemento = "suplemento"


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    contato: Mapped[str] = mapped_column(String(100), nullable=True)
    telefone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=True)
    cep: Mapped[str] = mapped_column(String(20), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class OrdemCompra(Base):
    __tablename__ = "ordens_compra"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    status: Mapped[StatusCompra] = mapped_column(Enum(StatusCompra), default=StatusCompra.pendente)
    data_emissao: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    data_prevista: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    fornecedor: Mapped["Fornecedor"] = relationship("Fornecedor")
    itens: Mapped[list["ItemCompra"]] = relationship("ItemCompra", back_populates="ordem", cascade="all, delete-orphan")


class ItemCompra(Base):
    __tablename__ = "itens_compra"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ordem_compra_id: Mapped[int] = mapped_column(ForeignKey("ordens_compra.id"), nullable=False)
    produto_tipo: Mapped[TipoProduto] = mapped_column(Enum(TipoProduto), nullable=False)
    produto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_solicitada: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_recebida: Mapped[int] = mapped_column(Integer, default=0)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    ordem: Mapped["OrdemCompra"] = relationship("OrdemCompra", back_populates="itens")
