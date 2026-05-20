/**
 * Phase UX-5.3 — minimal i18n helper.
 *
 * Loads the en.json strings as a typed object. Components that already
 * inline their strings keep working — adopt `t("auth.sign_in")` incrementally.
 * When a second locale is added (likely he.json for Hebrew first), this
 * helper switches to a runtime locale chooser; the dot-path API is stable.
 */
import strings from "./en.json";

type Strings = typeof strings;

type Path<T, P extends string = ""> = T extends object
  ? {
      [K in keyof T & string]:
        | (P extends "" ? K : `${P}.${K}`)
        | Path<T[K], P extends "" ? K : `${P}.${K}`>;
    }[keyof T & string]
  : never;

export type StringKey = Path<Strings>;

export function t(key: StringKey): string {
  // Resolve the dot path. Unknown keys return the key itself so missing
  // strings are visible in dev rather than silently empty.
  const parts = key.split(".");
  let cur: unknown = strings;
  for (const p of parts) {
    if (cur && typeof cur === "object" && p in cur) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return key;
    }
  }
  return typeof cur === "string" ? cur : key;
}
