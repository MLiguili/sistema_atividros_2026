"""Atualizando pedidos para 3 eixos de status

Revision ID: novo_pedido_3_eixos
Revises: baf432e819f5
Create Date: 2026-03-22 01:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'novo_pedido_3_eixos'
down_revision: Union[str, Sequence[str], None] = 'baf432e819f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DROP TABLE IF EXISTS itens_pedido')
    op.execute('DROP TABLE IF EXISTS eventos_pedido')
    op.execute('DROP TABLE IF EXISTS pedidos')

    op.create_table('pedidos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('numero_pedido', sa.String(length=20), nullable=False),
    sa.Column('status_geral', sa.String(length=20), nullable=False),
    sa.Column('status_producao', sa.String(length=30), nullable=False),
    sa.Column('status_financeiro', sa.String(length=20), nullable=False),
    sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_sinal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('saldo_devedor', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('endereco_entrega', sa.String(length=255), nullable=True),
    sa.Column('frete', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero_pedido')
    )

    op.create_table('itens_pedido',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pedido_id', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('moldura_id', sa.Integer(), nullable=True),
    sa.Column('vidro_id', sa.Integer(), nullable=True),
    sa.Column('fundo_id', sa.Integer(), nullable=True),
    sa.Column('largura', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('altura', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['fundo_id'], ['fundos.id'], ),
    sa.ForeignKeyConstraint(['moldura_id'], ['molduras.id'], ),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.ForeignKeyConstraint(['vidro_id'], ['vidros.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('pedidos_eventos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pedido_id', sa.Integer(), nullable=False),
    sa.Column('eixo', sa.String(length=20), nullable=False),
    sa.Column('status_anterior', sa.String(length=50), nullable=True),
    sa.Column('status_novo', sa.String(length=50), nullable=False),
    sa.Column('observacao', sa.String(length=255), nullable=True),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('pedidos_eventos')
    op.drop_table('itens_pedido')
    op.drop_table('pedidos')
