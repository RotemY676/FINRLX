import { ReactNode } from "react";

interface StageCardProps {
  title: string;
  subtitle?: string;
  available: boolean;
  children: ReactNode;
}

export function StageCard({ title, subtitle, available, children }: StageCardProps) {
  return (
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
      <div className="flex items-center justify-between mb-qp-3">
        <div>
          <h3 className="text-qp-h3">{title}</h3>
          {subtitle && <p className="text-qp-small text-qp-text-muted">{subtitle}</p>}
        </div>
        <span className={`w-2 h-2 rounded-full ${available ? "bg-qp-green-500" : "bg-qp-border"}`} />
      </div>
      {available ? children : (
        <p className="text-qp-body text-qp-text-muted">Stage data not available.</p>
      )}
    </div>
  );
}
