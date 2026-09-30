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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
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

export function createProductFromUrl(url: string, productId?: string): Promise<Product> {
  return request("/api/v1/products/from-url", {
    method: "POST",
    body: JSON.stringify({ url, product_id: productId ?? null }),
  });
}

export function deleteProduct(id: string): Promise<void> {
  return request(`/api/v1/products/${id}`, { method: "DELETE" });
}
