"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Offer, PricePoint } from "@/lib/api";

const SERIES_COLORS = [
  "var(--series-1)",
  "var(--series-2)",
  "var(--series-3)",
  "var(--series-4)",
  "var(--series-5)",
  "var(--series-6)",
  "var(--series-7)",
  "var(--series-8)",
];

const RANGES = [
  { label: "1 mes", days: 30 },
  { label: "3 meses", days: 90 },
  { label: "6 meses", days: 180 },
  { label: "1 año", days: 365 },
  { label: "Todo", days: null },
] as const;

function dayKey(iso: string): string {
  return iso.slice(0, 10); // YYYY-MM-DD, local-agnostic enough for daily bucketing
}

export default function PriceChart({
  history,
  offers,
}: {
  history: PricePoint[];
  offers: Offer[];
}) {
  const [range, setRange] = useState<(typeof RANGES)[number]>(RANGES[4]);
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  const retailerByOfferId = useMemo(
    () => new Map(offers.map((o) => [o.id, o.retailer])),
    [offers]
  );
  // Stable order: first-tracked store keeps the first color slot forever,
  // so a line's color never shifts as more offers are added later.
  const retailers = useMemo(
    () =>
      [...offers]
        .sort((a, b) => a.created_at.localeCompare(b.created_at))
        .map((o) => o.retailer),
    [offers]
  );

  const filteredHistory = useMemo(() => {
    if (range.days === null) return history;
    const cutoff = Date.now() - range.days * 24 * 60 * 60 * 1000;
    return history.filter((p) => new Date(p.scraped_at).getTime() >= cutoff);
  }, [history, range]);

  const data = useMemo(() => {
    const rowsByDay = new Map<string, Record<string, number | string>>();
    for (const point of filteredHistory) {
      const retailer = retailerByOfferId.get(point.offer_id);
      if (!retailer) continue;
      const key = dayKey(point.scraped_at);
      const row = rowsByDay.get(key) ?? { date: key };
      row[retailer] = Number(point.price); // last price of the day wins
      rowsByDay.set(key, row);
    }
    return [...rowsByDay.values()].sort((a, b) => (a.date as string).localeCompare(b.date as string));
  }, [filteredHistory, retailerByOfferId]);

  function toggleRetailer(retailer: string) {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(retailer)) next.delete(retailer);
      else next.add(retailer);
      return next;
    });
  }

  const formatDate = (value: string) =>
    new Date(value).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit" });

  if (history.length === 0) {
    return <p>Todavía no hay histórico de precios para este producto.</p>;
  }

  return (
    <div>
      <div className="chart-range-toggle">
        {RANGES.map((r) => (
          <button
            key={r.label}
            type="button"
            className={r.label === range.label ? "chart-range-toggle__btn chart-range-toggle__btn--active" : "chart-range-toggle__btn"}
            onClick={() => setRange(r)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {data.length === 0 ? (
        <p className="loading-state" style={{ padding: "2rem 0" }}>
          No hay datos en este rango todavía.
        </p>
      ) : (
        <div style={{ width: "100%", height: 340 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                interval="preserveStartEnd"
                minTickGap={40}
                tick={{ fontSize: 11, fill: "var(--text-faint)" }}
                stroke="var(--chart-axis)"
              />
              <YAxis
                domain={["auto", "auto"]}
                unit="€"
                tick={{ fontSize: 11, fill: "var(--text-faint)" }}
                stroke="var(--chart-axis)"
              />
              <Tooltip
                labelFormatter={formatDate}
                formatter={(value: number, name: string) => [`${value.toFixed(2)} €`, name]}
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 13,
                }}
                labelStyle={{ color: "var(--text-muted)" }}
              />
              {retailers.length > 1 && (
                <Legend
                  onClick={(e) => toggleRetailer(String(e.dataKey))}
                  formatter={(value) => (
                    <span
                      style={{
                        cursor: "pointer",
                        textTransform: "capitalize",
                        textDecoration: hidden.has(value) ? "line-through" : "none",
                        color: hidden.has(value) ? "var(--text-faint)" : "var(--text-muted)",
                      }}
                    >
                      {value}
                    </span>
                  )}
                  wrapperStyle={{ fontSize: 12 }}
                />
              )}
              {retailers.map((retailer, i) => (
                <Line
                  key={retailer}
                  type="monotone"
                  dataKey={retailer}
                  name={retailer}
                  stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                  dot={false}
                  strokeWidth={2}
                  connectNulls
                  hide={hidden.has(retailer)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {retailers.length > 1 && (
        <p className="chart-hint">Haz clic en una tienda de la leyenda para aislar o mostrar su línea.</p>
      )}
    </div>
  );
}
