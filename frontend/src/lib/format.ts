/**
 * Safe date/time formatting utilities.
 *
 * Uses fixed ISO-like format to avoid SSR/client hydration mismatch
 * caused by toLocaleString() producing different output on server vs browser.
 */

/**
 * Format a date string to a short readable format: "2026-04-24 14:30"
 * Safe for SSR — identical output on server and client.
 */
export function fmtDateTime(d: string | null | undefined): string {
  if (!d) return "—";
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return "—";
    const year = dt.getUTCFullYear();
    const month = String(dt.getUTCMonth() + 1).padStart(2, "0");
    const day = String(dt.getUTCDate()).padStart(2, "0");
    const hours = String(dt.getUTCHours()).padStart(2, "0");
    const mins = String(dt.getUTCMinutes()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${mins}`;
  } catch {
    return "—";
  }
}

/**
 * Format a date string to date only: "2026-04-24"
 */
export function fmtDate(d: string | null | undefined): string {
  if (!d) return "—";
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return "—";
    return dt.toISOString().slice(0, 10);
  } catch {
    return "—";
  }
}

/**
 * Format a date string to time only: "14:30"
 */
export function fmtTime(d: string | null | undefined): string {
  if (!d) return "—";
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return "—";
    const hours = String(dt.getUTCHours()).padStart(2, "0");
    const mins = String(dt.getUTCMinutes()).padStart(2, "0");
    return `${hours}:${mins}`;
  } catch {
    return "—";
  }
}
