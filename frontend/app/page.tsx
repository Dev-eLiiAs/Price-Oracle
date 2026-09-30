"use client";

import { useCallback, useEffect, useState } from "react";
import AddOfferForm from "@/components/AddOfferForm";
import ProductCard from "@/components/ProductCard";
import { listProducts, type Product } from "@/lib/api";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProducts(await listProducts());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error cargando productos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main>
      <div className="page-header">
        <div>
          <h1>Price Oracle</h1>
          <p className="subtitle">Tu lista de deseos con seguimiento de precios.</p>
        </div>
      </div>

      <AddOfferForm onSuccess={load} />

      {loading && <p className="loading-state">Cargando productos...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && products.length === 0 && (
        <div className="empty-state">
          <p>Todavía no tienes productos guardados.</p>
          <p>Pega la URL de un producto de Amazon o PcComponentes arriba para empezar.</p>
        </div>
      )}

      <div className="product-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </main>
  );
}
