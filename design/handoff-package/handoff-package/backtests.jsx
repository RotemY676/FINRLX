// Backtests workspace — UI components
// Consumes: BT_RUNS, BT_BENCH, BT_TRADES, drawdownOf

const { useState: useStateBt, useMemo: useMemoBt } = React;

// ========== Equity curve + benchmark SVG ==========
const EquityChart = ({ runs, showBench = true }) => {
  const w = 820, h = 240, pad = { t: 12, r: 16, b: 22, l: 40 };
  const all = [...runs.flatMap(r => r.curve), ...(showBench ? BT_BENCH.curve : [])];
  const vMin = Math.min(...all.map(p => p.v)) - 2;
  const vMax = Math.max(...all.map(p => p.v)) + 2;
  const tMax = 36;

  const x = t => pad.l + (t / tMax) * (w - pad.l - pad.r);
  const y = v => pad.t + (1 - (v - vMin) / (vMax - vMin)) * (h - pad.t - pad.b);

  const toPath = curve => curve.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");

  // Horizontal gridlines at 100, 125, 150
  const grids = [100, 120, 140];
  // Month labels: every 6 months
  const ticks = [0, 6, 12, 18, 24, 30, 36];
  const monthLabels = ["'23 Q1", "'23 Q3", "'24 Q1", "'24 Q3", "'25 Q1", "'25 Q3", "'26 Q1"];

  const primary = runs.find(r => r.color === "primary");
  const primaryAreaPath = primary
    ? toPath(primary.curve) + ` L${x(tMax).toFixed(1)},${y(vMin).toFixed(1)} L${x(0).toFixed(1)},${y(vMin).toFixed(1)} Z`
    : null;

  return (
    <svg className="bt-chart-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {/* Gridlines */}
      {grids.map(gv => gv >= vMin && gv <= vMax && (
        <g key={gv}>
          <line x1={pad.l} x2={w - pad.r} y1={y(gv)} y2={y(gv)} className="bt-grid-line" />
          <text x={pad.l - 6} y={y(gv) + 3} textAnchor="end" className="bt-axis-text">{gv}</text>
        </g>
      ))}
      {/* X ticks */}
      {ticks.map((tv, i) => (
        <text key={tv} x={x(tv)} y={h - 6} textAnchor="middle" className="bt-axis-text">{monthLabels[i]}</text>
      ))}

      {/* Primary area */}
      {primary && <path d={primaryAreaPath} className="bt-area-primary" />}

      {/* Bench dashed */}
      {showBench && <path d={toPath(BT_BENCH.curve)} className="bt-line-bench" />}

      {/* Other runs */}
      {runs.filter(r => r.color !== "primary").map(r => (
        <path key={r.id} d={toPath(r.curve)} className={`bt-line-${r.color}`} />
      ))}

      {/* Primary on top */}
      {primary && <path d={toPath(primary.curve)} className="bt-line-primary" />}

      {/* End markers */}
      {runs.map(r => {
        const end = r.curve[r.curve.length - 1];
        return <circle key={r.id} cx={x(end.t)} cy={y(end.v)} r={3.5}
          fill={`var(--${r.color === "primary" ? "primary" : r.color === "c2" ? "accent" : "accent-2"})`} />;
      })}
    </svg>
  );
};

