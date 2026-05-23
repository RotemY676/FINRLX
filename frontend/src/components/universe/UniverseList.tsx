import { UniverseListItem } from "@/services/api";

interface UniverseListProps {
  universes: UniverseListItem[];
  selectedId: string | null;
  onSelect: (universeId: string) => void;
}

export function UniverseList({ universes, selectedId, onSelect }: UniverseListProps) {
  if (universes.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-2">Universes</h3>
        <p className="text-[12.5px] text-ink-3">No universes configured.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <h3 className="text-[13px] font-semibold text-ink mb-3">Universes</h3>
      <div className="space-y-1">
        {universes.map((u) => {
          const isSelected = u.universe_id === selectedId;
          return (
            <button
              key={u.universe_id}
              type="button"
              onClick={() => onSelect(u.universe_id)}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors border-l-2 ${
                isSelected
                  ? "bg-surface-2 border-primary text-ink"
                  : "border-transparent text-ink-2 hover:bg-surface-3"
              }`}
              aria-pressed={isSelected}
            >
              <div className="flex items-center justify-between gap-2">
                <span className={`text-[13px] truncate ${isSelected ? "font-medium" : ""}`}>
                  {u.name}
                </span>
                <span className="text-[11px] font-mono text-ink-3">{u.asset_count}</span>
              </div>
              {u.description && (
                <p className="text-[11px] text-ink-3 mt-0.5 truncate">{u.description}</p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
