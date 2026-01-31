"""Add report models (report_reason, report)

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create m_report_reasons table (master data)
    op.create_table('m_report_reasons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('reason_code', sa.String(length=30), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reason_code')
    )

    # Create reports table
    op.create_table('reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('reporter_user_id', sa.String(length=36), nullable=True),
        sa.Column('reason_id', sa.String(length=36), nullable=False),
        sa.Column('target_type', sa.String(length=30), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['reporter_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reason_id'], ['m_report_reasons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reports_status', 'reports', ['status'], unique=False)
    op.create_index('idx_reports_target', 'reports', ['target_type', 'target_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_reports_target', table_name='reports')
    op.drop_index('idx_reports_status', table_name='reports')
    op.drop_table('reports')
    op.drop_table('m_report_reasons')
