// Universe browser — UI components

const { useState: useStateUn, useMemo: useMemoUn } = React;

const SECTOR_COLORS = {
  "Semis": "var(--primary)",
  "Software": "var(--accent-2)",
  "Comm Svc": "var(--accent)",
  "Hardware": "var(--pos)",
  "Networking": "var(--caution)",
  "Auto": "oklch(0.72 0.14 340)",
  "Financials": "oklch(0.68 0.12 170)",
  "Healthcare": "oklch(0.74 0.11 30)",
  "Energy": "oklch(0.7 0.15 55)",
  "Staples": "oklch(0.66 0.08 200)",
  "Industrials": "oklch(0.7 0.1 100)",
  "Utilities": "oklch(0.65 0.08 280)",
  "Discretionary": "oklch(0.72 0.12 380)",
};

const zClass = (z) => z > 0.4 ? "pos" : z < -0.4 ? "neg" : "neu";

const UnBar = ({ active }) => (
  <div className="un-bar">
    <div>
      <h1 className="un-bar-title">
        {active.name}
        <span className="count">{active.count} names</span>
      </h1>
      <div className="un-bar-meta">
        updated {active.updated} · owner {active.owner} · version 14
      </div>
    </div>
    <div className="un-bar-actions">
      <button className="btn ghost sm"><Icon name="history" size={12}/> Version history</button>
      <button className="btn ghost sm"><Icon name="external" size={12}/> Export CSV</button>
      <button className="btn primary sm"><Icon name="plus" size={12}/> New universe</button>
    </div>
  </div>
);

const UniverseList = ({ activeId, onSelect }) => (
  <aside className="un-universes">
    <div className="un-u-head">
      <span className="t">Saved universes</span>
      <span className="a">+ new</span>
    </div>
    {UNIVERSES.map(u => (
      <div key={u.id} className={"un-u" + (u.id === activeId ? " active" : "")} onClick={() => onSelect(u.id)}>
        <div className="un-u-name">{u.name}</div>
        <div className="un-u-sub">{u.count} names · {u.updated}</div>
        <div className="un-u-desc">{u.desc}</div>
      </div>
    ))}
  </aside>
);

const FilterRow = ({ filters, setFilters }) => {
  const chips = [
    { k: "minMcap", lbl: "min mcap", val: "$" + filters.minMcap + "B" },
    { k: "minADV",  lbl: "min ADV",  val: "$" + filters.minADV + "M" },
    { k: "liqMin",  lbl: "liquidity", val: "≥ " + filters.liqMin },
    { k: "sectors", lbl: "sectors", val: filters.sectors.length ? filters.sectors.length + " selected" : "all" },
    { k: "basketOnly", lbl: "scope", val: filters.basketOnly ? "in basket only" : "all", active: filters.basketOnly },
  ];
  return (
    <div className="un-filter-row">
      {chips.map(c => (
        <div key={c.k} className={"un-filter" + (c.active ? " active" : "")}>
          <span className="lbl">{c.lbl}</span>
          <span className="val">{c.val}</span>
          <Icon name="chevron-down" size={10} />
        </div>
      ))}
      <button className="btn ghost sm" style={{marginLeft:"auto"}}>Reset</button>
    </div>
  );
};