// ========== Drawdown strip ==========
const DrawdownStrip = ({ run }) => {
  const w = 820, h = 90, pad = { t: 8, r: 16, b: 18, l: 40 };
  const dd = drawdownOf(run.curve);
  const ddMin = Math.min(...dd.map(d => d.dd));   // most negative
  const tMax = 36;

  const x = t => pad.l + (t / tMax) * (w - pad.l - pad.r);
  const y = v => pad.t + (v / ddMin) * (h - pad.t - pad.b);  // 0 at top, ddMin at bottom

  const line = dd.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.dd).toFixed(1)}`).join(" ");
  const area = line + ` L${x(tMax).toFixed(1)},${pad.t} L${x(0).toFixed(1)},${pad.t} Z`;

  const grids = [0, ddMin / 2, ddMin];
  const ticks = [0, 12, 24, 36];
  const monthLabels = ["'23", "'24", "'25", "'26"];

  return (
    <svg className="bt-chart-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {grids.map((gv, i) => (
        <g key={i}>
          <line x1={pad.l} x2={w - pad.r} y1={y(gv)} y2={y(gv)} className="bt-grid-line" />
          <text x={pad.l - 6} y={y(gv) + 3} textAnchor="end" className="bt-axis-text">
            {(gv * 100).toFixed(0)}%
          </text>
        </g>
      ))}
      {ticks.map((tv, i) => (
        <text key={tv} x={x(tv)} y={h - 4} textAnchor="middle" className="bt-axis-text">{monthLabels[i]}</text>
      ))}
      <path d={area} className="bt-dd-fill" />
      <path d={line} className="bt-dd-line" />
    </svg>
  );
};

// ========== Strategy bar ==========
const StrategyBar = ({ run }) => (
  <div className="bt-bar">
    <div className="bt-bar-left">
      <h1 className="bt-bar-title">
        {run.name}
        <span className="status"><span className="dot" /> {run.status}</span>
      </h1>
      <div className="bt-bar-meta">
        <span><b>{run.universe}</b></span>
        <span className="pipe">·</span>
        <span>{run.start} → {run.end}</span>
        <span className="pipe">·</span>
        <span><b>{run.trades}</b> trades</span>
      </div>
    </div>
    <div className="bt-params">
      <div className="bt-param"><span className="lbl">rebal</span><span className="val">{run.rebalance}</span></div>
      <div className="bt-param"><span className="lbl">costs</span><span className="val">{run.costs}</span></div>
      <div className="bt-param"><span className="lbl">bench</span><span className="val">SPY</span></div>
      <button className="btn ghost sm" style={{ marginLeft: 4 }}>Edit config</button>
      <button className="btn primary sm"><Icon name="history" size={12}/> Re-run</button>
    </div>
  </div>
);

// ========== Left: saved runs list ==========
const RunsList = ({ active, onSelect }) => (
  <aside className="bt-runs">
    <div className="bt-runs-head">
      <div className="t">Recent runs</div>
      <div className="c">12</div>
    </div>
    {BT_RUNS.map(r => (
      <div key={r.id} className={"bt-run" + (r.id === active ? " active" : "")} onClick={() => onSelect(r.id)}>
        <div className={"bt-run-dot " + r.color} />
        <div className="bt-run-body">
          <div className="bt-run-name">{r.name}</div>
          <div className="bt-run-sub">{r.rebalance} · {r.costs}</div>
        </div>
        <div className={"bt-run-return " + (r.totalReturn >= 0 ? "pos" : "neg")}>
          {r.totalReturn >= 0 ? "+" : ""}{(r.totalReturn * 100).toFixed(1)}%
        </div>
      </div>
    ))}
    <div className="bt-runs-group-label">Archived</div>
    {[
      { name: "Quality + Low-vol", sub: "Monthly · 10bp", ret: 0.213 },
      { name: "Mean-reversion 5d",  sub: "Daily · 18bp", ret: 0.088 },
      { name: "Value tilt (deep)",  sub: "Quarterly · 6bp", ret: -0.031 },
      { name: "Sector rotation",    sub: "Monthly · 9bp", ret: 0.162 },
      { name: "Earnings drift",     sub: "Event · 22bp", ret: 0.104 },
    ].map((r, i) => (
      <div key={i} className="bt-run">
        <div className="bt-run-dot" />
        <div className="bt-run-body">
          <div className="bt-run-name" style={{ color: "var(--ink-2)" }}>{r.name}</div>
          <div className="bt-run-sub">{r.sub}</div>
        </div>
        <div className={"bt-run-return " + (r.ret >= 0 ? "pos" : "neg")}>
          {r.ret >= 0 ? "+" : ""}{(r.ret * 100).toFixed(1)}%
        </div>
      </div>
    ))}
  </aside>
);

// ========== Center main ==========
const BtMain = ({ run, comparisons }) => {
  const allRuns = [run, ...comparisons];

  const excessAnn = ((1 + run.cagr) / (1 + BT_BENCH.cagr) - 1);

  const heroStats = [
    { lbl: "Total return", val: `${(run.totalReturn * 100).toFixed(1)}%`, pos: run.totalReturn >= 0,
      sub: <><span className="up">+{((run.totalReturn - BT_BENCH.totalReturn) * 100).toFixed(1)}%</span> vs SPY</> },
    { lbl: "CAGR", val: `${(run.cagr * 100).toFixed(1)}%`, pos: true,
      sub: <><span className="up">+{(excessAnn * 100).toFixed(1)}%</span> excess</> },
    { lbl: "Sharpe", val: run.sharpe.toFixed(2), pos: run.sharpe >= 1,
      sub: <>SPY <b style={{color:"var(--ink-2)"}}>{BT_BENCH.sharpe.toFixed(2)}</b></> },
    { lbl: "Max DD", val: `${(run.maxDD * 100).toFixed(1)}%`, neg: true,
      sub: <>trough <b style={{color:"var(--ink-2)"}}>Sep '23</b></> },
    { lbl: "Win rate", val: `${(run.winRate * 100).toFixed(0)}%`,
      sub: <>of {run.trades} trades</> },
  ];

  return (
    <div className="bt-main">
      <div className="bt-hero-stats">
        {heroStats.map((s, i) => (
          <div key={i} className="bt-hs">
            <div className="lbl">{s.lbl}</div>
            <div className={"val" + (s.pos ? " pos" : s.neg ? " neg" : "")}>{s.val}</div>
            <div className="sub">{s.sub}</div>
          </div>
        ))}
      </div>

      <div className="bt-chart-card">
        <div className="bt-chart-head">
          <div className="bt-chart-title">Equity curve · indexed to 100</div>
          <div className="bt-chart-legend">
            <span className="lg"><span className="sw" style={{background:"var(--primary)"}}/> <b>{run.name}</b></span>
            {comparisons.map(c => (
              <span key={c.id} className="lg">
                <span className="sw" style={{background:`var(--${c.color==="c2"?"accent":"accent-2"})`}}/>
                {c.name}
              </span>
            ))}
            <span className="lg"><span className="sw" style={{background:"var(--ink-4)"}}/> SPY benchmark</span>
          </div>
        </div>
        <EquityChart runs={allRuns} showBench />
      </div>

      <div className="bt-chart-card bt-dd-card">
        <div className="bt-chart-head">
          <div className="bt-chart-title">Drawdown · peak-to-trough</div>
          <div className="bt-chart-legend">
            <span className="lg">Worst <b>{(run.maxDD * 100).toFixed(1)}%</b> on Sep '23</span>
            <span className="lg">Recovery <b>94 days</b></span>
          </div>
        </div>
        <DrawdownStrip run={run} />
      </div>

      <h2 className="bt-section-title">Risk & return</h2>
      <div className="bt-tear-grid">
        <Metric lbl="Sortino" val={run.sortino.toFixed(2)} tone="pos" bm={`SPY ${(BT_BENCH.sharpe * 1.15).toFixed(2)}`} />
        <Metric lbl="Calmar"  val={(run.cagr / -run.maxDD).toFixed(2)} tone="pos" bm="target ≥ 1.0" />
        <Metric lbl="Volatility (ann)" val="14.8%" bm="SPY 16.2%" />
        <Metric lbl="Beta to SPY" val="0.84" bm="target 0.70–0.90" />
        <Metric lbl="Alpha (ann)" val="6.2%" tone="pos" bm="t-stat 2.41" />
        <Metric lbl="Information ratio" val="0.88" tone="pos" bm="target ≥ 0.5" />
        <Metric lbl="Skew" val="-0.23" tone="caution" bm="mild left tail" />
        <Metric lbl="Kurtosis" val="3.8" bm="normal 3.0" />
      </div>

      <h2 className="bt-section-title">Turnover & costs</h2>
      <div className="bt-tear-grid">
        <Metric lbl="Turnover (ann)" val="312%" bm="2.6× monthly" />
        <Metric lbl="Avg hold" val="34d" bm="median 28d" />
        <Metric lbl="Cost drag (ann)" val="-1.4%" tone="neg" bm={run.costs + " avg"} />
        <Metric lbl="Slippage" val="-0.38%" tone="neg" bm="VWAP model" />
      </div>
    </div>
  );
};

const Metric = ({ lbl, val, tone, bm }) => (
  <div className="bt-metric">
    <div className="lbl">{lbl}</div>
    <div className={"val" + (tone ? " " + tone : "")}>{val}</div>
    {bm && <div className="bm">{bm}</div>}
  </div>
);

// ========== Right: trade blotter ==========
const TradeBlotter = () => {
  const [filter, setFilter] = useStateBt("all");
  const trades = BT_TRADES.filter(t => filter === "all" || t.side === filter);
  return (
    <aside className="bt-side">
      <h3 className="bt-side-head">Trade blotter</h3>
      <p className="bt-side-sub">Last 12 of 284 · total P&amp;L +$5,750</p>
      <div className="bt-side-pills">
        {["all", "buy", "sell"].map(p => (
          <div key={p} className={"bt-side-pill" + (p === filter ? " active" : "")} onClick={() => setFilter(p)}>
            {p === "all" ? "All" : p === "buy" ? "Entries" : "Exits"}
          </div>
        ))}
      </div>
      {trades.map((t, i) => (
        <div key={i} className="bt-trade">
          <div className={"bt-trade-side " + t.side}>{t.side}</div>
          <div className="bt-trade-body">
            <div className="bt-trade-tk">{t.tk}</div>
            <div className="bt-trade-date">{t.date}</div>
          </div>
          <div className={"bt-trade-pnl " + (t.pnl >= 0 ? "pos" : "neg")}>
            {t.pnl >= 0 ? "+" : ""}${t.pnl}
            <div className="days">{t.held}d hold</div>
          </div>
        </div>
      ))}
    </aside>
  );
};

// ========== Compare strip ==========
const CompareStrip = ({ comparisons, onRemove, onAdd }) => (
  <div className="bt-compare">
    <div className="bt-compare-label">Compare</div>
    <div className="bt-compare-runs">
      {comparisons.map(c => (
        <div key={c.id} className="bt-compare-item">
          <div className={"bt-run-dot " + c.color} />
          <div style={{minWidth:0}}>
            <div className="bt-compare-name">{c.name}</div>
            <div className="bt-compare-sub">
              {(c.totalReturn * 100).toFixed(1)}% · Sharpe {c.sharpe.toFixed(2)} · DD {(c.maxDD * 100).toFixed(1)}%
            </div>
          </div>
          <div className="rem" onClick={() => onRemove(c.id)}>
            <Icon name="close" size={12} />
          </div>
        </div>
      ))}
      <div className="bt-compare-add" onClick={onAdd}>
        <Icon name="plus" size={12} /> Add run
      </div>
    </div>
    <div className="bt-compare-actions">
      <button className="btn ghost sm"><Icon name="external" size={12}/> Export tear sheet</button>
      <button className="btn primary sm"><Icon name="decision" size={12}/> Promote to paper</button>
    </div>
  </div>
);

Object.assign(window, { StrategyBar, RunsList, BtMain, TradeBlotter, CompareStrip });
