// Replay workspace — data + chart + timeline components
// Time-travel forensics for a recommendation's lifecycle.

// ===================================================================
// The story: NVDA long, recommended 2026-01-12, horizon 3 months.
// Timeline: 14 days of events from genesis → publish → earnings
// reaction → volatility spike → partial trim → current position.
// ===================================================================

const REPLAY_EVENTS = [
  // t: 0..1 normalized time across the 14-day window
  { t: 0.00, kind: "rescore", label: "Genesis",        when: "Jan 12, 09:32", title: "Momentum engine reaches +0.82" , actor: "system" },
  { t: 0.05, kind: "rescore", label: "Rescore",        when: "Jan 12, 14:10", title: "3 engines confirm long stance",  actor: "system" },
  { t: 0.12, kind: "publish", label: "Published",      when: "Jan 13, 08:15", title: "Published to desk · entry $612.40", actor: "RM" },
  { t: 0.22, kind: "news",    label: "CES keynote",    when: "Jan 15, 18:00", title: "CES demo · positive sentiment score +0.31", actor: "news" },
  { t: 0.34, kind: "news",    label: "Earnings",       when: "Jan 17, 16:05", title: "Q4 earnings beat · guide raised", actor: "news" },
  { t: 0.42, kind: "rescore", label: "Confidence +",   when: "Jan 18, 09:30", title: "Confidence climbs to 0.84", actor: "system" },
  { t: 0.58, kind: "caution", label: "IV spike",       when: "Jan 20, 11:20", title: "Realized vol breaches 2σ band", actor: "system" },
  { t: 0.66, kind: "action",  label: "Trim 30%",       when: "Jan 21, 10:48", title: "Trimmed 30% into strength", actor: "TN" },
  { t: 0.78, kind: "news",    label: "Chip export",    when: "Jan 23, 07:02", title: "Export-control headline · -0.18 sentiment", actor: "news" },
  { t: 0.86, kind: "caution", label: "Data drop",      when: "Jan 24, 04:15", title: "Fundamentals feed stale for 47m", actor: "ops" },
  { t: 1.00, kind: "rescore", label: "Now",            when: "Jan 26, 11:40", title: "Current state — hold remainder", actor: "system" },
];

// Engine state at each event timestamp (for scrub replay).
// Keys: momentum, value, quality, sentiment, macro
const REPLAY_ENGINE_STATES = [
  // 0 — Genesis
  { momentum: { c: 0.82, s: "buy"  }, value:    { c: 0.48, s: "hold" }, quality:   { c: 0.71, s: "buy"  }, sentiment: { c: 0.62, s: "buy"  }, macro:     null },
  // 1 — Rescore
  { momentum: { c: 0.84, s: "buy"  }, value:    { c: 0.50, s: "hold" }, quality:   { c: 0.73, s: "buy"  }, sentiment: { c: 0.66, s: "buy"  }, macro:     { c: 0.55, s: "hold" } },
  // 2 — Published
  { momentum: { c: 0.85, s: "buy"  }, value:    { c: 0.50, s: "hold" }, quality:   { c: 0.74, s: "buy"  }, sentiment: { c: 0.68, s: "buy"  }, macro:     { c: 0.55, s: "hold" } },
  // 3 — CES
  { momentum: { c: 0.86, s: "buy"  }, value:    { c: 0.49, s: "hold" }, quality:   { c: 0.75, s: "buy"  }, sentiment: { c: 0.81, s: "buy"  }, macro:     { c: 0.55, s: "hold" } },
  // 4 — Earnings
  { momentum: { c: 0.87, s: "buy"  }, value:    { c: 0.52, s: "buy"  }, quality:   { c: 0.79, s: "buy"  }, sentiment: { c: 0.84, s: "buy"  }, macro:     { c: 0.57, s: "hold" } },
  // 5 — Confidence +
  { momentum: { c: 0.88, s: "buy"  }, value:    { c: 0.53, s: "buy"  }, quality:   { c: 0.80, s: "buy"  }, sentiment: { c: 0.86, s: "buy"  }, macro:     { c: 0.58, s: "hold" } },
  // 6 — IV spike (momentum still strong but caution rises)
  { momentum: { c: 0.82, s: "buy"  }, value:    { c: 0.50, s: "hold" }, quality:   { c: 0.78, s: "buy"  }, sentiment: { c: 0.72, s: "buy"  }, macro:     { c: 0.52, s: "hold" } },
  // 7 — Trim 30%
  { momentum: { c: 0.78, s: "buy"  }, value:    { c: 0.48, s: "hold" }, quality:   { c: 0.76, s: "buy"  }, sentiment: { c: 0.68, s: "buy"  }, macro:     { c: 0.50, s: "hold" } },
  // 8 — Chip export news
  { momentum: { c: 0.68, s: "buy"  }, value:    { c: 0.46, s: "hold" }, quality:   { c: 0.74, s: "buy"  }, sentiment: { c: 0.44, s: "hold" }, macro:     { c: 0.42, s: "hold" } },
  // 9 — Data drop (quality unavailable)
  { momentum: { c: 0.66, s: "buy"  }, value:    { c: 0.45, s: "hold" }, quality:   null /* feed stale */,       sentiment: { c: 0.42, s: "hold" }, macro:     { c: 0.40, s: "hold" } },
  // 10 — Now
  { momentum: { c: 0.64, s: "hold" }, value:    { c: 0.47, s: "hold" }, quality:   { c: 0.73, s: "buy"  }, sentiment: { c: 0.51, s: "hold" }, macro:     { c: 0.44, s: "hold" } },
];

