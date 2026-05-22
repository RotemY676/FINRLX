/**
 * Phase 15.0 — FINRLX brand mark.
 *
 * A distinctive SVG glyph for the app bar that signals the product
 * domain at a glance. Three ascending bars (decision pipeline stages
 * from raw signal to ranked recommendation) capped with a decision
 * dot in the accent hue. Outer ring is governance / containment.
 *
 * Two-tone via CSS custom properties:
 *   - bars + ring use `currentColor` so the mark inherits text color
 *     (lets the same SVG ship in light + dark + soft + ink contexts)
 *   - decision dot uses `var(--accent-2)` so it stands as the "point
 *     where research becomes a recommendation"
 *
 * Sized via the `size` prop; default 28 px (app-bar scale). Always
 * `aria-hidden` because the wordmark next to it carries the
 * accessible name.
 */
interface BrandMarkProps {
  size?: number;
  className?: string;
}

export function BrandMark({ size = 28, className = "" }: BrandMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      {/* Outer ring — governance / containment.  Stroke-only so the mark
          works on every surface (light, dark, soft) without a background. */}
      <circle
        cx="16"
        cy="16"
        r="14"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="1.5"
      />

      {/* Three ascending bars — the decision pipeline (selection →
          allocation → recommendation). Opacity ramp gives the mark
          forward motion without needing a second color. */}
      <rect x="7.5" y="18" width="3" height="6" rx="0.6" fill="currentColor" opacity="0.45" />
      <rect x="12.5" y="14" width="3" height="10" rx="0.6" fill="currentColor" opacity="0.7" />
      <rect x="17.5" y="9" width="3" height="15" rx="0.6" fill="currentColor" />

      {/* Decision dot — where the pipeline output becomes a published
          recommendation.  Anchored to the top of the tallest bar. */}
      <circle cx="19" cy="6.5" r="1.8" fill="var(--accent-2)" />
    </svg>
  );
}
