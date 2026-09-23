"""Add outreach_messages table

Revision ID: 005
Revises: 004
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'outreach_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('proposal_id', sa.Integer(), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('gmail_message_id', sa.String(), nullable=True),
        sa.Column('gmail_thread_id', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outreach_messages_id', 'outreach_messages', ['id'], unique=False)
    op.create_index('ix_outreach_messages_job_id', 'outreach_messages', ['job_id'], unique=False)
    op.create_index('ix_outreach_messages_user_id', 'outreach_messages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_outreach_messages_user_id', table_name='outreach_messages')
    op.drop_index('ix_outreach_messages_job_id', table_name='outreach_messages')
    op.drop_index('ix_outreach_messages_id', table_name='outreach_messages')
    op.drop_table('outreach_messages')
