interface Props {
  title: string;
  message: string;
}

export function PageEmpty({ title, message }: Props) {
  return (
    <div className="p-qp-6 bg-qp-bg-card border border-qp-border rounded-qp text-center">
      <h2 className="text-qp-h2 text-qp-text-secondary mb-qp-2">{title}</h2>
      <p className="text-qp-body text-qp-text-muted">{message}</p>
    </div>
  );
}
