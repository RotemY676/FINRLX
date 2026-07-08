// Ops Command Center — data, modules, workspace composer

const { useState: useStateOps } = React;

// ───────────── Data ─────────────
const OPS_QUEUE = [
  { id:"REC-2026-0419-NVDA-L", tk:"NVDA", stance:"LONG", version:"v4", submitted:"12m",
    submitter:"R. Mikhailov", weight:"+4.2%", conf:0.74, flags:["sector cap"], priority:"high" },
  { id:"REC-2026-0419-XOM-S", tk:"XOM", stance:"SHORT", version:"v2", submitted:"22m",
    submitter:"A. Chen", weight:"−2.1%", conf:0.68, flags:["breach: oil 12%/10%"], priority:"high" },
  { id:"REC-2026-0419-MSFT-T", tk:"MSFT", stance:"TRIM", version:"v3", submitted:"8m",
    submitter:"J. Park", weight:"−0.9%", conf:0.62, flags:["Azure caveat"], priority:"mid" },
  { id:"REC-2026-0419-AAPL-L", tk:"AAPL", stance:"LONG", version:"v2", submitted:"84m",
    submitter:"R. Mikhailov", weight:"+1.8%", conf:0.71, flags:["stale"], priority:"mid" },
  { id:"REC-2026-0419-TSM-L", tk:"TSM", stance:"LONG", version:"v1", submitted:"2h",
    submitter:"M. Alvarez", weight:"+1.4%", conf:0.66, flags:[], priority:"low" },
  { id:"REC-2026-0419-JPM-H", tk:"JPM", stance:"HOLD", version:"v1", submitted:"3h",
    submitter:"A. Chen", weight:"0.0%", conf:0.55, flags:[], priority:"low" },
  { id:"REC-2026-0419-KO-H", tk:"KO", stance:"HOLD", version:"v2", submitted:"4h",
    submitter:"J. Park", weight:"0.0%", conf:0.51, flags:[], priority:"low" },
];

const OPS_FEEDS = [
  { name:"Reuters · news intel", status:"ok", lag:"0s", coverage:"99.8%", slo:0.98, pulse:true },
  { name:"Bloomberg · price feed", status:"ok", lag:"12ms", coverage:"100%", slo:0.99, pulse:true },
  { name:"Options flow · CBOE", status:"degraded", lag:"14m", coverage:"72%", slo:0.86, pulse:false },
  { name:"Earnings · Factset", status:"ok", lag:"3s", coverage:"99.4%", slo:0.97, pulse:true },
  { name:"Alt data · satellite", status:"stale", lag:"2.4h", coverage:"41%", slo:0.64, pulse:false },
  { name:"Fundamentals · internal", status:"ok", lag:"0s", coverage:"100%", slo:1.0, pulse:true },
];

const OPS_ENGINES = [
  { name:"Momentum", latency:"82ms", drift:-0.03, lastRun:"2m", status:"ok" },
  { name:"Quality", latency:"156ms", drift:0.01, lastRun:"2m", status:"ok" },
  { name:"Earnings revisions", latency:"94ms", drift:-0.02, lastRun:"3m", status:"ok" },
  { name:"Value", latency:"118ms", drift:0.08, lastRun:"2m", status:"warn" },
  { name:"Flow/options", latency:"284ms", drift:-0.14, lastRun:"14m", status:"degraded" },
];

const OPS_INCIDENTS = [
  { id:"INC-2026-0419-003", title:"Options flow feed — latency spike",
    started:"14m ago", severity:"sev-2", owner:"M. Alvarez", status:"investigating",
    affectedRecs:11, note:"Confidence capped for flow engine until recovery." },
  { id:"INC-2026-0419-002", title:"Alt-data satellite refresh failed",
    started:"2h ago", severity:"sev-3", owner:"ops-bot", status:"monitoring",
    affectedRecs:0, note:"Vendor acknowledged; next refresh 16:00 UTC." },
];

