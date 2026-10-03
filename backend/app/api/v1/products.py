import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.products import (
    OfferCreate,
    OfferRead,
    PricePointCreate,
    PricePointRead,
    ProductCreate,
    ProductFromUrl,
    ProductRead,
    ProductUpdate,
    RecommendationRead,
)
from app.services import advisor as advisor_service
from app.services import products as products_service
from app.services import scraping as scraping_service
from worker.scraping.exceptions import DuplicateOfferError, ScrapingError

router = APIRouter(prefix="/products", tags=["products"])


async def _to_product_read(db: AsyncSession, product) -> ProductRead:
    best_price, best_retailer = await products_service.get_best_price(db, product)
    latest_prices = await products_service.get_latest_prices(db, product)
    read = ProductRead.model_validate(product)
    read.best_price = best_price
    read.best_price_retailer = best_retailer
    for offer_read in read.offers:
        offer_read.latest_price = latest_prices.get(offer_read.id)
    return read


async def _get_product_or_404(db: AsyncSession, product_id: uuid.UUID):
    product = await products_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=list[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)):
    products = await products_service.list_products(db)
    return [await _to_product_read(db, p) for p in products]


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = await products_service.create_product(db, data)
    return await _to_product_read(db, product)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    product = await _get_product_or_404(db, product_id)
    return await _to_product_read(db, product)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    product = await _get_product_or_404(db, product_id)
    product = await products_service.update_product(db, product, data)
    return await _to_product_read(db, product)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    product = await _get_product_or_404(db, product_id)
    await products_service.delete_product(db, product)


@router.post("/from-url", response_model=ProductRead, status_code=201)
async def create_from_url(data: ProductFromUrl, db: AsyncSession = Depends(get_db)):
    try:
        product = await scraping_service.ingest_from_url(db, data.url, data.product_id)
    except DuplicateOfferError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "product_id": exc.product_id},
        ) from exc
    except ScrapingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _to_product_read(db, product)


@router.post("/{product_id}/offers", response_model=OfferRead, status_code=201)
async def add_offer(
    product_id: uuid.UUID, data: OfferCreate, db: AsyncSession = Depends(get_db)
):
    product = await _get_product_or_404(db, product_id)
    offer = await products_service.add_offer(db, product, data)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.post(
    "/{product_id}/offers/{offer_id}/prices", response_model=PricePointRead, status_code=201
)
async def add_price_point(
    product_id: uuid.UUID,
    offer_id: uuid.UUID,
    data: PricePointCreate,
    db: AsyncSession = Depends(get_db),
):
    product = await _get_product_or_404(db, product_id)
    offer = await products_service.get_offer(db, product, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return await products_service.add_price_point(db, offer, data.price, data.currency)


@router.get("/{product_id}/history", response_model=list[PricePointRead])
async def get_history(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    product = await _get_product_or_404(db, product_id)
    return await products_service.get_history(db, product)


@router.get("/{product_id}/recommendation", response_model=RecommendationRead)
async def get_recommendation(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    product = await _get_product_or_404(db, product_id)
    history = await products_service.get_history(db, product)
    current_price, _ = await products_service.get_best_price(db, product)
    return advisor_service.compute_recommendation(history, current_price)
