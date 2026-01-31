"""Add conversation models (session, message)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create conversation_sessions table
    op.create_table('conversation_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('character_id', sa.String(length=36), nullable=False),
        sa.Column('pack_id', sa.String(length=36), nullable=True),
        sa.Column('session_type', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pack_id'], ['packs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversation_sessions_user_id', 'conversation_sessions', ['user_id'], unique=False)
    op.create_index('idx_conversation_sessions_character_id', 'conversation_sessions', ['character_id'], unique=False)
    op.create_index('idx_conversation_sessions_pack_id', 'conversation_sessions', ['pack_id'], unique=False)

    # Create conversation_messages table
    op.create_table('conversation_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversation_messages_session_id', 'conversation_messages', ['session_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_conversation_messages_session_id', table_name='conversation_messages')
    op.drop_table('conversation_messages')
    op.drop_index('idx_conversation_sessions_pack_id', table_name='conversation_sessions')
    op.drop_index('idx_conversation_sessions_character_id', table_name='conversation_sessions')
    op.drop_index('idx_conversation_sessions_user_id', table_name='conversation_sessions')
    op.drop_table('conversation_sessions')
