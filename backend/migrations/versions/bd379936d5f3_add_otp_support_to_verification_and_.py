"""add otp support to verification and reset tokens

Revision ID: bd379936d5f3
Revises: 7e45f35f1ed5
Create Date: 2026-09-14 11:36:49.968900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd379936d5f3'
down_revision = '7e45f35f1ed5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_verification_tokens",
        sa.Column("delivery_method", sa.String(10), nullable=False, server_default="link"),
    )
    op.add_column(
        "email_verification_tokens",
        sa.Column("otp_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "password_reset_tokens",
        sa.Column("delivery_method", sa.String(10), nullable=False, server_default="link"),
    )
    op.add_column(
        "password_reset_tokens",
        sa.Column("otp_hash", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("password_reset_tokens", "otp_hash")
    op.drop_column("password_reset_tokens", "delivery_method")
    op.drop_column("email_verification_tokens", "otp_hash")
    op.drop_column("email_verification_tokens", "delivery_method")