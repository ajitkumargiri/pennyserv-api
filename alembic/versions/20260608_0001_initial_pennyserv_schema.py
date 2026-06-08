"""Initial PennyServ schema with data-platform integration boundary.

Revision ID: 20260608_0001
Revises:
Create Date: 2026-06-08 00:00:00

"""

from typing import Sequence
from typing import Union

from alembic import op

from src.core.db.base import Base
from src.core.db import models  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "20260608_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_DROP_ORDER = [
    "saved_searches",
    "receipt_items",
    "receipt_extraction_runs",
    "receipts",
    "basket_optimization_runs",
    "basket_items",
    "baskets",
    "watchlists",
    "refresh_tokens",
    "users",
    "product_embeddings",
    "price_history",
    "product_prices",
    "offers",
    "product_aggregates",
    "products",
    "categories",
    "brands",
    "stores",
    "data_sync_watermarks",
    "data_platform_runs",
]


def upgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in TABLE_DROP_ORDER:
        op.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
