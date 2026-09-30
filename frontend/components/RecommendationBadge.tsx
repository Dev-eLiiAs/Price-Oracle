import type { Recommendation } from "@/lib/api";

const VERDICT_STYLES: Record<Recommendation["verdict"], string> = {
  buy_now: "recommendation-badge--buy",
  good_time: "recommendation-badge--good",
  wait: "recommendation-badge--wait",
  neutral: "recommendation-badge--neutral",
  insufficient_data: "recommendation-badge--neutral",
};

const VERDICT_LABELS: Record<Recommendation["verdict"], string> = {
  buy_now: "Comprar ahora",
  good_time: "Buen momento",
  wait: "Mejor esperar",
  neutral: "Precio habitual",
  insufficient_data: "Sin datos suficientes",
};

export default function RecommendationBadge({ recommendation }: { recommendation: Recommendation }) {
  return (
    <div className={`recommendation-badge ${VERDICT_STYLES[recommendation.verdict]}`}>
      <span className="recommendation-badge__label">
        {VERDICT_LABELS[recommendation.verdict]}
      </span>
      <p className="recommendation-badge__message">{recommendation.message}</p>
    </div>
  );
}
