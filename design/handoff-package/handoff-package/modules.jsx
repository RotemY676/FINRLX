// Evidence narrative, risk summary, disagreement
const EvidenceCard = () => (
  <div className="card">
    <div className="card-head">
      <Icon name="sparkle" size={14} style={{color:"var(--primary)"}} />
      <h3>Evidence narrative</h3>
      <div className="meta">
        <span>Last refreshed 12m ago</span>
        <button className="btn ghost sm"><Icon name="filter" size={12} /> Drivers</button>
      </div>
    </div>
    <div className="card-body">
      <div className="evidence-list">
        <div className="evi-row">
          <div className="evi-num">01</div>
          <div className="evi-text">
            <b>Earnings revisions</b> remain the dominant driver. 18 of 24 sell-side analysts
            raised FY26 EPS estimates over the last 30 days; median revision{" "}
            <span className="tok">+4.8%</span>, concentrated in data-center segment guidance.
          </div>
          <div className="evi-delta up">+4.8%</div>
        </div>
        <div className="evi-row">
          <div className="evi-num">02</div>
          <div className="evi-text">
            <b>Price momentum</b> in the top decile of the universe for a 9th consecutive week,
            with acceleration vs the equal-weight semi index <span className="tok">SOXX</span>.
            Factor attribution: momentum <span className="tok">+0.62</span>, quality <span className="tok">+0.31</span>.
          </div>
          <div className="evi-delta up">+0.62σ</div>
        </div>
        <div className="evi-row">
          <div className="evi-num">03</div>
          <div className="evi-text">
            <b>Options positioning</b> has rotated defensive. 30-day put/call skew widened;
            gamma exposure rolled negative through the 950 strike. Platform reads this as
            constructive-contrarian, not a breakdown.
          </div>
          <div className="evi-delta flat">±0</div>
        </div>
        <div className="evi-row">
          <div className="evi-num">04</div>
          <div className="evi-text">
            <b>News sentiment</b> mixed. Supply-chain risk narrative re-emerged after the
            16-Apr Taiwan logistics disruption; sector-level sentiment dropped{" "}
            <span className="tok">-0.22</span> but NVDA-specific remained <span className="tok">+0.11</span>.
          </div>
          <div className="evi-delta down">-0.22</div>
        </div>
        <div className="evi-row">
          <div className="evi-num">05</div>
          <div className="evi-text">
            <b>Regime filter</b> flags late-cycle risk-on with widening dispersion. Platform
            down-weights beta-carry engines by 15%; narrative & fundamentals engines unchanged.
          </div>
          <div className="evi-delta flat">—</div>
        </div>
      </div>

      <div className="caveat-row">
        <Icon name="alert-triangle" size={14} className="ic" />
        <span>
          <b>Attribution unavailable</b> for the fundamentals engine — it served a fallback
          path during the 09:20 data lag. Evidence above reflects the primary model only.
        </span>
        <span className="link">Open provenance</span>
      </div>
    </div>
  </div>
);

const RiskCard = () => {
  const items = [
    { name: "Portfolio weight", v: "4.2", u: "%", limit: 60, fill: 42, state: "ok" },
    { name: "Sector concentration", v: "28.1", u: "%", limit: 75, fill: 81, state: "caution" },
    { name: "Single-name drawdown", v: "-8.4", u: "%", limit: 60, fill: 35, state: "ok" },
    { name: "Correlation to top 5", v: "0.71", u: "", limit: 65, fill: 68, state: "caution" },
    { name: "Realized vol (30d)", v: "34.2", u: "%", limit: 50, fill: 42, state: "ok" },
    { name: "Policy constraints", v: "Passing", u: "", limit: 100, fill: 100, state: "ok" },
  ];
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="risk" size={14} style={{color:"var(--caution-soft-ink)"}} />
        <h3>Risk summary</h3>
        <div className="meta"><span>2 near limit · 0 breach</span></div>
      </div>
      <div className="card-body">
        <div className="risk-grid">
          {items.map((r, i) => (
            <div className="risk-item" key={i}>
              <div className="top">
                <span className="name">{r.name}</span>
                <span className={"state-dot " + (r.state === "caution" ? "caution" : r.state === "breach" ? "breach" : "")} />
              </div>
              <div className="v">{r.v}<small>{r.u}</small></div>
              <div className="risk-bar">
                <span className={r.state === "caution" ? "caution" : r.state === "breach" ? "breach" : ""}
                      style={{ width: r.fill + "%" }} />
                <div className="limit" style={{ left: r.limit + "%" }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const DisagreementCard = () => {
  const engines = [
    { name: "Momentum", mk: "M", stance: "buy", conf: 82, weight: "0.28" },
    { name: "Fundamentals", mk: "F", stance: "buy", conf: 71, weight: "0.24" },
    { name: "Narrative LLM", mk: "N", stance: "hold", conf: 58, weight: "0.18" },
    { name: "Risk-parity", mk: "R", stance: "hold", conf: 54, weight: "0.18" },
    { name: "Flow / options", mk: "O", stance: "sell", conf: 49, weight: "0.12" },
  ];
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="compare" size={14} />
        <h3>Engine disagreement</h3>
        <div className="meta">
          <a href="Engine Comparison.html" className="btn ghost sm" style={{textDecoration:"none"}}>Open matrix <Icon name="chevron-right" size={12} /></a>
        </div>
      </div>
      <div className="card-body">
        <div className="diverge-head">
          <div className="diverge-score">
            <span className="v">0.37</span>
            <span className="lbl">/ 1 dispersion · mixed</span>
          </div>
          <div style={{marginLeft:"auto",fontSize:12,color:"var(--ink-3)"}}>
            4/5 long · 1 short
          </div>
        </div>
        {engines.map((e, i) => (
          <div className="engine-row" key={i}>
            <div className="engine-name">
              <span className="mk">{e.mk}</span>
              {e.name}
            </div>
            <div className={"engine-stance " + e.stance}>{e.stance}</div>
            <div className="engine-conf-bar"><span style={{width: e.conf+"%"}} /></div>
            <div className="engine-weight">w {e.weight}</div>
          </div>
        ))}
        <div className="caveat-row" style={{marginTop:14}}>
          <Icon name="info" size={14} className="ic" />
          <span>
            <b>Flow/options dissents</b> on near-term exposure; its weight is capped while
            options IV is stale. Tone of recommendation is therefore <b>provisional</b>.
          </span>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { EvidenceCard, RiskCard, DisagreementCard });
