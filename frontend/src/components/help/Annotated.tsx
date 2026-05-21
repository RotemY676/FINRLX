import Image from "next/image";

export interface AnnotatedCallout {
  /** Percentage from the left edge of the image (0–100). */
  x: number;
  /** Percentage from the top edge of the image (0–100). */
  y: number;
  /** 1-indexed marker number shown on the image and in the legend. */
  n: number;
  /** What this marker points at — read by screen readers via the legend. */
  label: string;
}

/**
 * Annotated screenshot with numbered SVG callouts and an <ol> legend.
 *
 * Annotations are overlaid via SVG (not baked into the PNG) so re-capturing
 * the screenshot during Playwright drift checks does not invalidate the
 * legend. Each numbered circle is keyed to an <li> in the legend, which is
 * exposed to screen readers via `aria-describedby`.
 *
 * @example
 * <Annotated
 *   src="/help/screenshots/policies/cash-floor.png"
 *   alt="Policies page showing the cash floor control"
 *   width={1440}
 *   height={900}
 *   callouts={[
 *     { x: 22, y: 38, n: 1, label: "Cash floor slider — minimum % of portfolio kept in cash." },
 *     { x: 64, y: 38, n: 2, label: "Current effective value — applied to live recommendations." },
 *   ]}
 * />
 */
export function Annotated({
  src,
  alt,
  width,
  height,
  callouts = [],
  caption,
  unoptimized = true,
}: {
  src: string;
  alt: string;
  width: number;
  height: number;
  callouts?: AnnotatedCallout[];
  caption?: string;
  unoptimized?: boolean;
}) {
  const legendId = `legend-${src.replace(/[^a-z0-9]/gi, "-")}`;

  return (
    <figure className="my-6">
      <div className="relative rounded-lg overflow-hidden ring-1 ring-line bg-surface-2">
        <Image
          src={src}
          alt={alt}
          width={width}
          height={height}
          className="block w-full h-auto"
          aria-describedby={callouts.length > 0 ? legendId : undefined}
          unoptimized={unoptimized}
        />
        {callouts.length > 0 && (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="absolute inset-0 w-full h-full pointer-events-none"
            role="presentation"
            aria-hidden="true"
          >
            {callouts.map((c) => {
              const cx = (c.x / 100) * width;
              const cy = (c.y / 100) * height;
              const r = Math.max(14, Math.min(width, height) * 0.018);
              return (
                <g key={c.n}>
                  <circle cx={cx} cy={cy} r={r + 2} fill="white" />
                  <circle cx={cx} cy={cy} r={r} fill="oklch(0.58 0.18 25)" />
                  <text
                    x={cx}
                    y={cy}
                    fontSize={r * 1.2}
                    fontWeight={700}
                    fill="white"
                    fontFamily="var(--font-sans), system-ui, sans-serif"
                    textAnchor="middle"
                    dominantBaseline="central"
                  >
                    {c.n}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
      <figcaption className="mt-3 text-[13px] text-ink-2">
        {caption && <p className="mb-2">{caption}</p>}
        {callouts.length > 0 && (
          <ol id={legendId} className="space-y-1 list-none m-0 p-0">
            {callouts.map((c) => (
              <li key={c.n} className="flex items-start gap-2">
                <span
                  className="inline-flex items-center justify-center shrink-0 mt-0.5 w-5 h-5 rounded-full bg-breach text-white text-[11px] font-bold"
                  aria-hidden="true"
                >
                  {c.n}
                </span>
                <span className="flex-1">{c.label}</span>
              </li>
            ))}
          </ol>
        )}
      </figcaption>
    </figure>
  );
}
