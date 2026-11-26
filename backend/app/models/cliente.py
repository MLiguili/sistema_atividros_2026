from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Cliente(Base):
    """
    Representação de um cliente cadastrado na loja.
    """

    __tablename__ = "clientes"
    __table_args__ = (Index("ix_clientes_nome_sobrenome", "nome", "sobrenome"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(20), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self) -> str:
        """
        Retorna representação legível do cliente para depuração.
        """
        return f"<Cliente {self.nome} {self.sobrenome}>"
