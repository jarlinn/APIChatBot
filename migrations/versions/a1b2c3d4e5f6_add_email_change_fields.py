"""add email change fields

Revision ID: a1b2c3d4e5f6
Revises: ed67d9223762
Create Date: 2025-10-07 02:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ed67d9223762'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email change fields to users table
    op.add_column('users', sa.Column('email_change_token', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('email_change_token_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('pending_email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email_change_confirm_token', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove email change fields from users table
    op.drop_column('users', 'email_change_confirm_token')
    op.drop_column('users', 'pending_email')
    op.drop_column('users', 'email_change_token_expires')
    op.drop_column('users', 'email_change_token')