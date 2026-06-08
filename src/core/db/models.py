from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.db.base import Base
from src.shared.utils.vector import EMBEDDING_DIMENSION, EmbeddingVector


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DataPlatformRun(TimestampMixin, Base):
    __tablename__ = "data_platform_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_system: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default="savebasket-data-platform",
    )
    run_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    sync_watermarks: Mapped[list[DataSyncWatermark]] = relationship(back_populates="last_success_run")

    __table_args__ = (
        UniqueConstraint("upstream_run_id", name="uq_data_platform_runs_upstream_run_id"),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_data_platform_runs_completed_after_started",
        ),
        Index("ix_data_platform_runs_status_started", "status", "started_at"),
    )


class DataSyncWatermark(TimestampMixin, Base):
    __tablename__ = "data_sync_watermarks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_name: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False, server_default="global")
    upstream_cursor: Mapped[str | None] = mapped_column(String(256), nullable=True)
    upstream_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_success_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    sync_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    last_success_run: Mapped[DataPlatformRun | None] = relationship(back_populates="sync_watermarks")

    __table_args__ = (
        UniqueConstraint("entity_name", "scope_key", name="uq_data_sync_watermarks_entity_scope"),
        Index("ix_data_sync_watermarks_last_synced", "last_synced_at"),
    )


class Store(TimestampMixin, Base):
    __tablename__ = "stores"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_store_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    chain_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="US")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    prices: Mapped[list[ProductPrice]] = relationship(back_populates="store")
    offers: Mapped[list[Offer]] = relationship(back_populates="store")
    aggregates: Mapped[list[ProductAggregate]] = relationship(back_populates="store")
    price_history_rows: Mapped[list[PriceHistory]] = relationship(back_populates="store")
    baskets: Mapped[list[Basket]] = relationship(back_populates="store")
    receipts: Mapped[list[Receipt]] = relationship(back_populates="store")
    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="store")

    __table_args__ = (
        UniqueConstraint("upstream_store_id", name="uq_stores_upstream_store_id"),
        UniqueConstraint("slug", name="uq_stores_slug"),
        Index("ix_stores_name", "name"),
    )


class Brand(TimestampMixin, Base):
    __tablename__ = "brands"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_brand_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)

    products: Mapped[list[Product]] = relationship(back_populates="brand")

    __table_args__ = (
        UniqueConstraint("upstream_brand_id", name="uq_brands_upstream_brand_id"),
        UniqueConstraint("normalized_name", name="uq_brands_normalized_name"),
        Index("ix_brands_name", "name"),
    )


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_category_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    parent: Mapped[Category | None] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    products: Mapped[list[Product]] = relationship(back_populates="category")
    offers: Mapped[list[Offer]] = relationship(back_populates="category")

    __table_args__ = (
        UniqueConstraint("upstream_category_id", name="uq_categories_upstream_category_id"),
        UniqueConstraint("slug", name="uq_categories_slug"),
        UniqueConstraint("parent_id", "name", name="uq_categories_parent_name"),
        Index("ix_categories_parent", "parent_id"),
    )


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    brand_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    family: Mapped[str] = mapped_column(String(100), nullable=False)
    product_type: Mapped[str] = mapped_column("type", String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    storage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flavor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fat_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_tier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diet_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    packaging_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normalization_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    match_quality: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    brand: Mapped[Brand | None] = relationship(back_populates="products")
    category: Mapped[Category | None] = relationship(back_populates="products")
    prices: Mapped[list[ProductPrice]] = relationship(back_populates="product")
    offers: Mapped[list[Offer]] = relationship(back_populates="product")
    price_history_rows: Mapped[list[PriceHistory]] = relationship(back_populates="product")
    aggregates: Mapped[list[ProductAggregate]] = relationship(back_populates="product")
    embeddings: Mapped[list[ProductEmbedding]] = relationship(back_populates="product")
    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="product")
    basket_items: Mapped[list[BasketItem]] = relationship(back_populates="product")
    receipt_items: Mapped[list[ReceiptItem]] = relationship(back_populates="matched_product")

    __table_args__ = (
        UniqueConstraint("upstream_product_id", name="uq_products_upstream_product_id"),
        CheckConstraint("quantity > 0", name="ck_products_quantity_positive"),
        CheckConstraint(
            "normalization_confidence >= 0 AND normalization_confidence <= 1",
            name="ck_products_normalization_confidence_range",
        ),
        CheckConstraint(
            "match_quality IS NULL OR (match_quality >= 0 AND match_quality <= 1)",
            name="ck_products_match_quality_range",
        ),
        Index("ix_products_taxonomy", "department", "family", "type"),
        Index("ix_products_normalized_name", "normalized_name"),
        Index("ix_products_source_run", "source_run_id"),
    )