// Price series sampled across the replay window.
// Paired with position-size history so we can show P&L accrual.
const REPLAY_PRICE = [
  { t: 0.00, p: 608.20, pos: 0   },
  { t: 0.05, p: 611.10, pos: 0   },
  { t: 0.12, p: 612.40, pos: 100 },   // entry
  { t: 0.17, p: 618.90, pos: 100 },
  { t: 0.22, p: 624.10, pos: 100 },   // CES
  { t: 0.28, p: 629.50, pos: 100 },
  { t: 0.34, p: 648.20, pos: 100 },   // earnings gap
  { t: 0.38, p: 652.00, pos: 100 },
  { t: 0.42, p: 655.60, pos: 100 },
  { t: 0.50, p: 662.40, pos: 100 },
  { t: 0.58, p: 671.80, pos: 100 },   // IV spike
  { t: 0.62, p: 668.20, pos: 100 },
  { t: 0.66, p: 672.50, pos: 70  },   // trim 30%
  { t: 0.72, p: 665.40, pos: 70  },
  { t: 0.78, p: 641.20, pos: 70  },   // export headline
  { t: 0.82, p: 638.80, pos: 70  },
  { t: 0.86, p: 642.10, pos: 70  },
  { t: 0.92, p: 647.60, pos: 70  },
  { t: 1.00, p: 651.80, pos: 70  },
];

// ----- helpers ------------------------------------------------------
function interpPrice(t) {
  // Linear interpolation on the REPLAY_PRICE series
  const s = REPLAY_PRICE;
  if (t <= s[0].t) return s[0];
  if (t >= s[s.length - 1].t) return s[s.length - 1];
  for (let i = 1; i < s.length; i++) {
    if (s[i].t >= t) {
      const a = s[i - 1], b = s[i];
      const r = (t - a.t) / (b.t - a.t);
      return { t, p: a.p + (b.p - a.p) * r, pos: a.pos }; // pos is step-wise
    }
  }
  return s[s.length - 1];
}

function eventIndexForT(t) {
  // Find the latest event whose t <= current t
  let idx = 0;
  for (let i = 0; i < REPLAY_EVENTS.length; i++) {
    if (REPLAY_EVENTS[i].t <= t + 1e-6) idx = i;
    else break;
  }
  return idx;
}

function formatPct(delta) {
  if (!isFinite(delta)) return "—";
  const sign = delta > 0 ? "+" : "";
  return sign + (delta * 100).toFixed(1) + "%";
}

Object.assign(window, {
  REPLAY_EVENTS,
  REPLAY_ENGINE_STATES,
  REPLAY_PRICE,
  interpPrice,
  eventIndexForT,
  formatPct,
});
