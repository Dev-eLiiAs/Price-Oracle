export const SUPPORTED_RETAILERS = [
  { name: "Amazon", domains: ["amazon.es", "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr"] },
  { name: "PcComponentes", domains: ["pccomponentes.com"] },
] as const;

/** True for http(s) URLs. Beyond that, the backend accepts any domain — Amazon
 * and PcComponentes get dedicated selectors, other sites fall back to reading
 * their standard Open Graph / schema.org product metadata. */
export function isScrapableUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export const INVALID_URL_MESSAGE = "Eso no parece un enlace válido. Pega la URL completa del producto.";
