// Paper portfolio — data

const PAPER_STRATEGY = {
  id: "paper-momx3",
  name: "Momentum 3-factor · v2.4",
  promotedFrom: "run-momx3",
  promotedAt: "2025-11-20",
  daysLive: 48,
  capitalAllocated: 1_000_000,
  capitalDeployed: 872_400,
  status: "running",            // running | paused | killed
  owner: "Rivka Leibowitz",
  secondApprover: null,          // null until PM signs
};

// Divergence between paper (live) and backtest projection
const PAPER_DIVERGENCE = {
  sharpeBacktest: 1.42,
  sharpeLive: 1.18,
  returnBacktest: 0.061,   // expected +6.1% over 48 days
  returnLive: 0.042,       // actual +4.2%
  slippageModeled: -0.0038, // -38bp annualized
  slippageRealized: -0.0061,// -61bp — worse
  reasons: [
    { k: "Thin mid-caps",       v: "3 names (CRWD, ANET, AVGO) show 2× modeled slippage on exits — liquidity model underweighted these.", severity: "warning" },
    { k: "Earnings volatility", v: "Held MSFT through earnings against rule — +$412 lucky, not repeatable.", severity: "info" },
    { k: "Rebalance timing",    v: "Mon 09:32 open fills bleed to 09:45 VWAP. Avg -7bp.", severity: "warning" },
  ],
  verdict: "Within tolerance but worth fixing before scaling",
};

// Live vs backtest equity curve (48 days, daily)
function genPaperCurve(start, drift, vol, seed) {
  let s = seed;
  const rand = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
  const pts = [{ t: 0, v: start }];
  let v = start;
  for (let i = 1; i <= 48; i++) {
    v = v * (1 + drift / 252 + (rand() - 0.5) * vol / 100);
    pts.push({ t: i, v });
  }
  return pts;
}
const PAPER_LIVE_CURVE     = genPaperCurve(1_000_000, 0.23, 0.85, 17);
const PAPER_BACKTEST_CURVE = genPaperCurve(1_000_000, 0.31, 0.65, 5);
const PAPER_BENCH_CURVE    = genPaperCurve(1_000_000, 0.14, 0.70, 42);

// Open positions — 8 names
const PAPER_POSITIONS = [
  { tk: "NVDA",  sector: "Semis",      side: "LONG", shares: 420, entry: 612.40, mark: 628.15, entered: "2025-12-22", modelMatch: true,  thesis: "momentum-3f cohort A" },
  { tk: "AVGO",  sector: "Semis",      side: "LONG", shares: 180, entry: 1284.30, mark: 1317.80, entered: "2025-12-18", modelMatch: true,  thesis: "momentum-3f cohort A" },
  { tk: "META",  sector: "Comm Svc",   side: "LONG", shares: 240, entry: 584.10, mark: 601.25, entered: "2026-01-02", modelMatch: true,  thesis: "momentum-3f cohort B" },
  { tk: "ANET",  sector: "Networking", side: "LONG", shares: 150, entry: 392.80, mark: 378.40, entered: "2025-12-28", modelMatch: true,  thesis: "momentum-3f cohort B" },
  { tk: "GOOGL", sector: "Comm Svc",   side: "LONG", shares: 380, entry: 192.50, mark: 198.10, entered: "2026-01-05", modelMatch: true,  thesis: "momentum-3f cohort B" },
  { tk: "MSFT",  sector: "Software",   side: "LONG", shares: 210, entry: 418.70, mark: 425.40, entered: "2025-12-15", modelMatch: false, thesis: "held through earnings — deviation" },
  { tk: "CRWD",  sector: "Software",   side: "LONG", shares: 170, entry: 348.20, mark: 339.90, entered: "2026-01-06", modelMatch: true,  thesis: "momentum-3f cohort C" },
  { tk: "AMD",   sector: "Semis",      side: "LONG", shares: 320, entry: 172.40, mark: 169.80, entered: "2026-01-07", modelMatch: true,  thesis: "momentum-3f cohort C" },
];

// Recent fills (last 10)
const PAPER_FILLS = [
  { id: "F-0048", tk: "AMD",   side: "BUY",  qty: 320, px: 172.40, slipBps: -4, at: "2026-01-07 09:32", model: "mkt-open",  ok: true  },
  { id: "F-0047", tk: "CRWD",  side: "BUY",  qty: 170, px: 348.20, slipBps: -12, at: "2026-01-06 09:34", model: "mkt-open", ok: false },
  { id: "F-0046", tk: "GOOGL", side: "BUY",  qty: 380, px: 192.50, slipBps: -3, at: "2026-01-05 09:31", model: "mkt-open",  ok: true  },
  { id: "F-0045", tk: "TSLA",  side: "SELL", qty: 220, px: 244.80, slipBps: -18, at: "2026-01-03 15:48", model: "close-vwap", ok: false },
  { id: "F-0044", tk: "META",  side: "BUY",  qty: 240, px: 584.10, slipBps: -5, at: "2026-01-02 09:33", model: "mkt-open",  ok: true  },
  { id: "F-0043", tk: "AAPL",  side: "SELL", qty: 190, px: 219.40, slipBps: -2, at: "2025-12-30 15:51", model: "close-vwap", ok: true  },
  { id: "F-0042", tk: "ANET",  side: "BUY",  qty: 150, px: 392.80, slipBps: -9, at: "2025-12-28 09:35", model: "mkt-open",  ok: true  },
  { id: "F-0041", tk: "NVDA",  side: "BUY",  qty: 420, px: 612.40, slipBps: -6, at: "2025-12-22 09:32", model: "mkt-open",  ok: true  },
  { id: "F-0040", tk: "AVGO",  side: "BUY",  qty: 180, px: 1284.30, slipBps: -14, at: "2025-12-18 09:33", model: "mkt-open", ok: false },
  { id: "F-0039", tk: "MSFT",  side: "BUY",  qty: 210, px: 418.70, slipBps: -4, at: "2025-12-15 09:34", model: "mkt-open",  ok: true  },
];

Object.assign(window, {
  PAPER_STRATEGY, PAPER_DIVERGENCE,
  PAPER_LIVE_CURVE, PAPER_BACKTEST_CURVE, PAPER_BENCH_CURVE,
  PAPER_POSITIONS, PAPER_FILLS,
});
