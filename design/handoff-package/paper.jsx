// Paper portfolio — UI components

const { useState: useStatePp, useMemo: useMemoPp } = React;

const fmt$ = (n) => "$" + Math.round(n).toLocaleString();
const fmtPctPp = (n, d = 2) => (n >= 0 ? "+" : "") + (n * 100).toFixed(d) + "%";

// ========== Strategy bar ==========
const PaperBar = ({ strat }) => (
  <div className="pp-bar">
    <div className="pp-bar-left">
      <h1 className="pp-bar-title">
        {strat.name}
        <span className="status"><span className="dot" /> paper · {strat.status}</span>
      </h1>
      <div className="pp-bar-meta">
        <span>day <b>{strat.daysLive}</b></span>
        <span className="pipe">·</span>
        <span>capital <b>{fmt$(strat.capitalAllocated)}</b></span>
        <span className="pipe">·</span>
        <span>deployed <b>{((strat.capitalDeployed / strat.capitalAllocated) * 100).toFixed(0)}%</b></span>
        <span className="pipe">·</span>
        <span>owner <b>{strat.owner}</b></span>
      </div>
    </div>
    <div className="pp-bar-actions">
      <button className="btn ghost sm"><Icon name="history" size={12}/> Back to backtest</button>
      <button className="btn ghost sm"><Icon name="external" size={12}/> Export report</button>
      <button className="btn ghost sm">Pause</button>
    </div>
  </div>
);

