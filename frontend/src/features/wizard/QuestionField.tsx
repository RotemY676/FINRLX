"use client";

/**
 * Phase W-3 — wizard input widget (single-choice radio or multi-select).
 *
 * Renders accessible radio-group / checkbox-group with min 44px touch
 * targets per the UX track gates (UX-1.5 sweep + CI lint).
 */
import type { CSSProperties } from "react";

import type { AnswerValue, ProfileQuestion } from "./types";
import { MULTI_SELECT_CODES } from "./types";

interface Props {
  question: ProfileQuestion;
  value: AnswerValue | undefined;
  onChange: (value: AnswerValue) => void;
}

export function QuestionField({ question, value, onChange }: Props) {
  const isMulti = MULTI_SELECT_CODES.has(question.code);

  if (isMulti) {
    const selected = new Set<string>(Array.isArray(value) ? value : []);
    return (
      <fieldset style={fieldStyles.fieldset}>
        <legend style={fieldStyles.legend}>{question.text}</legend>
        {question.helper_text ? (
          <p style={fieldStyles.helper}>{question.helper_text}</p>
        ) : null}
        <div role="group" aria-labelledby={`q-${question.code}-label`}>
          {question.choices.map((c) => {
            const checked = selected.has(c.value);
            return (
              <label key={c.value} style={fieldStyles.choiceRow}>
                <input
                  type="checkbox"
                  name={`q-${question.code}`}
                  value={c.value}
                  checked={checked}
                  onChange={(e) => {
                    const next = new Set(selected);
                    if (e.target.checked) next.add(c.value);
                    else next.delete(c.value);
                    onChange(Array.from(next));
                  }}
                  style={fieldStyles.input}
                />
                <span style={fieldStyles.choiceLabel}>{c.label}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    );
  }

  // single-choice radio
  const singleValue = typeof value === "string" ? value : "";
  return (
    <fieldset style={fieldStyles.fieldset}>
      <legend style={fieldStyles.legend}>{question.text}</legend>
      {question.helper_text ? (
        <p style={fieldStyles.helper}>{question.helper_text}</p>
      ) : null}
      <div role="radiogroup" aria-labelledby={`q-${question.code}-label`}>
        {question.choices.map((c) => {
          const checked = singleValue === c.value;
          return (
            <label key={c.value} style={fieldStyles.choiceRow}>
              <input
                type="radio"
                name={`q-${question.code}`}
                value={c.value}
                checked={checked}
                onChange={() => onChange(c.value)}
                style={fieldStyles.input}
              />
              <span style={fieldStyles.choiceLabel}>{c.label}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

const fieldStyles: Record<string, CSSProperties> = {
  fieldset: {
    border: 0,
    padding: 0,
    margin: "0 0 28px",
  },
  legend: {
    fontSize: 16,
    fontWeight: 600,
    color: "var(--fg, #e9e9ee)",
    marginBottom: 6,
    lineHeight: 1.45,
    padding: 0,
  },
  helper: {
    fontSize: 13,
    color: "var(--fg, #e9e9ee)",
    opacity: 0.65,
    margin: "0 0 12px",
    lineHeight: 1.5,
  },
  choiceRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    padding: "12px 14px",
    marginBottom: 6,
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 10,
    cursor: "pointer",
    minHeight: 44,
    fontSize: 14,
    lineHeight: 1.45,
    color: "var(--fg, #e9e9ee)",
  },
  input: {
    marginTop: 3,
    width: 18,
    height: 18,
    flexShrink: 0,
    accentColor: "var(--accent, #4f9fff)",
  },
  choiceLabel: { flex: 1 },
};
