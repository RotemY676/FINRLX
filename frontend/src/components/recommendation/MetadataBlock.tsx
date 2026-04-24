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
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
      <h3 className="text-qp-h3 mb-qp-3">Publication Metadata</h3>
      <div className="grid grid-cols-2 gap-qp-3 text-qp-body">
        <div>
          <p className="text-qp-small text-qp-text-muted">Status</p>
          <StatusBadge status={props.status} />
        </div>
        <div>
          <p className="text-qp-small text-qp-text-muted">Published</p>
          <p>{fmt(props.publishedAt)}</p>
        </div>
        <div>
          <p className="text-qp-small text-qp-text-muted">Valid From</p>
          <p>{fmt(props.validFrom)}</p>
        </div>
        <div>
          <p className="text-qp-small text-qp-text-muted">Valid To</p>
          <p>{fmt(props.validTo)}</p>
        </div>
        <div>
          <p className="text-qp-small text-qp-text-muted">Data As Of</p>
          <p>{fmt(props.dataAsOf)}</p>
        </div>
        {props.policyVersionId && (
          <div>
            <p className="text-qp-small text-qp-text-muted">Policy Version</p>
            <p className="font-mono text-qp-small">{props.policyVersionId.slice(0, 8)}...</p>
          </div>
        )}
      </div>
    </div>
  );
}
