"""add cascade delete to token foreign keys

Revision ID: 7e45f35f1ed5
Revises: 0001
Create Date: 2026-09-13 11:00:45.652343

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e45f35f1ed5'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
    )
