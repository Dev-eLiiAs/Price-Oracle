"use client";

import Link from "next/link";
import type { Product } from "@/lib/api";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link href={`/products/${product.id}`} className="product-card">
      <div className="product-card__image">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image_url} alt={product.canonical_name ?? "Producto"} />
        ) : (
          <div className="product-card__image-placeholder">Sin imagen</div>
        )}
      </div>
      <div className="product-card__body">
        <h3>{product.canonical_name ?? "Producto sin nombre"}</h3>
        {product.best_price ? (
          <p className="product-card__price">
            {product.best_price} € en <strong>{product.best_price_retailer}</strong>
          </p>
        ) : (
          <p className="product-card__price product-card__price--empty">Sin precio disponible</p>
        )}
        <p className="product-card__offers">
          {product.offers.length} {product.offers.length === 1 ? "oferta" : "ofertas"} trackeadas
        </p>
      </div>
    </Link>
  );
}
