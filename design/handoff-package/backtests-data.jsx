// Backtests — data + chart helpers

// Generate an equity curve: start 100, 36 monthly points, with drift + noise + drawdown regions
function genCurve(seed, drift, vol, ddPoints) {
  const rng = (() => { let s = seed; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; }; })();
  const pts = [{ t: 0, v: 100 }];
  let v = 100;
  for (let i = 1; i <= 36; i++) {
    const shock = (rng() - 0.5) * vol * 4;
    const dd = ddPoints.find(p => i >= p.start && i <= p.end) ? -Math.abs(vol) * 1.2 : 0;
    v = v * (1 + drift / 12 + shock / 100 + dd / 100);
    pts.push({ t: i, v });
  }
  return pts;
}

const BT_RUNS = [
  {
    id: "run-momx3",                                          // primary
    name: "Momentum 3-factor · v2.4",
    strategy: "momentum-3f",
    universe: "US-LargeCap-500",
    start: "2023-01",
    end: "2026-01",
    rebalance: "Weekly",
    costs: "12bp",
    status: "live",
    color: "primary",
    curve: genCurve(7, 0.14, 3.2, [{ start: 8, end: 11 }, { start: 24, end: 26 }]),
    totalReturn: 0.487,
    cagr: 0.153,
    sharpe: 1.42,
    sortino: 2.08,
    maxDD: -0.118,
    winRate: 0.573,
    trades: 284,
  },
  {
    id: "run-valmom",
    name: "Value + Momentum blend",
    strategy: "val-mom-blend",
    universe: "US-LargeCap-500",
    start: "2023-01",
    end: "2026-01",
    rebalance: "Monthly",
    costs: "8bp",
    status: "saved",
    color: "c2",
    curve: genCurve(13, 0.11, 2.4, [{ start: 10, end: 12 }]),
    totalReturn: 0.362,
    cagr: 0.117,
    sharpe: 1.28,
    sortino: 1.74,
    maxDD: -0.083,
    winRate: 0.601,
    trades: 146,
  },
  {
    id: "run-rvn",
    name: "Residual-vol neutralized",
    strategy: "resvol",
    universe: "US-LargeCap-500",
    start: "2023-01",
    end: "2026-01",
    rebalance: "Weekly",
    costs: "14bp",
    status: "saved",
    color: "c3",
    curve: genCurve(22, 0.09, 2.1, []),
    totalReturn: 0.294,
    cagr: 0.097,
    sharpe: 1.52,
    sortino: 2.31,
    maxDD: -0.062,
    winRate: 0.617,
    trades: 312,
  },
];

const BT_BENCH = {
  name: "SPY · Total return",
  curve: genCurve(3, 0.08, 2.0, [{ start: 9, end: 10 }]),
  totalReturn: 0.251,
  cagr: 0.084,
  sharpe: 0.91,
  maxDD: -0.094,
};

// Drawdown series derived from a curve (peak-to-trough running)
function drawdownOf(curve) {
  let peak = curve[0].v;
  return curve.map(p => {
    peak = Math.max(peak, p.v);
    return { t: p.t, dd: (p.v - peak) / peak };
  });
}

// Trades (only for primary run)
const BT_TRADES = [
  { side: "buy",  tk: "NVDA", date: "2025-07-14", held: 42, pnl:  912 },
  { side: "sell", tk: "NVDA", date: "2025-08-25", held: 42, pnl:  912 },
  { side: "buy",  tk: "MSFT", date: "2025-07-21", held: 28, pnl:  344 },
  { side: "sell", tk: "MSFT", date: "2025-08-18", held: 28, pnl:  344 },
  { side: "buy",  tk: "AVGO", date: "2025-08-04", held: 35, pnl: 1127 },
  { side: "sell", tk: "TSLA", date: "2025-08-12", held: 21, pnl: -238 },
  { side: "buy",  tk: "AMD",  date: "2025-08-19", held: 49, pnl:  470 },
  { side: "sell", tk: "AAPL", date: "2025-09-02", held: 35, pnl: -118 },
  { side: "buy",  tk: "ANET", date: "2025-09-15", held: 28, pnl:  615 },
  { side: "buy",  tk: "GOOGL",date: "2025-09-22", held: 14, pnl:  204 },
  { side: "sell", tk: "META", date: "2025-10-06", held: 56, pnl:  887 },
  { side: "buy",  tk: "CRWD", date: "2025-10-20", held: 42, pnl:  393 },
];

Object.assign(window, { BT_RUNS, BT_BENCH, BT_TRADES, drawdownOf });
