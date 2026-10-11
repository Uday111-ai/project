"""initial schema

This is the first Alembic migration for this project. It's introduced
before any production data exists (per the security review), so rather
than replaying the app's incremental history, it creates the full,
current schema directly — including email verification and per-account
lockout, which didn't exist in the original MVP.

Revision ID: 0001
Revises:
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Case-insensitive uniqueness on username/email, enforced by the
    # database itself rather than only checked in application code. Plain
    # CREATE UNIQUE INDEX ... (lower(col)) is supported by both Postgres
    # and SQLite (>=3.9), so this works for local/test SQLite too.
    op.execute(
        "CREATE UNIQUE INDEX ix_users_username_lower "
        "ON users (lower(username))"
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_users_email_lower "
        "ON users (lower(email))"
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_email_verification_tokens_user_id",
        "email_verification_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    # This is the fix for "no index on password_reset_tokens.user_id" —
    # Postgres does not auto-index foreign key columns.
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_reset_tokens_user_id", table_name="password_reset_tokens"
    )
    op.drop_table("password_reset_tokens")

    op.drop_index(
        "ix_email_verification_tokens_user_id",
        table_name="email_verification_tokens",
    )
    op.drop_table("email_verification_tokens")

    op.execute("DROP INDEX ix_users_email_lower")
    op.execute("DROP INDEX ix_users_username_lower")
    op.drop_table("users")
