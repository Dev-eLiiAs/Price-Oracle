import pytest

pytestmark = pytest.mark.asyncio


async def test_create_product_with_offer(client):
    resp = await client.post(
        "/api/v1/products",
        json={
            "canonical_name": "Producto de prueba",
            "offer": {
                "url": "https://example.com/producto-1",
                "retailer": "amazon",
                "scraper_strategy": "amazon",
                "price": "100.00",
            },
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["canonical_name"] == "Producto de prueba"
    assert len(body["offers"]) == 1
    assert body["best_price"] == "100.00"

    await client.delete(f"/api/v1/products/{body['id']}")


async def test_best_price_is_minimum_across_offers(client):
    create_resp = await client.post(
        "/api/v1/products",
        json={
            "canonical_name": "Multi-tienda",
            "offer": {
                "url": "https://amazon.example.com/p",
                "retailer": "amazon",
                "scraper_strategy": "amazon",
                "price": "200.00",
            },
        },
    )
    product_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/products/{product_id}/offers",
        json={
            "url": "https://pccomponentes.example.com/p",
            "retailer": "pccomponentes",
            "scraper_strategy": "pccomponentes",
            "price": "150.00",
        },
    )

    get_resp = await client.get(f"/api/v1/products/{product_id}")
    body = get_resp.json()
    assert body["best_price"] == "150.00"
    assert body["best_price_retailer"] == "pccomponentes"
    assert len(body["offers"]) == 2

    history_resp = await client.get(f"/api/v1/products/{product_id}/history")
    assert len(history_resp.json()) == 2

    await client.delete(f"/api/v1/products/{product_id}")


async def test_delete_product_cascades(client):
    create_resp = await client.post(
        "/api/v1/products",
        json={
            "canonical_name": "A borrar",
            "offer": {
                "url": "https://example.com/borrar",
                "retailer": "amazon",
                "scraper_strategy": "amazon",
                "price": "50.00",
            },
        },
    )
    product_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/products/{product_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/products/{product_id}")
    assert get_resp.status_code == 404
