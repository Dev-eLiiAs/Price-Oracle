const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Offer {
  id: string;
  product_id: string;
  url: string;
  retailer: string;
  scraper_strategy: string;
  scraped_name: string | null;
  scraped_image_url: string | null;
  status: "active" | "unavailable" | "paused";
  consecutive_failures: number;
  last_scraped_at: string | null;
  created_at: string;
  latest_price: string | null;
}

export interface Product {
  id: string;
  user_id: string;
  canonical_name: string | null;
  image_url: string | null;
  created_at: string;
  offers: Offer[];
  best_price: string | null;
  best_price_retailer: string | null;
}

export interface PricePoint {
  id: number;
  offer_id: string;
  price: string;
  currency: string;
  scraped_at: string;
}

export class DuplicateOfferApiError extends Error {
  productId: string;
  constructor(message: string, productId: string) {
    super(message);
    this.name = "DuplicateOfferApiError";
    this.productId = productId;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 409 && body.detail?.product_id) {
      throw new DuplicateOfferApiError(body.detail.message, body.detail.product_id);
    }
    const detail = typeof body.detail === "string" ? body.detail : undefined;
    throw new Error(detail ?? `Request failed with status ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function listProducts(): Promise<Product[]> {
  return request("/api/v1/products");
}

export function getProduct(id: string): Promise<Product> {
  return request(`/api/v1/products/${id}`);
}

export function getHistory(id: string): Promise<PricePoint[]> {
  return request(`/api/v1/products/${id}/history`);
}

export interface Recommendation {
  verdict: "buy_now" | "good_time" | "wait" | "neutral" | "insufficient_data";
  message: string;
  current_price: string | null;
  historical_min: string | null;
  moving_average_30d: string | null;
  percentile_rank: number | null;
}

export function getRecommendation(id: string): Promise<Recommendation> {
  return request(`/api/v1/products/${id}/recommendation`);
}

export function createProductFromUrl(url: string, productId?: string): Promise<Product> {
  return request("/api/v1/products/from-url", {
    method: "POST",
    body: JSON.stringify({ url, product_id: productId ?? null }),
  });
}

export function deleteProduct(id: string): Promise<void> {
  return request(`/api/v1/products/${id}`, { method: "DELETE" });
}

export interface Alert {
  id: string;
  user_id: string;
  product_id: string;
  threshold_price: string | null;
  threshold_type: string;
  is_active: boolean;
  created_at: string;
}

export function listAlerts(productId: string): Promise<Alert[]> {
  return request(`/api/v1/alerts?product_id=${productId}`);
}

export function createAlert(productId: string, thresholdPrice: string): Promise<Alert> {
  return request("/api/v1/alerts", {
    method: "POST",
    body: JSON.stringify({
      product_id: productId,
      threshold_price: thresholdPrice,
      threshold_type: "fixed_price",
    }),
  });
}

export function deleteAlert(id: string): Promise<void> {
  return request(`/api/v1/alerts/${id}`, { method: "DELETE" });
}
