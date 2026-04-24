export function PageLoading({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-qp-3">
      {/* Simple animated dots */}
      <div className="flex gap-1.5">
        <span className="w-2 h-2 rounded-full bg-qp-blue-400 animate-pulse" />
        <span className="w-2 h-2 rounded-full bg-qp-blue-400 animate-pulse [animation-delay:150ms]" />
        <span className="w-2 h-2 rounded-full bg-qp-blue-400 animate-pulse [animation-delay:300ms]" />
      </div>
      <p className="text-qp-body text-qp-text-muted">
        {label || "Loading..."}
      </p>
    </div>
  );
}