class ProductAggregate(TimestampMixin, Base):
    __tablename__ = "product_aggregates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=True,
    )
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    search_rank_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    popularity_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    aggregate_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    product: Mapped[Product] = relationship(back_populates="aggregates")
    store: Mapped[Store | None] = relationship(back_populates="aggregates")

    __table_args__ = (
        UniqueConstraint(
            "product_id", "store_id", "snapshot_at", name="uq_product_aggregates_product_store_snapshot"
        ),
        Index("ix_product_aggregates_product_store", "product_id", "store_id"),
    )


class Offer(TimestampMixin, Base):
    __tablename__ = "offers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_offer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    store_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mechanic_type: Mapped[str] = mapped_column(String(64), nullable=False)
    mechanic_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    effective_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    effective_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    store: Mapped[Store] = relationship(back_populates="offers")
    product: Mapped[Product | None] = relationship(back_populates="offers")
    category: Mapped[Category | None] = relationship(back_populates="offers")
    prices: Mapped[list[ProductPrice]] = relationship(back_populates="active_offer")
    price_history_rows: Mapped[list[PriceHistory]] = relationship(back_populates="offer")

    __table_args__ = (
        UniqueConstraint("upstream_offer_id", name="uq_offers_upstream_offer_id"),
        CheckConstraint("ends_at >= starts_at", name="ck_offers_valid_window"),
        CheckConstraint(
            "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
            name="ck_offers_discount_percent_range",
        ),
        Index("ix_offers_store_window", "store_id", "starts_at", "ends_at"),
        Index("ix_offers_active", "is_active"),
    )


class ProductPrice(TimestampMixin, Base):
    __tablename__ = "product_prices"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    store_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    active_offer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    effective_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    store: Mapped[Store] = relationship(back_populates="prices")
    product: Mapped[Product] = relationship(back_populates="prices")
    active_offer: Mapped[Offer | None] = relationship(back_populates="prices")
    history_rows: Mapped[list[PriceHistory]] = relationship(back_populates="product_price")

    __table_args__ = (
        CheckConstraint("current_price >= 0", name="ck_product_prices_current_non_negative"),
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="ck_product_prices_unit_non_negative"),
        CheckConstraint(
            "effective_price IS NULL OR effective_price >= 0",
            name="ck_product_prices_effective_non_negative",
        ),
        UniqueConstraint("store_id", "product_id", "observed_at", name="uq_product_prices_store_product_observed"),
        Index("ix_product_prices_store_product", "store_id", "product_id"),
        Index("ix_product_prices_product_observed", "product_id", "observed_at"),
        Index(
            "uq_product_prices_store_product_current",
            "store_id",
            "product_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    store_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_price_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product_prices.id", ondelete="SET NULL"),
        nullable=True,
    )
    offer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    listed_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    effective_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")

    store: Mapped[Store] = relationship(back_populates="price_history_rows")
    product: Mapped[Product] = relationship(back_populates="price_history_rows")
    product_price: Mapped[ProductPrice | None] = relationship(back_populates="history_rows")
    offer: Mapped[Offer | None] = relationship(back_populates="price_history_rows")

    __table_args__ = (
        CheckConstraint("listed_price >= 0", name="ck_price_history_listed_non_negative"),
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="ck_price_history_unit_non_negative"),
        CheckConstraint(
            "effective_price IS NULL OR effective_price >= 0",
            name="ck_price_history_effective_non_negative",
        ),
        Index("ix_price_history_store_product_observed", "store_id", "product_id", "observed_at"),
    )


