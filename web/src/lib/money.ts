/**
 * Money as the FOMO relay bills it. The relay keeps its ledger in one currency (`_cny`
 * fields are "ledger units", whatever the relay bills in) and, since the AWS move, says which
 * (`currency`, an ISO code, and `currency_symbol`) on `/v1/me`, the public config and the
 * allowance refusal. Older relays say nothing, and billed in yuan: the default stays `¥`.
 */

const SYMBOLS: Record<string, string> = {
  CNY: "¥",
  RMB: "¥",
  INR: "₹",
  USD: "$",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
};

/** The sign to print: the relay's own symbol when it sent one, else the one for its code, else `¥`. */
export function currencySymbol(code?: string | null, symbol?: string | null): string {
  const s = (symbol ?? "").trim();
  if (s) return s;
  const c = (code ?? "").trim().toUpperCase();
  return SYMBOLS[c] ?? "¥";
}

/** `fmtMoney(1.2, "₹")` → "₹1.20"; `fmtMoney(10, "¥", 0)` → "¥10". */
export function fmtMoney(n: number, symbol: string, digits = 2): string {
  return `${symbol}${(Number.isFinite(n) ? n : 0).toFixed(digits)}`;
}

/** The symbol from any relay object that carries the two fields (spend, public config, refusal info). */
export function symbolOf(o?: { currency?: string | null; currency_symbol?: string | null } | null): string {
  return currencySymbol(o?.currency, o?.currency_symbol);
}
