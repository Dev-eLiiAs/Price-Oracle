"use client";

import { useState } from "react";
import Link from "next/link";
import { DuplicateOfferApiError, createProductFromUrl, type Product } from "@/lib/api";
import { INVALID_URL_MESSAGE, SUPPORTED_RETAILERS, isScrapableUrl } from "@/lib/retailers";

interface Props {
  productId?: string;
  /** Known products+offers to check for client-side duplicate detection (instant, no network call). */
  existingProducts?: Product[];
  onSuccess: () => void;
}

type FormError =
  | { type: "validation"; message: string }
  | { type: "duplicate"; message: string; productId: string };

export default function AddOfferForm({ productId, existingProducts = [], onSuccess }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<FormError | null>(null);
  const [errorKey, setErrorKey] = useState(0);
  const [success, setSuccess] = useState(false);

  function showError(err: FormError) {
    setError(err);
    setErrorKey((k) => k + 1); // forces the shake animation to replay even for the same message
  }

  function findDuplicate(candidateUrl: string): Product | undefined {
    const normalized = candidateUrl.trim();
    return existingProducts.find((p) => p.offers.some((o) => o.url.trim() === normalized));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!isScrapableUrl(url)) {
      showError({ type: "validation", message: INVALID_URL_MESSAGE });
      return;
    }

    const duplicate = findDuplicate(url);
    if (duplicate) {
      showError({
        type: "duplicate",
        message: `Ya tienes este producto guardado: ${duplicate.canonical_name ?? "producto sin nombre"}.`,
        productId: duplicate.id,
      });
      return;
    }

    setLoading(true);
    try {
      await createProductFromUrl(url, productId);
      setUrl("");
      onSuccess();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 1600);
    } catch (err) {
      if (err instanceof DuplicateOfferApiError) {
        showError({ type: "duplicate", message: err.message, productId: err.productId });
      } else {
        const message = err instanceof Error ? err.message : "Error desconocido al scrapear la URL";
        showError({ type: "validation", message });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="add-offer">
      <form onSubmit={handleSubmit} className={`add-offer-form${success ? " add-offer-form--success" : ""}`}>
        <input
          type="url"
          required
          placeholder={
            productId
              ? "URL de otra tienda para este producto"
              : "Pega aquí el enlace del producto…"
          }
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            if (error) setError(null);
          }}
          disabled={loading}
          aria-invalid={error ? true : undefined}
        />
        <button type="submit" disabled={loading || url.length === 0 || success}>
          {loading ? (
            <>
              <span className="spinner" aria-hidden="true" /> Buscando…
            </>
          ) : success ? (
            <>
              <span className="check-pop" aria-hidden="true">
                ✓
              </span>{" "}
              Añadido
            </>
          ) : productId ? (
            "Añadir oferta"
          ) : (
            "Añadir producto"
          )}
        </button>
      </form>

      <div className="add-offer__hint">
        <span>Soporte a medida:</span>
        {SUPPORTED_RETAILERS.map((r) => (
          <span key={r.name} className="retailer-chip">
            {r.name}
          </span>
        ))}
        <span className="add-offer__hint-extra">+ funciona con la mayoría de tiendas online</span>
      </div>

      {error && error.type === "validation" && (
        <p key={errorKey} className="add-offer-form__error add-offer-form__error--shake">
          {error.message}
        </p>
      )}

      {error && error.type === "duplicate" && (
        <div key={errorKey} className="duplicate-warning duplicate-warning--shake">
          <span aria-hidden="true">🔁</span>
          <p>
            {error.message}{" "}
            <Link href={`/products/${error.productId}`} className="duplicate-warning__link">
              Ver producto →
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