class ProductEmbedding(TimestampMixin, Base):
    __tablename__ = "product_embeddings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_platform_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    vector: Mapped[list[float]] = mapped_column(EmbeddingVector, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False, default=EMBEDDING_DIMENSION)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    product: Mapped[Product] = relationship(back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint("product_id", "model_name", name="uq_product_embeddings_product_model"),
        CheckConstraint(f"dimensions = {EMBEDDING_DIMENSION}", name="ck_product_embeddings_dimensions"),
        Index("ix_product_embeddings_product", "product_id"),
        Index("ix_product_embeddings_model", "model_name"),
    )


Index(
    "ix_product_embeddings_vector_ivfflat",
    ProductEmbedding.vector,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 100},
    postgresql_ops={"vector": "vector_cosine_ops"},
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_subject: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="user")
    baskets: Mapped[list[Basket]] = relationship(back_populates="user")
    basket_optimization_runs: Mapped[list[BasketOptimizationRun]] = relationship(back_populates="user")
    receipts: Mapped[list[Receipt]] = relationship(back_populates="user")
    saved_searches: Mapped[list[SavedSearch]] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("external_subject", name="uq_users_external_subject"),
        Index("ix_users_email", "email"),
    )


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        CheckConstraint("expires_at > issued_at", name="ck_refresh_tokens_expires_after_issued"),
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
    )


class SavedSearch(TimestampMixin, Base):
    __tablename__ = "saved_searches"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    query_text: Mapped[str] = mapped_column(String(255), nullable=False)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="saved_searches")

    __table_args__ = (
        UniqueConstraint("user_id", "query_text", name="uq_saved_searches_user_query"),
        Index("ix_saved_searches_user_last_executed", "user_id", "last_executed_at"),
    )


class Watchlist(TimestampMixin, Base):
    __tablename__ = "watchlists"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notify_on_price_drop: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notify_on_offer: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    user: Mapped[User] = relationship(back_populates="watchlists")
    product: Mapped[Product] = relationship(back_populates="watchlists")
    store: Mapped[Store | None] = relationship(back_populates="watchlists")

    __table_args__ = (
        CheckConstraint("target_price IS NULL OR target_price >= 0", name="ck_watchlists_target_price_non_negative"),
        UniqueConstraint("user_id", "product_id", "store_id", name="uq_watchlists_user_product_store"),
        Index("ix_watchlists_user_active", "user_id", "is_active"),
    )


class Basket(TimestampMixin, Base):
    __tablename__ = "baskets"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, server_default="Default Basket")
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped[User] = relationship(back_populates="baskets")
    store: Mapped[Store | None] = relationship(back_populates="baskets")
    items: Mapped[list[BasketItem]] = relationship(back_populates="basket")
    optimization_runs: Mapped[list[BasketOptimizationRun]] = relationship(back_populates="basket")

    __table_args__ = (
        CheckConstraint("status IN ('open','archived','checked_out')", name="ck_baskets_status_allowed"),
        Index("ix_baskets_user_status", "user_id", "status"),
    )


class BasketItem(TimestampMixin, Base):
    __tablename__ = "basket_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    basket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("baskets.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, server_default="1")
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expected_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    basket: Mapped[Basket] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="basket_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_basket_items_quantity_positive"),
        CheckConstraint(
            "expected_price IS NULL OR expected_price >= 0", name="ck_basket_items_expected_price_non_negative"
        ),
        UniqueConstraint("basket_id", "product_id", name="uq_basket_items_basket_product"),
        Index("ix_basket_items_basket_selected", "basket_id", "selected"),
    )


