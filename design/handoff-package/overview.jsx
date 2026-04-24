// Overview — triage, portfolio health, activity feed
const { useState: useStateOv } = React;

// ----- Triage row -----
const TRIAGE = [
  { id:"REC-2026-0419-NVDA-L", ticker:"NVDA", name:"NVIDIA Corp", stance:"buy",
    status:"fresh", ageMin:12, conf:0.74, expDelta:+0.048, weight:"+4.2%",
    reason:"Momentum accelerating · EPS revisions +4.8%", risk:"moderate",
    flags:["Sector 28.1%/30% limit"], dispersion:0.37, sector:"Semiconductors" },
  { id:"REC-2026-0419-MSFT-T", ticker:"MSFT", name:"Microsoft", stance:"trim",
    status:"provisional", ageMin:8, conf:0.62, expDelta:-0.018, weight:"−0.9%",
    reason:"Azure deceleration · relative momentum fading", risk:"moderate",
    flags:["Azure growth caveat"], dispersion:0.41, sector:"Software" },
  { id:"REC-2026-0419-META-H", ticker:"META", name:"Meta Platforms", stance:"hold",
    status:"pending", ageMin:3, conf:0.58, expDelta:+0.009, weight:"0.0%",
    reason:"Engines split 3/5 · awaiting earnings", risk:"elevated",
    flags:["Engine split"], dispersion:0.58, sector:"Internet" },
  { id:"REC-2026-0419-XOM-S", ticker:"XOM", name:"Exxon Mobil", stance:"sell",
    status:"fresh", ageMin:22, conf:0.68, expDelta:-0.031, weight:"−2.1%",
    reason:"Crude regime shift · margin compression", risk:"high",
    flags:["Breach: oil exposure 12%/10%"], dispersion:0.22, sector:"Energy" },
  { id:"REC-2026-0419-AAPL-L", ticker:"AAPL", name:"Apple", stance:"buy",
    status:"stale", ageMin:84, conf:0.71, expDelta:+0.022, weight:"+1.8%",
    reason:"Services growth + buyback · thesis intact", risk:"low",
    flags:["Data stale 84m"], dispersion:0.31, sector:"Hardware" },
];

const StanceBadge = ({ s }) => (
  <span className={"ov-stance " + s}>
    {s === "buy" ? "LONG" : s === "sell" ? "SHORT" : s === "trim" ? "TRIM" : "HOLD"}
  </span>
);

const StatusDot = ({ s }) => (
  <span className={"ov-status-dot " + s} title={s}>
    <span className="dot" />
    {s === "fresh" ? "Fresh" : s === "provisional" ? "Provisional" :
     s === "published" ? "Published" : s === "pending" ? "Pending" : "Stale"}
  </span>
);

const Sparkline = ({ points, color }) => {
  const W = 80, H = 24;
  const min = Math.min(...points), max = Math.max(...points);
  const sx = i => (i / (points.length - 1)) * W;
  const sy = v => H - ((v - min) / (max - min || 1)) * H;
  const d = points.map((p, i) => (i === 0 ? "M" : "L") + sx(i).toFixed(1) + " " + sy(p).toFixed(1)).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:W,height:H,display:"block"}}>
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
};

