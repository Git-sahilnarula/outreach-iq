"""Add linkedin_messages table

Revision ID: 006
Revises: 005
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'linkedin_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('recipient_role', sa.String(), nullable=True),
        sa.Column('recipient_profile_url', sa.String(), nullable=True),
        sa.Column('tone', sa.String(), nullable=False, server_default='value_first'),
        sa.Column('connection_note', sa.String(length=300), nullable=False),
        sa.Column('inmail_subject', sa.String(length=200), nullable=False),
        sa.Column('inmail_body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='GENERATED'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_linkedin_messages_id', 'linkedin_messages', ['id'], unique=False)
    op.create_index('ix_linkedin_messages_job_id', 'linkedin_messages', ['job_id'], unique=False)
    op.create_index('ix_linkedin_messages_user_id', 'linkedin_messages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_linkedin_messages_user_id', table_name='linkedin_messages')
    op.drop_index('ix_linkedin_messages_job_id', table_name='linkedin_messages')
    op.drop_index('ix_linkedin_messages_id', table_name='linkedin_messages')
    op.drop_table('linkedin_messages')
