"""Add catalog models (creator, pack, character, pack_item)

Revision ID: a1b2c3d4e5f6
Revises: 39f28c58020e
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '39f28c58020e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create creators table
    op.create_table('creators',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('bio', sa.String(length=500), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create characters table
    op.create_table('characters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('creator_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create packs table
    op.create_table('packs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('creator_id', sa.String(length=36), nullable=False),
        sa.Column('pack_type', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('age_rating', sa.String(length=10), nullable=False, server_default='all'),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_packs_status', 'packs', ['status'], unique=False)
    op.create_index('idx_packs_pack_type', 'packs', ['pack_type'], unique=False)

    # Create pack_items table (association between packs and characters)
    op.create_table('pack_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('pack_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=30), nullable=False, server_default='character'),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pack_id'], ['packs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pack_items_pack_id', 'pack_items', ['pack_id'], unique=False)
    op.create_index('idx_pack_items_item', 'pack_items', ['item_type', 'item_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_pack_items_item', table_name='pack_items')
    op.drop_index('idx_pack_items_pack_id', table_name='pack_items')
    op.drop_table('pack_items')
    op.drop_index('idx_packs_pack_type', table_name='packs')
    op.drop_index('idx_packs_status', table_name='packs')
    op.drop_table('packs')
    op.drop_table('characters')
    op.drop_table('creators')
