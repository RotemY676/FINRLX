import { StatusBadge } from "./StatusBadge";

interface MetadataProps {
  status: string;
  publishedAt: string | null;
  validFrom: string | null;
  validTo: string | null;
  dataAsOf: string | null;
  policyVersionId: string | null;
}

function fmt(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleString();
}

export function MetadataBlock(props: MetadataProps) {
  return (
    <div className="rounded-lg border border-line bg-surface p-pad">
      <h3 className="text-[13px] font-semibold text-ink mb-3">Publication Metadata</h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-[12.5px]">
        <div>
          <p className="text-[11px] text-ink-4 mb-0.5">Status</p>
          <StatusBadge status={props.status} />
        </div>
        <div>
          <p className="text-[11px] text-ink-4 mb-0.5">Published</p>
          <p className="text-ink-2">{fmt(props.publishedAt)}</p>
        </div>
        <div>
          <p className="text-[11px] text-ink-4 mb-0.5">Valid From</p>
          <p className="text-ink-2">{fmt(props.validFrom)}</p>
        </div>
        <div>
          <p className="text-[11px] text-ink-4 mb-0.5">Valid To</p>
          <p className="text-ink-2">{fmt(props.validTo)}</p>
        </div>
        <div>
          <p className="text-[11px] text-ink-4 mb-0.5">Data As Of</p>
          <p className="text-ink-2">{fmt(props.dataAsOf)}</p>
        </div>
        {props.policyVersionId && (
          <div>
            <p className="text-[11px] text-ink-4 mb-0.5">Policy Version</p>
            <p className="font-mono text-[11px] text-ink-3">{props.policyVersionId.slice(0, 8)}…</p>
          </div>
        )}
      </div>
    </div>
  );
}
