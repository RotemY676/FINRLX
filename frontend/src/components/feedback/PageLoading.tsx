import { PageSkeleton } from "./Skeleton";

/**
 * Top-level page loading state. Delegates to PageSkeleton — content-shaped
 * placeholder boxes that approximate the rendered layout — instead of a
 * generic dot animation. The dot pattern stays available as `InlineLoading`
 * below for spinners inside smaller surfaces.
 */
export function PageLoading({ label }: { label?: string }) {
  return <PageSkeleton label={label || "Loading"} />;
}

/**
 * Compact dot-pulse spinner for use inside a card or panel (e.g. when
 * fetching detail in response to a row click). Not appropriate for full
 * page loads — those should use PageLoading / PageSkeleton.
 */
export function InlineLoading({ label }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label || "Loading"}
      className="flex flex-col items-center justify-center h-32 gap-3"
    >
      <div className="flex gap-1.5" aria-hidden="true">
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:150ms]" />
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:300ms]" />
      </div>
      <p className="text-[13px] text-ink-3">{label || "Loading..."}</p>
    </div>
  );
}
