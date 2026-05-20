/**
 * Skeleton primitives.
 *
 * Use these to render the shape of content while it's loading, rather than the
 * generic three-dot PageLoading. Skeletons should approximate the rendered
 * layout — a list of cards, a table of rows, a chart frame — so the layout
 * doesn't jump when real data arrives.
 *
 * All skeletons:
 *  - respect prefers-reduced-motion globally (handled in globals.css)
 *  - carry no aria role themselves — the wrapping `<PageSkeleton>` or page
 *    component should announce a single `role="status" aria-live="polite"`
 *    so AT users get one polite "Loading X..." instead of dozens of
 *    "loading" announcements per element.
 */
export function SkeletonBox({ className = "", style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      aria-hidden="true"
      className={`bg-surface-3 rounded-md animate-pulse ${className}`}
      style={style}
    />
  );
}

export function SkeletonText({ width = "w-full", className = "" }: { width?: string; className?: string }) {
  return <SkeletonBox className={`h-3 ${width} ${className}`} />;
}

export function SkeletonHeading({ className = "" }: { className?: string }) {
  return <SkeletonBox className={`h-5 w-2/3 ${className}`} />;
}

/**
 * A full-page loading state shaped roughly like a typical FINRLX page:
 * heading + sub + a few cards.
 *
 * Carries one `role="status"` + an aria-label so a screen reader announces
 * "Loading $label" once on mount, not per-skeleton.
 */
export function PageSkeleton({ label = "Loading" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label}
      className="space-y-gap max-w-[1200px]"
    >
      {/* Heading */}
      <div className="space-y-2">
        <SkeletonBox className="h-6 w-48" />
        <SkeletonBox className="h-3 w-64" />
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-gap">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-line bg-surface p-3 shadow-sm space-y-2">
            <SkeletonBox className="h-3 w-2/3" />
            <SkeletonBox className="h-6 w-1/2" />
            <SkeletonBox className="h-2.5 w-3/4" />
          </div>
        ))}
      </div>

      {/* Hero card */}
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm space-y-3">
        <SkeletonHeading />
        <SkeletonText />
        <SkeletonText width="w-5/6" />
        <SkeletonText width="w-3/4" />
      </div>

      {/* Two-up cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        {[0, 1].map((i) => (
          <div key={i} className="rounded-lg border border-line bg-surface p-pad shadow-sm space-y-3">
            <SkeletonBox className="h-4 w-1/3" />
            <SkeletonBox className="h-32 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