class BasketOptimizationRun(TimestampMixin, Base):
    __tablename__ = "basket_optimization_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    basket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("baskets.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chosen_products_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    rejected_candidates_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    explanation_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    estimated_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    optimized_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_savings: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    basket: Mapped[Basket] = relationship(back_populates="optimization_runs")
    user: Mapped[User] = relationship(back_populates="basket_optimization_runs")

    __table_args__ = (
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_basket_optimization_runs_completed_after_started",
        ),
        CheckConstraint(
            "estimated_savings IS NULL OR estimated_savings >= 0",
            name="ck_basket_optimization_runs_savings_non_negative",
        ),
        Index("ix_basket_optimization_runs_basket_started", "basket_id", "started_at"),
    )


class Receipt(TimestampMixin, Base):
    __tablename__ = "receipts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_receipt_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tax: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped[User] = relationship(back_populates="receipts")
    store: Mapped[Store | None] = relationship(back_populates="receipts")
    extraction_runs: Mapped[list[ReceiptExtractionRun]] = relationship(back_populates="receipt")
    items: Mapped[list[ReceiptItem]] = relationship(back_populates="receipt")

    __table_args__ = (
        CheckConstraint("subtotal IS NULL OR subtotal >= 0", name="ck_receipts_subtotal_non_negative"),
        CheckConstraint("tax IS NULL OR tax >= 0", name="ck_receipts_tax_non_negative"),
        CheckConstraint("total IS NULL OR total >= 0", name="ck_receipts_total_non_negative"),
        UniqueConstraint("user_id", "external_receipt_ref", name="uq_receipts_user_external_ref"),
        Index("ix_receipts_user_purchased_at", "user_id", "purchased_at"),
    )


class ReceiptExtractionRun(TimestampMixin, Base):
    __tablename__ = "receipt_extraction_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    receipt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    extractor_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overall_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    receipt: Mapped[Receipt] = relationship(back_populates="extraction_runs")
    items: Mapped[list[ReceiptItem]] = relationship(back_populates="extraction_run")

    __table_args__ = (
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_receipt_extraction_runs_completed_after_started",
        ),
        CheckConstraint(
            "overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)",
            name="ck_receipt_extraction_runs_confidence_range",
        ),
    )


class ReceiptItem(TimestampMixin, Base):
    __tablename__ = "receipt_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    receipt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("receipt_extraction_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, server_default="1")
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    matched_product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_match_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    item_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    receipt: Mapped[Receipt] = relationship(back_populates="items")
    extraction_run: Mapped[ReceiptExtractionRun | None] = relationship(back_populates="items")
    matched_product: Mapped[Product | None] = relationship(back_populates="receipt_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_receipt_items_quantity_positive"),
        CheckConstraint(
            "match_confidence IS NULL OR (match_confidence >= 0 AND match_confidence <= 1)",
            name="ck_receipt_items_match_confidence_range",
        ),
        UniqueConstraint("receipt_id", "line_number", name="uq_receipt_items_receipt_line"),
        Index("ix_receipt_items_matched_product", "matched_product_id"),
    )


__all__ = [
    "Basket",
    "BasketItem",
    "BasketOptimizationRun",
    "Brand",
    "Category",
    "DataPlatformRun",
    "DataSyncWatermark",
    "Offer",
    "PriceHistory",
    "Product",
    "ProductAggregate",
    "ProductEmbedding",
    "ProductPrice",
    "Receipt",
    "ReceiptExtractionRun",
    "ReceiptItem",
    "RefreshToken",
    "SavedSearch",
    "Store",
    "User",
    "Watchlist",
    "EMBEDDING_DIMENSION",
]
