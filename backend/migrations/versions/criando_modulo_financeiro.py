"""Criando modulo financeiro (contas_receber, contas_pagar)

Revision ID: criando_modulo_financeiro
Revises: criando_modulo_compras
Create Date: 2026-06-21 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "criando_modulo_financeiro"
down_revision: Union[str, Sequence[str], None] = "criando_modulo_compras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contas_receber",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_recebido", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_recebimento", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pendente", "parcial", "recebido", "pago", "cancelado", name="statusfinanceiro"),
            nullable=False,
        ),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contas_receber_id"), "contas_receber", ["id"], unique=False)

    op.create_table(
        "contas_pagar",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_pago", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pendente", "parcial", "recebido", "pago", "cancelado", name="statusfinanceiro"),
            nullable=False,
        ),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contas_pagar_id"), "contas_pagar", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contas_pagar_id"), table_name="contas_pagar")
    op.drop_table("contas_pagar")
    op.drop_index(op.f("ix_contas_receber_id"), table_name="contas_receber")
    op.drop_table("contas_receber")
    op.execute("DROP TYPE IF EXISTS statusfinanceiro")
