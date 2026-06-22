"""Adicionando tabelas de preco vidro e paspatour

Revision ID: tabela_preco_vidro_paspatour
Revises: novo_pedido_3_eixos
Create Date: 2026-03-22 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'tabela_preco_vidro_paspatour'
down_revision: Union[str, Sequence[str], None] = 'novo_pedido_3_eixos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tabela_preco_vidro',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(length=50), nullable=False),
    sa.Column('preco_por_m2', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tipo')
    )
    
    op.create_table('tabela_preco_paspatour',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=False),
    sa.Column('preco_por_m2', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tabela_preco_paspatour')
    op.drop_table('tabela_preco_vidro')