// ========== Divergence banner ==========
const DivergenceBanner = ({ d }) => {
  const metrics = [
    { lbl: "Sharpe",        bt: d.sharpeBacktest.toFixed(2),       live: d.sharpeLive.toFixed(2),
      delta: "-0.24",       tone: "warn" },
    { lbl: "Return (48d)",  bt: fmtPctPp(d.returnBacktest, 1),     live: fmtPctPp(d.returnLive, 1),
      delta: "-1.9 pts",    tone: "warn" },
    { lbl: "Slippage (ann)",bt: (d.slippageModeled * 10000).toFixed(0) + "bp",
      live: (d.slippageRealized * 10000).toFixed(0) + "bp",
      delta: "-23bp",       tone: "neg" },
    { lbl: "Hit rate (same dir)", bt: "57.3%", live: "54.1%",
      delta: "-3.2 pts",    tone: "warn" },
  ];
  return (
    <div className="pp-div">
      <div>
        <div className="pp-div-head">
          <Icon name="alert-triangle" size={14} style={{color:"var(--caution)"}} />
          <h3 className="pp-div-title">Live vs backtest divergence</h3>
          <span className="pp-div-verdict">{d.verdict}</span>
        </div>
        <div className="pp-div-grid">
          {metrics.map(m => (
            <div key={m.lbl} className="pp-div-metric">
              <div className="lbl">{m.lbl}</div>
              <div className="row">
                <span className="bt">{m.bt}</span>
                <span className={"live " + m.tone}>{m.live}</span>
              </div>
              <div className="delta">{m.delta} vs model</div>
            </div>
          ))}
        </div>
      </div>
      <div className="pp-div-actions">
        <button className="btn ghost sm">Open replay</button>
        <button className="btn ghost sm">File for review</button>
      </div>
      <div className="pp-div-reasons">
        {d.reasons.map((r, i) => (
          <div key={i} className={"pp-div-reason " + r.severity}>
            <div className="bullet" />
            <div>
              <span className="k">{r.k}</span>
              {r.v}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ========== Hero KPIs ==========
const PaperKpis = () => {
  const live = PAPER_LIVE_CURVE[PAPER_LIVE_CURVE.length - 1].v;
  const start = PAPER_LIVE_CURVE[0].v;
  const pnl$ = live - start;
  const pnlPct = (live - start) / start;
  const bench = PAPER_BENCH_CURVE[PAPER_BENCH_CURVE.length - 1].v;
  const benchPct = (bench - start) / start;
  const kpis = [
    { lbl: "Live P&L", val: fmt$(pnl$), tone: pnl$ >= 0 ? "pos" : "neg",
      sub: fmtPctPp(pnlPct, 2) + " since promote" },
    { lbl: "vs SPY",   val: fmtPctPp(pnlPct - benchPct, 1), tone: (pnlPct - benchPct) >= 0 ? "pos" : "neg",
      sub: "bench " + fmtPctPp(benchPct, 1) },
    { lbl: "Sharpe (live)", val: "1.18", sub: "backtest 1.42" },
    { lbl: "Max DD",   val: "-2.8%",   tone: "neg", sub: "on day 31" },
    { lbl: "Slippage realized", val: "-61bp", tone: "neg", sub: "modeled -38bp" },
  ];
  return (
    <div className="pp-kpis">
      {kpis.map(k => (
        <div key={k.lbl} className="pp-kpi">
          <div className="lbl">{k.lbl}</div>
          <div className={"val " + (k.tone || "")}>{k.val}</div>
          <div className="sub">{k.sub}</div>
        </div>
      ))}
    </div>
  );
};

// ========== Equity curve chart ==========
const PaperChart = () => {
  const w = 820, h = 220, pad = { t: 12, r: 16, b: 22, l: 56 };
  const all = [...PAPER_LIVE_CURVE, ...PAPER_BACKTEST_CURVE, ...PAPER_BENCH_CURVE];
  const vMin = Math.min(...all.map(p => p.v)) - 5000;
  const vMax = Math.max(...all.map(p => p.v)) + 5000;
  const tMax = 48;

  const x = t => pad.l + (t / tMax) * (w - pad.l - pad.r);
  const y = v => pad.t + (1 - (v - vMin) / (vMax - vMin)) * (h - pad.t - pad.b);
  const toPath = curve => curve.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");

  // Gap fill between backtest (upper) and live (lower)
  const gapPath =
    PAPER_BACKTEST_CURVE.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ") +
    " " +
    [...PAPER_LIVE_CURVE].reverse().map(p => `L${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ") + " Z";

  const grids = [1_000_000, 1_020_000, 1_040_000, 1_060_000];
  const ticks = [0, 12, 24, 36, 48];
  const labels = ["Nov 20", "Dec 2", "Dec 14", "Dec 26", "Jan 7"];

  return (
    <svg className="pp-chart-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {grids.map(gv => gv >= vMin && gv <= vMax && (
        <g key={gv}>
          <line x1={pad.l} x2={w - pad.r} y1={y(gv)} y2={y(gv)} className="pp-grid" />
          <text x={pad.l - 6} y={y(gv) + 3} textAnchor="end" className="pp-axis">
            ${(gv / 1000).toFixed(0)}k
          </text>
        </g>
      ))}
      {ticks.map((t, i) => (
        <text key={t} x={x(t)} y={h - 6} textAnchor="middle" className="pp-axis">{labels[i]}</text>
      ))}
      <path d={gapPath} className="pp-area-gap" />
      <path d={toPath(PAPER_BENCH_CURVE)}    className="pp-line-bench" />
      <path d={toPath(PAPER_BACKTEST_CURVE)} className="pp-line-bt" />
      <path d={toPath(PAPER_LIVE_CURVE)}     className="pp-line-live" />

      {/* End-of-line dot */}
      <circle cx={x(tMax)} cy={y(PAPER_LIVE_CURVE[PAPER_LIVE_CURVE.length - 1].v)} r={3.5} fill="var(--primary)" />
    </svg>
  );
};

const PaperChartCard = () => (
  <div className="pp-chart-card">
    <div className="pp-chart-head">
      <div className="pp-chart-title">Equity · live vs backtest projection</div>
      <div className="pp-chart-legend">
        <span className="lg"><span className="sw" style={{background:"var(--primary)"}}/> <b>Live</b></span>
        <span className="lg"><span className="sw" style={{background:"var(--ink-3)"}}/> Backtest projection</span>
        <span className="lg"><span className="sw" style={{background:"var(--ink-4)"}}/> SPY</span>
        <span className="lg"><span className="sw" style={{background:"var(--caution-soft)", height:6}}/> gap</span>
      </div>
    </div>
    <PaperChart />
  </div>
);

// ========== Positions table ==========
const PositionsTable = () => (
  <div className="pp-positions-card">
    <div className="pp-section-head">
      <h3 className="pp-section-title">Open positions</h3>
      <span className="pp-section-count">{PAPER_POSITIONS.length} names · $872,400 deployed</span>
    </div>
    <table className="pp-pos-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Side</th>
          <th className="num">Shares</th>
          <th className="num">Entry</th>
          <th className="num">Mark</th>
          <th className="num">P&amp;L $</th>
          <th className="num">P&amp;L %</th>
          <th>Model</th>
        </tr>
      </thead>
      <tbody>
        {PAPER_POSITIONS.map(p => {
          const pnl$ = (p.mark - p.entry) * p.shares * (p.side === "LONG" ? 1 : -1);
          const pnlPct = ((p.mark - p.entry) / p.entry) * (p.side === "LONG" ? 1 : -1);
          return (
            <tr key={p.tk}>
              <td>
                <div className="pp-pos-tk">{p.tk}</div>
                <div className="pp-pos-sector">{p.sector}</div>
              </td>
              <td><span className={"pp-pos-side " + p.side}>{p.side}</span></td>
              <td className="num">{p.shares}</td>
              <td className="num">${p.entry.toFixed(2)}</td>
              <td className="num">${p.mark.toFixed(2)}</td>
              <td className={"num pp-pos-pnl " + (pnl$ >= 0 ? "pos" : "neg")}>
                {pnl$ >= 0 ? "+" : ""}${Math.round(pnl$).toLocaleString()}
              </td>
              <td className={"num pp-pos-pnl " + (pnlPct >= 0 ? "pos" : "neg")}>
                {fmtPctPp(pnlPct, 2)}
              </td>
              <td>
                {p.modelMatch
                  ? <span className="pp-pos-match">match</span>
                  : <span className="pp-pos-deviation"><Icon name="alert-triangle" size={10}/> deviation</span>}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
);

// ========== Sector exposure ==========
const ExposureCard = () => {
  const agg = {};
  let total = 0;
  PAPER_POSITIONS.forEach(p => {
    const v = p.shares * p.mark;
    agg[p.sector] = (agg[p.sector] || 0) + v;
    total += v;
  });
  const colors = {
    "Semis": "var(--primary)",
    "Comm Svc": "var(--accent)",
    "Software": "var(--accent-2)",
    "Networking": "var(--caution)",
  };
  const segs = Object.entries(agg).map(([k, v]) => ({ k, v, pct: v / total, color: colors[k] || "var(--ink-4)" }));
  segs.sort((a, b) => b.v - a.v);
  return (
    <div className="pp-expo-card">
      <div className="pp-section-head">
        <h3 className="pp-section-title" style={{fontSize:14}}>Sector exposure</h3>
        <span className="pp-section-count">Semis 42% (limit 30% · breach)</span>
      </div>
      <div className="pp-expo-bar">
        {segs.map(s => <div key={s.k} className="pp-expo-seg" style={{width: (s.pct * 100) + "%", background: s.color}} />)}
      </div>
      <div className="pp-expo-legend">
        {segs.map(s => (
          <div key={s.k} className="lg">
            <span className="sw" style={{background: s.color}} />
            {s.k}
            <span className="pct">{(s.pct * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ========== Fills side ==========
const FillsPanel = () => (
  <div className="pp-fills-card">
    <div className="pp-section-head">
      <h3 className="pp-section-title" style={{fontSize:14}}>Recent fills</h3>
      <span className="pp-section-count">10 of 48</span>
    </div>
    {PAPER_FILLS.map(f => (
      <div key={f.id} className="pp-fill">
        <span className={"pp-fill-side " + f.side}>{f.side}</span>
        <div className="pp-fill-body">
          <div className="pp-fill-tk">{f.tk} <span style={{color:"var(--ink-3)", fontWeight:400}}>× {f.qty}</span></div>
          <div className="pp-fill-meta">${f.px.toFixed(2)} · {f.at}</div>
        </div>
        <div className={"pp-fill-slip " + (f.ok ? "ok" : "warn")}>
          {f.slipBps}bp
          <div className="model">{f.model}</div>
        </div>
      </div>
    ))}
  </div>
);

// ========== Promote footer ==========
const PromoteFooter = ({ strat }) => (
  <div className="pp-promote">
    <div className="pp-promote-lbl">Promote to production</div>
    <div className="pp-promote-gate">
      <div className="req">
        <div className="ok">✓</div>
        <div className="k">paper age ≥ 30d</div>
        <b>48d</b>
      </div>
      <div className="req">
        <div className="ok">✓</div>
        <div className="k">max DD respected</div>
        <b>-2.8% / -8%</b>
      </div>
      <div className="req">
        <div className="wait" />
        <div className="k">PM sign-off</div>
        <b>pending</b>
      </div>
      <div className="req">
        <div className="wait" />
        <div className="k">deviation ack</div>
        <b>3 items open</b>
      </div>
    </div>
    <div className="pp-promote-actions">
      <button className="btn ghost sm">Kill strategy</button>
      <button className="btn primary sm" disabled style={{opacity:0.55, cursor:"not-allowed"}}>
        <Icon name="decision" size={12}/> Request promote
      </button>
    </div>
  </div>
);

Object.assign(window, {
  PaperBar, DivergenceBanner, PaperKpis, PaperChartCard,
  PositionsTable, ExposureCard, FillsPanel, PromoteFooter,
});
