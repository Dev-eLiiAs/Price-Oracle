"use client";

import { useEffect, useState } from "react";
import { type Alert, createAlert, deleteAlert, listAlerts } from "@/lib/api";

export default function PriceAlert({ productId }: { productId: string }) {
  const [alert, setAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [threshold, setThreshold] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justSaved, setJustSaved] = useState(false);

  useEffect(() => {
    listAlerts(productId)
      .then((alerts) => setAlert(alerts.find((a) => a.is_active) ?? null))
      .finally(() => setLoading(false));
  }, [productId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const created = await createAlert(productId, threshold);
      setAlert(created);
      setEditing(false);
      setThreshold("");
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar el aviso");
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove() {
    if (!alert) return;
    setSaving(true);
    try {
      await deleteAlert(alert.id);
      setAlert(null);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return null;

  return (
    <div className={`price-alert${justSaved ? " price-alert--saved" : ""}`}>
      <span
        className={`price-alert__icon${!alert && !editing ? " price-alert__icon--attention" : ""}`}
        aria-hidden="true"
      >
        🔔
      </span>

      {alert ? (
        <div className="price-alert__body">
          <p>
            Te avisaremos por <strong>Telegram y email</strong> en cuanto el precio baje a{" "}
            <strong>{alert.threshold_price} €</strong> o menos.
          </p>
          <button className="price-alert__link" onClick={handleRemove} disabled={saving}>
            Quitar aviso
          </button>
        </div>
      ) : editing ? (
        <form className="price-alert__form" onSubmit={handleSave}>
          <label htmlFor="threshold">Avísame si baja de</label>
          <input
            id="threshold"
            type="number"
            step="0.01"
            min="0"
            required
            placeholder="p. ej. 199.99"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            disabled={saving}
          />
          <span>€</span>
          <button type="submit" disabled={saving || threshold.length === 0}>
            {saving ? <span className="spinner" aria-hidden="true" /> : "Guardar"}
          </button>
          <button
            type="button"
            className="price-alert__link"
            onClick={() => setEditing(false)}
            disabled={saving}
          >
            Cancelar
          </button>
          {error && <p className="add-offer-form__error">{error}</p>}
        </form>
      ) : (
        <div className="price-alert__body">
          <p>
            Puedes recibir un aviso por <strong>Telegram y email</strong> en cuanto este producto
            baje del precio que tú decidas.
          </p>
          <button className="price-alert__link" onClick={() => setEditing(true)}>
            Avisarme cuando baje de precio
          </button>
        </div>
      )}
    </div>
  );
}
