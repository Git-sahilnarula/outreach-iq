"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-09-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create startup_profiles table
    op.create_table(
        'startup_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('startup_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('services', sa.Text(), nullable=True),
        sa.Column('technical_skills', sa.Text(), nullable=True),
        sa.Column('preferred_job_types', sa.Text(), nullable=True),
        sa.Column('preferred_industries', sa.Text(), nullable=True),
        sa.Column('minimum_budget', sa.Numeric(10, 2), nullable=True),
        sa.Column('preferred_budget', sa.Numeric(10, 2), nullable=True),
        sa.Column('preferred_locations', sa.Text(), nullable=True),
        sa.Column('remote_allowed', sa.Boolean(), nullable=True),
        sa.Column('team_size', sa.Integer(), nullable=True),
        sa.Column('certifications', sa.Text(), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('excluded_keywords', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create portfolio_projects table
    op.create_table(
        'portfolio_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('startup_profile_id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('portfolio_url', sa.String(), nullable=True),
        sa.Column('case_study', sa.Text(), nullable=True),
        sa.Column('technologies', sa.Text(), nullable=True),
        sa.Column('results', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['startup_profile_id'], ['startup_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_job_id', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('job_type', sa.String(), nullable=True),
        sa.Column('salary_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_source_job_id'), 'jobs', ['source_job_id'], unique=False)
    
    # Create job_analyses table
    op.create_table(
        'job_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('can_do', sa.String(), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('match_score', sa.Integer(), nullable=True),
        sa.Column('technical_match', sa.Integer(), nullable=True),
        sa.Column('service_match', sa.Integer(), nullable=True),
        sa.Column('experience_match', sa.Integer(), nullable=True),
        sa.Column('budget_match', sa.Integer(), nullable=True),
        sa.Column('location_match', sa.Integer(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('missing_requirements', sa.Text(), nullable=True),
        sa.Column('risks', sa.Text(), nullable=True),
        sa.Column('recommended_action', sa.String(), nullable=True),
        sa.Column('relevant_portfolio_projects', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )


def downgrade() -> None:
    op.drop_table('job_analyses')
    op.drop_index(op.f('ix_jobs_source_job_id'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_table('portfolio_projects')
    op.drop_table('startup_profiles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
