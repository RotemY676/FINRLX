import Link from "next/link";

export function Term({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <Link
      href={`/help/glossary#${id}`}
      className="underline decoration-dotted underline-offset-4 decoration-ink-4 hover:decoration-primary text-ink hover:text-primary transition-colors"
      title={`See definition: ${typeof children === "string" ? children : id}`}
    >
      {children}
    </Link>
  );
}
