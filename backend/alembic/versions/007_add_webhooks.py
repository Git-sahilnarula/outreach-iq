"""Add webhook_token to users and create webhook_subscriptions table

Revision ID: 007
Revises: 006
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add webhook_token to users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('webhook_token', sa.String(), nullable=True))
        batch_op.create_index('ix_users_webhook_token', ['webhook_token'], unique=True)

    # Create webhook_subscriptions table
    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('secret_token', sa.String(), nullable=True),
        sa.Column('events', sa.String(), nullable=False, server_default='*'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status_code', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_subscriptions_id', 'webhook_subscriptions', ['id'], unique=False)
    op.create_index('ix_webhook_subscriptions_user_id', 'webhook_subscriptions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_webhook_subscriptions_user_id', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_id', table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_webhook_token')
        batch_op.drop_column('webhook_token')