const ConstituentsTable = ({ rows, onToggle }) => (
  <div className="un-table-card">
    <div className="un-table-head">
      <h3 className="un-table-title">Constituents</h3>
      <span style={{fontFamily:"var(--font-mono)", fontSize:11, color:"var(--ink-3)"}}>
        {rows.filter(r => r.inBasket).length} / {rows.length} in basket
      </span>
    </div>
    <div className="un-table-wrap">
      <table className="un-table">
        <thead>
          <tr>
            <th style={{width:32}}></th>
            <th>Ticker</th>
            <th className="num">Mkt cap</th>
            <th className="num">ADV</th>
            <th>Liq</th>
            <th className="num">β</th>
            {FACTORS.map(f => <th key={f} className="num">{f}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.tk}>
              <td><span className={"un-in" + (r.inBasket ? " on" : "")} onClick={() => onToggle(r.tk)} /></td>
              <td>
                <div className="un-tk">{r.tk}</div>
                <div className="un-name-sub">{r.name} · {r.sector}</div>
              </td>
              <td className="num">${r.mcap}B</td>
              <td className="num">${r.adv.toFixed(1)}M</td>
              <td><span className={"un-liq " + r.liq}>{r.liq}</span></td>
              <td className="num">{r.beta.toFixed(2)}</td>
              {FACTORS.map(f => (
                <td key={f} className="num">
                  <span className={"un-z " + zClass(r.f[f])}>{r.f[f] >= 0 ? "+" : ""}{r.f[f].toFixed(1)}</span>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const DiffBanner = ({ rows }) => {
  // For demo: show simulated adds/removes if filters changed (static here)
  const inBasket = rows.filter(r => r.inBasket).length;
  return (
    <div className="un-diff">
      <div>
        Pending edits · <b>3 changes</b> to basket vs saved version 14
      </div>
      <div className="changes">
        <span className="add">+2 add</span>
        <span className="rem">−1 remove</span>
        <span style={{color:"var(--ink-3)"}}>→ {inBasket} names</span>
        <button className="btn ghost sm">Preview diff</button>
        <button className="btn primary sm">Save v15</button>
      </div>
    </div>
  );
};

const FactorPanel = ({ rows }) => {
  const inBasket = rows.filter(r => r.inBasket);
  const avgFactors = FACTORS.map(f => {
    const vals = inBasket.map(r => r.f[f]);
    const mean = vals.reduce((s, v) => s + v, 0) / (vals.length || 1);
    return { k: f, v: mean };
  });

  // Sector breakdown
  const sectorCounts = {};
  let totalMcap = 0;
  inBasket.forEach(r => {
    sectorCounts[r.sector] = sectorCounts[r.sector] || { count: 0, mcap: 0 };
    sectorCounts[r.sector].count += 1;
    sectorCounts[r.sector].mcap += r.mcap;
    totalMcap += r.mcap;
  });
  const sectors = Object.entries(sectorCounts)
    .map(([k, v]) => ({ k, ...v, pct: v.mcap / totalMcap }))
    .sort((a, b) => b.mcap - a.mcap);

  return (
    <aside className="un-factors">
      <h3 className="un-factors-head">Factor exposure</h3>
      <p className="un-factors-sub">Basket mean z-score · {inBasket.length} names</p>

      {avgFactors.map(f => {
        const pct = Math.min(1, Math.max(-1, f.v / 2));  // clamp to ±2σ
        const w = Math.abs(pct) * 50;
        const left = pct >= 0 ? 50 : 50 - w;
        return (
          <div key={f.k} className="un-factor">
            <div className="un-factor-top">
              <span className="k">{f.k}</span>
              <span className="v">{f.v >= 0 ? "+" : ""}{f.v.toFixed(2)}σ</span>
            </div>
            <div className="un-factor-bar">
              <div className="fill" style={{
                left: left + "%", width: w + "%",
                background: f.v >= 0 ? "var(--primary)" : "var(--breach)",
              }} />
              <div className="mid" />
            </div>
          </div>
        );
      })}

      <h3 className="un-factors-head" style={{marginTop:20, fontSize:14}}>Sector weights</h3>
      <p className="un-factors-sub">By market cap</p>
      <div className="un-sector-list">
        {sectors.map(s => (
          <div key={s.k} className="un-sector-item">
            <span className="sw" style={{background: SECTOR_COLORS[s.k] || "var(--ink-4)"}} />
            <span className="n">{s.k}</span>
            <span className="c">{s.count}</span>
            <span className="p">{(s.pct * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </aside>
  );
};

Object.assign(window, { UnBar, UniverseList, FilterRow, ConstituentsTable, DiffBanner, FactorPanel });
