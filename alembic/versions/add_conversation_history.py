"""Add conversation history table.

Revision ID: add_conversation_history
Revises: 12_1c8f5b
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_conversation_history'
down_revision: Union[str, None] = '12_1c8f5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_history_user_id'), 'conversation_history', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_conversation_history_user_id'), table_name='conversation_history')
    op.drop_table('conversation_history')
