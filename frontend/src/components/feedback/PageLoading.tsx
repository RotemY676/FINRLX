export function PageLoading({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <div className="flex gap-1.5">
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:150ms]" />
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:300ms]" />
      </div>
      <p className="text-[13px] text-ink-3">{label || "Loading..."}</p>
    </div>
  );
}
