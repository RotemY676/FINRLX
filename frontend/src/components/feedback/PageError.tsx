interface Props {
  title?: string;
  message: string;
  hint?: string;
}

export function PageError({ title, message, hint }: Props) {
  return (
    <div className="p-qp-6 bg-qp-red-400/10 border border-qp-red-400 rounded-qp">
      <h2 className="text-qp-h2 text-qp-red-600 mb-qp-2">
        {title || "Error"}
      </h2>
      <p className="text-qp-body text-qp-text-secondary">{message}</p>
      {hint && (
        <p className="text-qp-small text-qp-text-muted mt-qp-2">{hint}</p>
      )}
    </div>
  );
}
