interface Props {
  title: string;
  message: string;
}

export function PageEmpty({ title, message }: Props) {
  return (
    <div className="rounded-lg border border-line bg-surface p-pad text-center py-12">
      <h2 className="text-[15px] font-semibold text-ink-2 mb-1">{title}</h2>
      <p className="text-[13px] text-ink-3">{message}</p>
    </div>
  );
}
