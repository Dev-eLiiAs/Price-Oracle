"use client";

import { useState } from "react";
import { createProductFromUrl } from "@/lib/api";

interface Props {
  productId?: string;
  onSuccess: () => void;
}

export default function AddOfferForm({ productId, onSuccess }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createProductFromUrl(url, productId);
      setUrl("");
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido al scrapear la URL");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="add-offer-form">
      <input
        type="url"
        required
        placeholder={
          productId
            ? "URL de otra tienda para este producto"
            : "https://www.amazon.es/... o https://www.pccomponentes.com/..."
        }
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={loading}
      />
      <button type="submit" disabled={loading || url.length === 0}>
        {loading ? "Scrapeando..." : productId ? "Añadir oferta" : "Añadir producto"}
      </button>
      {error && <p className="add-offer-form__error">{error}</p>}
    </form>
  );
}
