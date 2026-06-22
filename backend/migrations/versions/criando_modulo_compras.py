"""Criando modulo de compras (fornecedores, ordens, itens)

Revision ID: criando_modulo_compras
Revises: tabela_preco_vidro_paspatour
Create Date: 2026-06-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "criando_modulo_compras"
down_revision: Union[str, Sequence[str], None] = "tabela_preco_vidro_paspatour"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fornecedores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("contato", sa.String(length=100), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("endereco", sa.String(length=255), nullable=True),
        sa.Column("cep", sa.String(length=20), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fornecedores_id"), "fornecedores", ["id"], unique=False)
    op.create_index(op.f("ix_fornecedores_telefone"), "fornecedores", ["telefone"], unique=False)

    op.create_table(
        "ordens_compra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pendente", "enviada", "parcial", "recebida", "cancelada", name="statuscompra"),
            nullable=False,
        ),
        sa.Column("data_emissao", sa.DateTime(), nullable=False),
        sa.Column("data_prevista", sa.DateTime(), nullable=True),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ordens_compra_id"), "ordens_compra", ["id"], unique=False)

    op.create_table(
        "itens_compra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ordem_compra_id", sa.Integer(), nullable=False),
        sa.Column(
            "produto_tipo",
            sa.Enum("moldura", "vidro", "fundo", "suplemento", name="tipoproduto"),
            nullable=False,
        ),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade_solicitada", sa.Integer(), nullable=False),
        sa.Column("quantidade_recebida", sa.Integer(), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["ordem_compra_id"], ["ordens_compra.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_itens_compra_id"), "itens_compra", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_itens_compra_id"), table_name="itens_compra")
    op.drop_table("itens_compra")
    op.drop_index(op.f("ix_ordens_compra_id"), table_name="ordens_compra")
    op.drop_table("ordens_compra")
    op.drop_index(op.f("ix_fornecedores_telefone"), table_name="fornecedores")
    op.drop_index(op.f("ix_fornecedores_id"), table_name="fornecedores")
    op.drop_table("fornecedores")
    op.execute("DROP TYPE IF EXISTS statuscompra")
    op.execute("DROP TYPE IF EXISTS tipoproduto")
