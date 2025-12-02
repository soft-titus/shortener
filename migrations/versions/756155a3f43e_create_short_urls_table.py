"""create short_urls table

Revision ID: 756155a3f43e
Revises:
Create Date: 2025-12-02 10:11:47.745671

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "756155a3f43e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "short_urls",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("short_code", sa.String(16), unique=True, nullable=False),
        sa.Column("original_url", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.func.now(), nullable=False
        ),
        sa.Column("visits", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("short_urls")
