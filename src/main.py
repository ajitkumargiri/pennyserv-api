from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.caching.infrastructure.redis_client import close_redis_client
from src.core.api.health import router as health_router
from src.core.api.router import api_router
from src.core.config import get_settings
from src.core.db.session import engine
from src.core.exceptions import register_exception_handlers
from src.core.logging import configure_logging
from src.core.middleware.request_id import RequestIDMiddleware
from src.shared.utils.openapi import use_route_names_as_operation_ids

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_redis_client()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        summary="AI-powered grocery savings and price intelligence platform.",
        description=(
            "PennyServ backend exposes APIs for catalog, pricing, offers, search, "
            "receipts, basket, watchlist, and authentication experiences backed by "
            "normalized upstream SaveBasket data-platform signals."
        ),
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url if settings.is_docs_enabled else None,
        redoc_url=settings.redoc_url if settings.is_docs_enabled else None,
        lifespan=lifespan,
        contact={"name": "PennyServ Platform Team"},
        license_info={"name": "Proprietary"},
        openapi_tags=[
            {"name": "health", "description": "Service health and readiness."},
            {"name": "catalog", "description": "Product catalog services."},
            {"name": "pricing", "description": "Price intelligence endpoints."},
            {"name": "offers", "description": "Offer and promotion discovery."},
            {"name": "search", "description": "Search and ranking APIs."},
            {"name": "receipts", "description": "Receipt ingest and parsing APIs."},
            {"name": "basket", "description": "Basket optimization services."},
            {"name": "users", "description": "User profile and preference APIs."},
            {"name": "auth", "description": "Authentication and authorization APIs."},
            {
                "name": "normalization_quality",
                "description": "Data-quality visibility for upstream normalized records.",
            },
        ],
    )

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_prefix)

    use_route_names_as_operation_ids(app)
    return app


app = create_app()