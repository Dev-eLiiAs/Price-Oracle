"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "@/lib/api";

export default function PriceChart({ history }: { history: PricePoint[] }) {
  if (history.length === 0) {
    return <p>Todavía no hay histórico de precios para este producto.</p>;
  }

  const data = history.map((point) => ({
    date: new Date(point.scraped_at).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "2-digit",
    }),
    price: Number(point.price),
  }));

  return (
    <div style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={["auto", "auto"]} unit="€" />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(2)} €`, "Precio"]}
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
            labelStyle={{ color: "var(--text-muted)" }}
            itemStyle={{ color: "var(--text)" }}
          />
          <Line type="monotone" dataKey="price" stroke="#2563eb" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