const OPS_BREACHES = [
  { kind:"sector", label:"Semiconductors · 28.1% / 30%", utilization:0.937, trend:"+0.8%",
    severity:"high", related:"NVDA promotion would add ~0.6%" },
  { kind:"single", label:"NVDA single-name · 4.2% / 5.0%", utilization:0.84, trend:"+0.3%",
    severity:"mid", related:"Reviewed by J. Park · 12m ago" },
  { kind:"oil", label:"Energy net exposure · 12% / 10%", utilization:1.2, trend:"+1.9%",
    severity:"breach", related:"Hard breach · escalated" },
];

const OPS_AUDIT = [
  { when:"2m", actor:"R. Mikhailov", action:"published", target:"REC…NVDA-L v4", scope:"paper", ok:true },
  { when:"8m", actor:"ops-bot", action:"down-weighted engine", target:"Flow/options", scope:"system", ok:true },
  { when:"12m", actor:"J. Park", action:"approved policy exception", target:"Semis cap watch", scope:"policy", ok:true },
  { when:"14m", actor:"system", action:"opened incident", target:"INC-2026-0419-003", scope:"ops", ok:false },
  { when:"22m", actor:"A. Chen", action:"submitted for review", target:"REC…XOM-S v2", scope:"queue", ok:true },
  { when:"38m", actor:"ops-bot", action:"breach warning", target:"Energy exposure 12%/10%", scope:"policy", ok:false },
  { when:"44m", actor:"M. Alvarez", action:"ran backtest #204", target:"Momentum + quality", scope:"system", ok:true },
  { when:"1h", actor:"R. Mikhailov", action:"deferred", target:"REC…XOM-S", scope:"queue", ok:true },
];

// ───────────── Helpers ─────────────
const statusColor = {
  ok: "var(--pos)", warn: "var(--caution)", degraded: "var(--caution)",
  stale: "var(--breach)", breach: "var(--breach)", down: "var(--breach)",
};

const Pulse = ({ on, color = "var(--pos)" }) => (
  <span className="ops-pulse" data-on={on ? "1" : "0"} style={{ "--pc": color }}>
    <span className="dot" />
    {on && <span className="ring" />}
  </span>
);

