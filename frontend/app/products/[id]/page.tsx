"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AddOfferForm from "@/components/AddOfferForm";
import PriceAlert from "@/components/PriceAlert";
import PriceChart from "@/components/PriceChart";
import RecommendationBadge from "@/components/RecommendationBadge";
import {
  deleteProduct,
  getHistory,
  getProduct,
  getRecommendation,
  type PricePoint,
  type Product,
  type Recommendation,
} from "@/lib/api";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = params.id;

  const [product, setProduct] = useState<Product | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [productData, historyData, recommendationData] = await Promise.all([
        getProduct(productId),
        getHistory(productId),
        getRecommendation(productId),
      ]);
      setProduct(productData);
      setHistory(historyData);
      setRecommendation(recommendationData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error cargando el producto");
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete() {
    if (!confirm("¿Eliminar este producto y todo su histórico?")) return;
    await deleteProduct(productId);
    window.location.href = "/";
  }

  if (loading) {
    return (
      <main>
        <p className="loading-state">
          <span className="spinner" aria-hidden="true" /> Cargando…
        </p>
      </main>
    );
  }
  if (error) return <main><p className="error">{error}</p></main>;
  if (!product) return null;

  const pricedOffers = product.offers.filter((o) => o.latest_price !== null);
  const cheapestOfferId =
    pricedOffers.length > 1
      ? pricedOffers.reduce((min, o) =>
          parseFloat(o.latest_price!) < parseFloat(min.latest_price!) ? o : min
        ).id
      : null;

  return (
    <main>
      <Link href="/" className="back-link">
        ← Volver al listado
      </Link>

      <div className="product-detail__header">
        <h1>{product.canonical_name ?? "Producto sin nombre"}</h1>
        <button onClick={handleDelete} className="button--danger">
          Eliminar
        </button>
      </div>

      {product.best_price ? (
        <p className="product-detail__price">
          {product.best_price} € · <strong>{product.best_price_retailer}</strong>
        </p>
      ) : (
        <p className="product-detail__price product-card__price--empty">
          Sin precio disponible.
        </p>
      )}

      {recommendation && <RecommendationBadge recommendation={recommendation} />}

      <PriceAlert productId={product.id} />

      <section>
        <h2>Histórico de precios</h2>
        <div className="card chart-card">
          <PriceChart history={history} offers={product.offers} />
        </div>
      </section>

      <section>
        <h2>Ofertas trackeadas</h2>
        <div className="card offers-list">
          {product.offers.map((offer) => (
            <div
              key={offer.id}
              className={`offer-row${offer.id === cheapestOfferId ? " offer-row--cheapest" : ""}`}
            >
              {offer.latest_price ? (
                <span className="offer-row__price">{offer.latest_price} €</span>
              ) : (
                <span className="offer-row__price offer-row__price--empty">Sin precio</span>
              )}
              {offer.id === cheapestOfferId && (
                <span className="offer-row__best-badge">Más barato</span>
              )}
              <span className="offer-row__retailer">{offer.retailer}</span>
              <span className={`status-badge status-badge--${offer.status}`}>
                {offer.status}
              </span>
              <span className="offer-row__meta">
                {offer.last_scraped_at
                  ? `Actualizado ${new Date(offer.last_scraped_at).toLocaleString("es-ES")}`
                  : "Sin actualizar todavía"}
              </span>
              <a href={offer.url} target="_blank" rel="noreferrer" className="offer-row__link">
                Ver oferta →
              </a>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Añadir oferta de otra tienda</h2>
        <div className="card">
          <AddOfferForm productId={product.id} onSuccess={load} existingProducts={[product]} />
        </div>
      </section>
    </main>
  );
}
