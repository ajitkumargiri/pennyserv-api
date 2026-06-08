from src.auth.presentation.router import router as auth_router
from fastapi import APIRouter

from src.basket.presentation.router import router as basket_router
from src.catalog.presentation.router import router as catalog_router
from src.normalization_quality.presentation.router import router as normalization_quality_router
from src.offers.presentation.router import router as offers_router
from src.pricing.presentation.router import router as pricing_router
from src.receipts.presentation.router import router as receipts_router
from src.search.presentation.router import router as search_router
from src.users.presentation.router import router as users_router

api_router = APIRouter()
api_router.include_router(catalog_router)
api_router.include_router(pricing_router)
api_router.include_router(offers_router)
api_router.include_router(search_router)
api_router.include_router(receipts_router)
api_router.include_router(basket_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(normalization_quality_router)