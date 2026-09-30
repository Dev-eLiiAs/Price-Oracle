from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import alerts, health, products
from app.core.config import settings

app = FastAPI(title="Price Oracle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