const TriageTable = () => (
  <div className="card ov-triage">
    <div className="card-head">
      <Icon name="decision" size={14}/>
      <h3>Needs attention today</h3>
      <div className="meta">
        <span>{TRIAGE.length} recommendations · ranked by conviction × freshness</span>
        <div className="seg">
          <button className="active">All</button>
          <button>Fresh</button>
          <button>Flagged</button>
          <button>Watched</button>
        </div>
      </div>
    </div>
    <div className="card-body" style={{padding:0}}>
      <table className="ov-table">
        <thead>
          <tr>
            <th style={{width:44}}></th>
            <th>Recommendation</th>
            <th>Stance</th>
            <th>Confidence</th>
            <th>Expected Δ</th>
            <th>Weight</th>
            <th style={{width:90}}>10d</th>
            <th>Status</th>
            <th>Why</th>
            <th style={{width:34}}></th>
          </tr>
        </thead>
        <tbody>
          {TRIAGE.map((r, i) => {
            const spark = Array.from({length:10}, (_,k)=>Math.sin(i+k*0.7)*0.5 + (k*(r.expDelta>0?0.12:-0.08)) + i);
            const sparkColor = r.expDelta >= 0 ? "var(--pos)" : "var(--breach)";
            const deltaCls = r.expDelta >= 0 ? "hl-pos" : "hl-neg";
            return (
              <tr key={r.id}>
                <td><span className="ov-rank">{i+1}</span></td>
                <td>
                  <div className="ov-rec">
                    <a href="Decision Workspace.html" className="tk">{r.ticker}</a>
                    <span className="nm">{r.name}</span>
                    <span className="id">{r.id}</span>
                  </div>
                </td>
                <td><StanceBadge s={r.stance}/></td>
                <td>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <div className="engine-conf-bar" style={{width:56}}><span style={{width:(r.conf*100)+"%"}} /></div>
                    <span className="num" style={{fontSize:12}}>{r.conf.toFixed(2)}</span>
                  </div>
                </td>
                <td className={"num " + deltaCls}>{r.expDelta >=0?"+":""}{(r.expDelta*100).toFixed(1)}%</td>
                <td className="num">{r.weight}</td>
                <td><Sparkline points={spark} color={sparkColor}/></td>
                <td><StatusDot s={r.status}/>
                  <div className="age">{r.ageMin}m ago</div>
                </td>
                <td className="why">{r.reason}
                  {r.flags.length > 0 && (
                    <div className="flags">
                      {r.flags.map((f,j)=>(
                        <span key={j} className={"flag " + (f.includes("Breach")?"breach":f.includes("stale")||f.includes("limit")||f.includes("caveat")?"caution":"info")}>
                          <Icon name={f.includes("Breach")?"risk":"info"} size={10}/>{f}
                        </span>
                      ))}
                    </div>
                  )}
                </td>
                <td>
                  <button className="icon-btn sm" title="Open">
                    <Icon name="chevron-right" size={14}/>
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
);

// ----- Portfolio health -----
const HEALTH = [
  { k:"AUM", v:"$ 2.84 B", sub:"intraday −0.18%", tone:"neutral" },
  { k:"Positions", v:"184", sub:"+3 new · 2 closed", tone:"neutral" },
  { k:"Publishable queue", v:"7", sub:"3 require review", tone:"primary" },
  { k:"Breach watch", v:"2", sub:"sector · single-name", tone:"breach" },
  { k:"Freshness", v:"94%", sub:"6% stale > 60m", tone:"caution" },
  { k:"Coverage", v:"96%", sub:"universe US-LargeCap", tone:"pos" },
];

const HealthStrip = () => (
  <div className="ov-health">
    {HEALTH.map((h, i) => (
      <div key={i} className={"ov-kpi tone-"+h.tone}>
        <div className="k">{h.k}</div>
        <div className="v">{h.v}</div>
        <div className="sub">{h.sub}</div>
      </div>
    ))}
  </div>
);

// Regime strip
const RegimeStrip = () => (
  <div className="card ov-regime">
    <div className="card-head">
      <Icon name="trend-up" size={14}/>
      <h3>Regime & signal posture</h3>
      <div className="meta"><span>as of 09:42 · re-classified 4h ago</span></div>
    </div>
    <div className="card-body">
      <div className="regime-grid">
        <div className="regime-col">
          <div className="ov-label">Current regime</div>
          <div className="regime-big">Risk‑on · late‑cycle</div>
          <div className="regime-meta">confidence 0.78 · persistence 41d · last switch 14 Mar</div>
          <div className="regime-switch">
            <div className="bar"><span style={{width:"78%"}}/></div>
            <span>risk‑off 0.14 · rotation 0.08</span>
          </div>
        </div>
        <div className="regime-col">
          <div className="ov-label">Signal posture</div>
          <ul className="posture-list">
            <li><span className="sw" style={{background:"var(--pos)"}}/> Momentum overweight <span className="num">+2.4σ</span></li>
            <li><span className="sw" style={{background:"var(--pos)"}}/> Quality overweight <span className="num">+1.1σ</span></li>
            <li><span className="sw" style={{background:"var(--ink-3)"}}/> Value neutral <span className="num">0.0σ</span></li>
            <li><span className="sw" style={{background:"var(--breach)"}}/> Low‑vol underweight <span className="num">−1.8σ</span></li>
          </ul>
        </div>
        <div className="regime-col">
          <div className="ov-label">Sector tilt</div>
          <div className="tilt-rows">
            {[["Semis","+3.2",1],["Software","+2.1",0.8],["Financials","+0.4",0.4],
              ["Energy","−1.6",-0.7],["Utilities","−2.4",-0.9]].map((t,i)=>(
              <div key={i} className="tilt-row">
                <span className="nm">{t[0]}</span>
                <div className="bar">
                  <span className={t[2]>=0?"pos":"neg"} style={{width:(Math.abs(t[2])*100)+"%", [t[2]>=0?"left":"right"]:"50%"}}/>
                </div>
                <span className={"num " + (t[2]>=0?"hl-pos":"hl-neg")}>{t[1]}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Activity feed
const ACTIVITY = [
  { kind:"publish", who:"R. Mikhailov", what:"published REC‑...NVDA‑L v4", when:"12m",
    meta:"Momentum + earnings · horizon 3M" },
  { kind:"breach", who:"system", what:"sector limit approaching", when:"38m",
    meta:"Semis 28.1% of 30% cap" },
  { kind:"engine", who:"system", what:"Flow/options engine down‑weighted", when:"44m",
    meta:"Data stale 14m · confidence capped" },
  { kind:"note", who:"J. Park", what:"added note to META thesis", when:"1h",
    meta:"Earnings in 2 days · review synthesis" },
  { kind:"defer", who:"A. Chen", what:"deferred XOM short to tomorrow", when:"2h",
    meta:"Awaiting crude inventory print" },
  { kind:"incident", who:"Ops", what:"reuters feed recovered", when:"3h",
    meta:"Backfilled 09:14 → 09:27 · re-scored 11 recs" },
  { kind:"backtest", who:"M. Alvarez", what:"backtest #204 complete", when:"3h",
    meta:"Momentum + quality · 5y IR 1.32" },
  { kind:"publish", who:"R. Mikhailov", what:"published REC‑...AAPL‑L v2", when:"4h", meta:"Services + buyback" },
];

const ActivityFeed = () => (
  <div className="card ov-activity">
    <div className="card-head">
      <Icon name="news" size={14}/>
      <h3>Activity</h3>
      <div className="meta">
        <div className="seg sm">
          <button className="active">All</button>
          <button>Mine</button>
          <button>System</button>
        </div>
      </div>
    </div>
    <div className="card-body" style={{padding:"6px 0"}}>
      {ACTIVITY.map((a, i) => (
        <div key={i} className={"ov-act ov-act-"+a.kind}>
          <div className={"ic ic-"+a.kind}>
            <Icon name={
              a.kind==="publish"?"check":a.kind==="breach"?"risk":a.kind==="engine"?"compare":
              a.kind==="note"?"paper":a.kind==="defer"?"clock":a.kind==="incident"?"info":"backtest"
            } size={12}/>
          </div>
          <div className="body">
            <div className="line">
              <b>{a.who}</b> {a.what} <span className="t">· {a.when}</span>
            </div>
            <div className="meta">{a.meta}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

Object.assign(window, { TriageTable, HealthStrip, RegimeStrip, ActivityFeed });
