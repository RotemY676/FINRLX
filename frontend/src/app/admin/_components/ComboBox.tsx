"use client";

import { useState, useRef, useEffect } from "react";

interface ComboBoxProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  title?: string;
  className?: string;
  allowCustom?: boolean;
  customLabel?: string;
}

/**
 * ComboBox — A select dropdown with predefined options + optional custom input.
 * When "Custom..." is selected, shows a text input for free-form entry.
 */
export function ComboBox({
  value,
  onChange,
  options,
  placeholder,
  title,
  className = "",
  allowCustom = true,
  customLabel = "Custom...",
}: ComboBoxProps) {
  const isCustom = value !== "" && !options.some(o => o.value === value);
  const [showCustom, setShowCustom] = useState(isCustom);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showCustom && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showCustom]);

  const baseClass = `w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none ${className}`;

  if (showCustom && allowCustom) {
    return (
      <div className="flex gap-1.5">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          title={title}
          className={`flex-1 ${baseClass}`}
        />
        <button
          type="button"
          onClick={() => {
            setShowCustom(false);
            if (options.length > 0) onChange(options[0].value);
          }}
          className="px-2 py-1 rounded-md bg-surface-2 text-ink-3 text-[10px] hover:bg-surface-3 transition-colors shrink-0"
          title="Switch back to preset options"
        >
          Presets
        </button>
      </div>
    );
  }

  return (
    <select
      value={options.some(o => o.value === value) ? value : "__custom__"}
      onChange={e => {
        if (e.target.value === "__custom__") {
          setShowCustom(true);
          onChange("");
        } else {
          onChange(e.target.value);
        }
      }}
      title={title}
      className={baseClass}
    >
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
      {allowCustom && <option value="__custom__">{customLabel}</option>}
    </select>
  );
}