// ───────────── Modules ─────────────
function ModSystemStrip() {
  return (
    <div className="card ops-system">
      <div className="card-body" style={{ display:"grid", gridTemplateColumns:"repeat(6, 1fr)", gap:14 }}>
        {[
          { k:"Uptime · 30d", v:"99.94%", sub:"SLA 99.9%", tone:"pos" },
          { k:"Rescore rate", v:"184 /min", sub:"+12% intraday", tone:"neutral" },
          { k:"Open incidents", v:"2", sub:"1 sev-2 · 1 sev-3", tone:"caution" },
          { k:"Queue depth", v:"7", sub:"3 need review", tone:"primary" },
          { k:"Feed coverage", v:"87%", sub:"2 degraded", tone:"caution" },
          { k:"Policy breaches", v:"1", sub:"Energy · hard", tone:"breach" },
        ].map((k,i)=>(
          <div key={i} className={"ov-kpi tone-"+k.tone}>
            <div className="k">{k.k}</div>
            <div className="v">{k.v}</div>
            <div className="sub">{k.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModQueue({ selected, onSelect, bulkMode }) {
  const sevCls = s => s==="high"?"breach":s==="mid"?"caution":"info";
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="check" size={14}/>
        <h3>Publication queue</h3>
        <div className="meta">
          <span>{OPS_QUEUE.length} pending · 2 require approval</span>
          <div className="seg">
            <button className="active">All</button>
            <button>Mine</button>
            <button>High priority</button>
          </div>
        </div>
      </div>
      <div className="card-body" style={{ padding:0 }}>
        {bulkMode && (
          <div className="ops-bulk-bar">
            <span className="ops-bulk-count">2 selected</span>
            <button className="btn ghost sm">Defer</button>
            <button className="btn ghost sm">Challenge</button>
            <button className="btn primary sm"><Icon name="check" size={12}/> Approve all</button>
          </div>
        )}
        <table className="ov-table ops-queue-table">
          <thead>
            <tr>
              {bulkMode && <th style={{width:34}}></th>}
              <th>Recommendation</th>
              <th>Stance</th>
              <th>Weight</th>
              <th>Conf</th>
              <th>Submitter</th>
              <th>Age</th>
              <th>Flags</th>
              <th style={{width:200}}>Action</th>
            </tr>
          </thead>
          <tbody>
            {OPS_QUEUE.map((r,i)=>(
              <tr key={r.id}
                  className={selected===r.id?"selected":""}
                  onClick={()=>onSelect && onSelect(r.id)}>
                {bulkMode && <td><input type="checkbox" defaultChecked={i<2} className="ops-cb"/></td>}
                <td>
                  <div className="ov-rec">
                    <span className="tk">{r.tk}</span>
                    <span className="id">{r.id} · {r.version}</span>
                  </div>
                </td>
                <td>
                  <span className={"ov-stance " + (r.stance==="LONG"?"buy":r.stance==="SHORT"?"sell":r.stance==="TRIM"?"trim":"hold")}>
                    {r.stance}
                  </span>
                </td>
                <td className="num">{r.weight}</td>
                <td className="num">{r.conf.toFixed(2)}</td>
                <td style={{fontSize:12}}>{r.submitter}</td>
                <td><span className="age">{r.submitted}</span></td>
                <td>
                  {r.flags.length === 0 ? <span style={{color:"var(--ink-4)"}}>—</span> :
                    <div className="flags">
                      {r.flags.map((f,j)=>(
                        <span key={j} className={"flag " + (f.includes("breach")?"breach":"caution")}>
                          <Icon name={f.includes("breach")?"risk":"info"} size={10}/>{f}
                        </span>
                      ))}
                    </div>
                  }
                </td>
                <td>
                  {!bulkMode && (
                    <div style={{ display:"flex", gap:4 }}>
                      <button className="btn ghost sm">Defer</button>
                      <button className="btn ghost sm">Challenge</button>
                      <button className="btn primary sm">Approve</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModFeeds({ pulse }) {
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="news" size={14}/>
        <h3>Data‑source health</h3>
        <div className="meta"><span>6 feeds · 4 ok · 2 degraded</span></div>
      </div>
      <div className="card-body" style={{ padding:"6px 0" }}>
        {OPS_FEEDS.map((f,i)=>(
          <div key={i} className="ops-feed">
            <Pulse on={pulse && f.pulse} color={statusColor[f.status]}/>
            <div className="ops-feed-name">
              <div className="nm">{f.name}</div>
              <div className="meta">lag {f.lag} · coverage {f.coverage}</div>
            </div>
            <div className="ops-slo">
              <div className="bar"><span style={{ width:(f.slo*100)+"%", background:statusColor[f.status] }}/></div>
              <span className="num">{(f.slo*100).toFixed(1)}%</span>
            </div>
            <span className={"ops-status-pill st-"+f.status}>{f.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModEngines() {
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="compare" size={14}/>
        <h3>Engine health</h3>
        <div className="meta"><span>5 engines · 1 degraded · 1 drift watch</span></div>
      </div>
      <div className="card-body" style={{ padding:0 }}>
        <table className="ov-table ops-engines">
          <thead>
            <tr><th>Engine</th><th>Latency</th><th>Confidence drift</th><th>Last run</th><th>Status</th></tr>
          </thead>
          <tbody>
            {OPS_ENGINES.map((e,i)=>{
              const driftPos = e.drift >= 0;
              return (
                <tr key={i}>
                  <td style={{ fontWeight:500 }}>{e.name}</td>
                  <td className="num">{e.latency}</td>
                  <td>
                    <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                      <div className="ops-drift-bar">
                        <span className="mid"/>
                        <span className={driftPos?"pos":"neg"} style={{
                          width: Math.min(Math.abs(e.drift)*200, 50) + "%",
                          [driftPos?"left":"right"]: "50%",
                        }}/>
                      </div>
                      <span className={"num " + (driftPos?"hl-pos":"hl-neg")}>
                        {driftPos?"+":""}{e.drift.toFixed(2)}σ
                      </span>
                    </div>
                  </td>
                  <td><span className="age">{e.lastRun}</span></td>
                  <td><span className={"ops-status-pill st-"+e.status}>{e.status}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModBreaches({ onOpen }) {
  return (
    <div className="card ops-breaches">
      <div className="card-head">
        <Icon name="risk" size={14}/>
        <h3>Policy breaches &amp; watch</h3>
        <div className="meta"><span>1 hard breach · 2 approaching</span></div>
      </div>
      <div className="card-body" style={{ display:"flex", flexDirection:"column", gap:8, padding:"10px 14px" }}>
        {OPS_BREACHES.map((b,i)=>(
          <div key={i} className={"ops-breach-row sev-"+b.severity}>
            <div className="ops-breach-ic">
              <Icon name={b.severity==="breach"?"risk":"info"} size={14}/>
            </div>
            <div className="ops-breach-body">
              <div className="ops-breach-label">{b.label}</div>
              <div className="ops-breach-meta">{b.related}</div>
            </div>
            <div className="ops-breach-util">
              <div className="bar">
                <span style={{
                  width: Math.min(b.utilization*100, 100)+"%",
                  background: b.severity==="breach"?"var(--breach)":b.severity==="high"?"var(--caution)":"var(--primary)"
                }}/>
              </div>
              <span className="num">{(b.utilization*100).toFixed(0)}%</span>
              <span className={"trend " + (b.trend.startsWith("+")?"up":"down")}>{b.trend}</span>
            </div>
            <button className="btn ghost sm" onClick={()=>onOpen && onOpen(b)}>Review →</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModIncidents({ onOpen }) {
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="risk" size={14}/>
        <h3>Active incidents</h3>
        <div className="meta"><span>2 open · last update 4m</span></div>
      </div>
      <div className="card-body" style={{ padding:"6px 0" }}>
        {OPS_INCIDENTS.map((i,j)=>(
          <div key={j} className={"ops-incident sev-"+i.severity} onClick={()=>onOpen && onOpen(i)}>
            <div className="ops-inc-head">
              <span className={"ops-sev-tag sev-"+i.severity}>{i.severity}</span>
              <span className="ops-inc-id">{i.id}</span>
              <span className="ops-inc-status">{i.status}</span>
              <span className="ops-inc-age">{i.started}</span>
            </div>
            <div className="ops-inc-title">{i.title}</div>
            <div className="ops-inc-meta">
              <span>Owner <b>{i.owner}</b></span>
              {i.affectedRecs>0 && <span>{i.affectedRecs} recs affected</span>}
              <span>{i.note}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModAudit() {
  const [filter, setFilter] = useStateOps("all");
  const rows = filter==="all" ? OPS_AUDIT : OPS_AUDIT.filter(r=>r.scope===filter);
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="news" size={14}/>
        <h3>Audit log</h3>
        <div className="meta">
          <div className="seg sm">
            {["all","queue","policy","ops","system"].map(f=>(
              <button key={f} className={filter===f?"active":""} onClick={()=>setFilter(f)}>
                {f==="all"?"All":f.charAt(0).toUpperCase()+f.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="card-body" style={{ padding:0 }}>
        <table className="ov-table ops-audit">
          <thead>
            <tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th><th>Scope</th></tr>
          </thead>
          <tbody>
            {rows.map((r,i)=>(
              <tr key={i}>
                <td><span className="age">{r.when}</span></td>
                <td>
                  <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                    <span className={"ops-audit-dot " + (r.ok?"ok":"warn")}/>
                    <span>{r.actor}</span>
                  </div>
                </td>
                <td style={{ color:"var(--ink-2)" }}>{r.action}</td>
                <td className="id" style={{ fontFamily:"var(--font-mono)", fontSize:12, color:"var(--ink-2)" }}>{r.target}</td>
                <td><span className="ops-scope">{r.scope}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ───────────── Incident drawer ─────────────
function IncidentDrawer({ incident, onClose }) {
  if (!incident) return null;
  return (
    <div className="ops-drawer">
      <div className="ops-drawer-backdrop" onClick={onClose}/>
      <div className="ops-drawer-sheet">
        <div className="ops-drawer-head">
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <span className={"ops-sev-tag sev-"+incident.severity}>{incident.severity}</span>
              <span className="ops-inc-id">{incident.id}</span>
            </div>
            <h2 style={{ margin:"6px 0 0", fontFamily:"var(--font-display)", fontSize:22, fontWeight:500, letterSpacing:"-0.015em" }}>
              {incident.title}
            </h2>
            <div style={{ fontSize:13, color:"var(--ink-3)", marginTop:4 }}>
              Started {incident.started} · Owner {incident.owner} · {incident.status}
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><Icon name="close" size={16}/></button>
        </div>
        <div className="ops-drawer-body">
          <div className="ops-drawer-section">
            <div className="ov-label">Impact</div>
            <div style={{ fontSize:14, color:"var(--ink-2)", lineHeight:1.5 }}>
              {incident.note} {incident.affectedRecs>0 && `${incident.affectedRecs} recommendations are re-scoring with capped confidence.`}
            </div>
          </div>

          <div className="ops-drawer-section">
            <div className="ov-label">Timeline</div>
            <div className="ops-timeline">
              {[
                { t:"14m ago", e:"System detected latency spike >10s on CBOE options feed", kind:"warn" },
                { t:"13m ago", e:"Flow/options engine auto down-weighted (confidence cap 0.60)", kind:"ok" },
                { t:"12m ago", e:"Incident opened · sev-2 · notified M. Alvarez", kind:"warn" },
                { t:"8m ago", e:"M. Alvarez acknowledged · investigating vendor route", kind:"ok" },
                { t:"4m ago", e:"Partial recovery: 5/8 symbols backfilled", kind:"ok" },
              ].map((ev,i)=>(
                <div key={i} className="ops-tl-row">
                  <div className={"ops-tl-dot " + ev.kind}/>
                  <div className="ops-tl-time">{ev.t}</div>
                  <div className="ops-tl-event">{ev.e}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="ops-drawer-section">
            <div className="ov-label">Affected recommendations</div>
            <table className="ov-table" style={{ fontSize:12.5 }}>
              <thead><tr><th>Rec</th><th>Engine impact</th><th>Capped conf</th><th>Status</th></tr></thead>
              <tbody>
                {[
                  ["REC…NVDA-L v4","Flow −0.14","0.74 → 0.68","monitoring"],
                  ["REC…MSFT-T v3","Flow −0.22","0.62 → 0.54","monitoring"],
                  ["REC…META-H v1","Flow −0.31","0.58 → 0.48","re-scoring"],
                ].map((r,i)=>(
                  <tr key={i}>
                    <td className="id" style={{ fontFamily:"var(--font-mono)" }}>{r[0]}</td>
                    <td className="num hl-neg">{r[1]}</td>
                    <td className="num">{r[2]}</td>
                    <td><span className="ops-status-pill st-warn">{r[3]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="ops-drawer-section">
            <div className="ov-label">Actions</div>
            <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
              <button className="btn ghost sm">Open runbook</button>
              <button className="btn ghost sm">Page on-call</button>
              <button className="btn ghost sm">Snooze 15m</button>
              <button className="btn primary sm">Mark resolved</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  ModSystemStrip, ModQueue, ModFeeds, ModEngines, ModBreaches, ModIncidents, ModAudit,
  IncidentDrawer
});
