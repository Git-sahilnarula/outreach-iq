"""Add proposals table

Revision ID: 004
Revises: 003
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('tone', sa.String(), nullable=False, server_default='professional'),
        sa.Column('custom_instructions', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('estimated_duration', sa.String(), nullable=True),
        sa.Column('estimated_budget', sa.String(), nullable=True),
        sa.Column('relevant_projects', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_proposals_id', 'proposals', ['id'], unique=False)
    op.create_index('ix_proposals_job_id', 'proposals', ['job_id'], unique=False)
    op.create_index('ix_proposals_user_id', 'proposals', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_proposals_user_id', table_name='proposals')
    op.drop_index('ix_proposals_job_id', table_name='proposals')
    op.drop_index('ix_proposals_id', table_name='proposals')
    op.drop_table('proposals')
