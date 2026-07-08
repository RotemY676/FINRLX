// Design System — components tiers, patterns, states
const { useState: useStateDSC } = React;

// ─────── Reusable mini components for demos ───────
function MiniConfTrio({ model=0.78, data=0.94, ops=1.0 }) {
  const color = v => v>=0.9?"var(--pos)":v>=0.7?"var(--primary)":v>=0.5?"var(--caution)":"var(--breach)";
  return (
    <div className="ds-conf-trio">
      {[["Model", model],["Data quality", data],["Operational", ops]].map(([k,v])=>(
        <div key={k} className="item">
          <div className="k">{k}</div>
          <div className="bar"><span style={{ width: (v*100)+"%", background: color(v) }}/></div>
          <div className="v">{v.toFixed(2)}</div>
        </div>
      ))}
    </div>
  );
}

function MiniRecCard({ stance="LONG", muted=false }) {
  return (
    <div className="ds-rec-card" style={muted?{opacity:0.6}:{}}>
      <div className="head">
        <div>
          <div className="tk">NVDA</div>
          <div className="id">REC-2026-0419-NVDA-L · v4</div>
        </div>
        <span className={"ov-stance " + (stance==="LONG"?"buy":stance==="SHORT"?"sell":stance==="TRIM"?"trim":"hold")}>{stance}</span>
      </div>
      <div className="thesis">
        Four engines align above 0.68 on Q4 revision momentum; flow is supportive.
        Upside to 3M target is 12%, downside clipped by semis sector cap.
      </div>
      <MiniConfTrio/>
      <div className="meta-row">
        <div><span className="k">Weight</span><span className="v">+4.2%</span></div>
        <div><span className="k">Horizon</span><span className="v">3M</span></div>
        <div><span className="k">E[Δ]</span><span className="v">+0.082</span></div>
      </div>
    </div>
  );
}

// ─────── Alert mini ───────
function MiniAlert({ sev="info", title, desc }) {
  const map = {
    info: { bg:"color-mix(in oklch, var(--primary) 8%, var(--surface))", br:"color-mix(in oklch, var(--primary) 35%, var(--line))", fg:"var(--primary-soft-ink)", ic:"info" },
    caution: { bg:"var(--caution-soft)", br:"color-mix(in oklch, var(--caution) 35%, var(--line))", fg:"var(--caution-soft-ink)", ic:"alert-triangle" },
    breach: { bg:"var(--breach-soft)", br:"color-mix(in oklch, var(--breach) 35%, var(--line))", fg:"var(--breach-soft-ink)", ic:"risk" },
    pos: { bg:"var(--pos-soft)", br:"color-mix(in oklch, var(--pos) 35%, var(--line))", fg:"var(--pos-soft-ink)", ic:"check" },
  };
  const s = map[sev];
  return (
    <div style={{
      display:"flex", gap:10,
      padding:"10px 14px",
      background:s.bg,
      border:"1px solid "+s.br,
      borderRadius:"var(--r-md)",
    }}>
      <div style={{ color:s.fg, marginTop:1, flexShrink:0 }}><Icon name={s.ic} size={16}/></div>
      <div style={{ minWidth:0, flex:1 }}>
        <div style={{ fontSize:13, fontWeight:500, color:"var(--ink)" }}>{title}</div>
        {desc && <div style={{ fontSize:12, color:"var(--ink-2)", marginTop:2, lineHeight:1.45 }}>{desc}</div>}
      </div>
    </div>
  );
}

// ─────── Slot wrapper ───────
function Slot({ name, tier, state, children, center }) {
  return (
    <div className="ds-slot">
      <div className="ds-slot-head">
        <span className="tag">{tier}</span>
        <span>{name}</span>
        {state && <span className="state">{state}</span>}
      </div>
      <div className={"ds-slot-body" + (center?" center":"")}>{children}</div>
    </div>
  );
}

// ─────── Tier 1 ───────
function Tier1Section() {
  return (
    <section id="tier1" className="ds-section">
      <h2>Tier 1 — core components</h2>
      <p className="lead">
        The six primitives every workspace relies on. If any of these break,
        the whole product feels broken.
      </p>

      <Slot name="RecommendationCard" tier="T1" state="default">
        <MiniRecCard/>
      </Slot>

      <Slot name="ConfidenceBlock (trio)" tier="T1" state="default">
        <MiniConfTrio/>
        <div style={{ fontSize:12, color:"var(--ink-3)", lineHeight:1.5, maxWidth:520 }}>
          Three independent signals. Never collapse into one number — an analyst needs to see which
          factor is the weak link before accepting a recommendation.
        </div>
      </Slot>

      <Slot name="AlertSystem · severity tiers" tier="T1">
        <MiniAlert sev="info" title="Regime flipped to risk‑on" desc="Momentum, quality, and flow engines all re‑ran at 08:12."/>
        <MiniAlert sev="caution" title="Semis exposure approaching cap" desc="28.1% of 30% used. Promoting NVDA would reach 28.7%."/>
        <MiniAlert sev="breach" title="Energy exposure breached" desc="12% actual vs 10% policy. Escalated to ops · 38m ago."/>
        <MiniAlert sev="pos" title="Backtest #204 complete" desc="Momentum + quality blend · Sharpe 1.42, max DD 8.1%."/>
      </Slot>

      <Slot name="QueueItem" tier="T1" state="default">
        <div style={{ display:"flex", alignItems:"center", gap:12, padding:"12px 14px", background:"var(--surface)", border:"1px solid var(--line)", borderRadius:"var(--r-md)", width:"100%", maxWidth:680 }}>
          <span className="ov-stance buy" style={{flexShrink:0}}>LONG</span>
          <div style={{ minWidth:0, flex:1 }}>
            <div style={{ fontSize:13, fontWeight:500 }}>NVDA <span style={{color:"var(--ink-4)", fontFamily:"var(--font-mono)", fontSize:11}}>· REC‑…NVDA‑L v4</span></div>
            <div style={{ fontSize:11.5, color:"var(--ink-3)", marginTop:2 }}>R. Mikhailov · 12m ago · +4.2% · conf 0.74</div>
          </div>
          <div style={{ display:"flex", gap:4 }}>
            <button className="btn ghost sm">Defer</button>
            <button className="btn primary sm">Approve</button>
          </div>
        </div>
      </Slot>

      <Slot name="ComparisonTable (engines)" tier="T1" state="default">
        <table className="ov-table" style={{ maxWidth:720, width:"100%" }}>
          <thead><tr><th>Engine</th><th>Stance</th><th>Confidence</th><th>Weight</th></tr></thead>
          <tbody>
            {[
              ["Momentum","LONG",0.82,"0.28"],
              ["Quality","LONG",0.76,"0.22"],
              ["Earnings rev.","LONG",0.71,"0.20"],
              ["Value","HOLD",0.54,"0.18"],
              ["Flow/options","SHORT",0.42,"0.12"],
            ].map(([nm,st,c,w],i)=>(
              <tr key={i}>
                <td style={{fontWeight:500}}>{nm}</td>
                <td><span className={"ov-stance "+(st==="LONG"?"buy":st==="SHORT"?"sell":"hold")}>{st}</span></td>
                <td><div style={{display:"flex",alignItems:"center",gap:8}}>
                  <div style={{flex:1, maxWidth:90, height:5, background:"var(--surface-3)", borderRadius:999}}>
                    <div style={{width:(c*100)+"%", height:"100%", background:c>=0.7?"var(--primary)":"var(--caution)", borderRadius:999}}/>
                  </div>
                  <span className="num">{c.toFixed(2)}</span>
                </div></td>
                <td className="num">{w}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Slot>

      <Slot name="AppShell · three‑zone" tier="T1" state="schematic">
        <div style={{ display:"grid", gridTemplateColumns:"60px 1fr 180px", gap:4, width:"100%", maxWidth:560, height:220 }}>
          <div style={{ background:"var(--surface-2)", border:"1px solid var(--line)", borderRadius:6, padding:8, display:"flex", flexDirection:"column", gap:6 }}>
            {[0,1,2,3].map(i=><div key={i} style={{height:8, background:"var(--surface-3)", borderRadius:2}}/>)}
          </div>
          <div style={{ background:"var(--surface)", border:"1px solid var(--line)", borderRadius:6, padding:10, display:"flex", flexDirection:"column", gap:6 }}>
            <div style={{ display:"flex", gap:4 }}>
              <div style={{ flex:1, height:24, background:"var(--surface-2)", borderRadius:4 }}/>
              <div style={{ width:40, height:24, background:"var(--primary)", borderRadius:4 }}/>
            </div>
            <div style={{ flex:1, background:"var(--surface-2)", borderRadius:4 }}/>
          </div>
          <div style={{ background:"var(--surface-2)", border:"1px solid var(--line)", borderRadius:6, padding:8, display:"flex", flexDirection:"column", gap:4 }}>
            {[0,1,2].map(i=><div key={i} style={{height:28, background:"var(--surface-3)", borderRadius:3}}/>)}
          </div>
        </div>
        <div style={{ fontSize:12, color:"var(--ink-3)", textAlign:"center", maxWidth:480 }}>
          Left nav · workspace canvas · right context pane.
          Context pane collapses into a two‑zone layout under 1280px or on demand.
        </div>
      </Slot>
    </section>
  );
}

// ─────── Tier 2 ───────
function Tier2Section() {
  return (
    <section id="tier2" className="ds-section">
      <h2>Tier 2 — contextual components</h2>
      <p className="lead">
        Appear in specific workspaces. Should feel coherent with Tier 1 primitives but
        carry workspace‑specific affordances.
      </p>

      <Slot name="ScenarioControl · slider" tier="T2">
        <div style={{ width:"100%", maxWidth:420, display:"flex", flexDirection:"column", gap:6 }}>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:11.5 }}>
            <span style={{ color:"var(--ink-3)" }}>Revenue growth · FY26</span>
            <span style={{ fontFamily:"var(--font-mono)", color:"var(--ink)" }}>+14.2%</span>
          </div>
          <div style={{ position:"relative", height:6, background:"var(--surface-3)", borderRadius:999 }}>
            <div style={{ position:"absolute", left:0, top:0, bottom:0, width:"62%", background:"var(--primary)", borderRadius:999 }}/>
            <div style={{ position:"absolute", left:"62%", top:"50%", transform:"translate(-50%,-50%)", width:14, height:14, background:"var(--surface)", border:"2px solid var(--primary)", borderRadius:"50%" }}/>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"var(--ink-4)", fontFamily:"var(--font-mono)" }}>
            <span>0%</span><span>consensus 10%</span><span>25%</span>
          </div>
        </div>
      </Slot>

      <Slot name="Timeline · replay" tier="T2">
        <div style={{ width:"100%", maxWidth:560, position:"relative", paddingLeft:18 }}>
          {[
            ["08:12","Momentum engine rescored",true],
            ["09:04","Earnings beat published",false],
            ["11:28","Flow engine confidence capped",true],
            ["14:02","Recommendation promoted to paper",false],
          ].map(([t, e, warn], i)=>(
            <div key={i} style={{ display:"grid", gridTemplateColumns:"60px 1fr", gap:10, padding:"6px 0", position:"relative" }}>
              <div style={{ position:"absolute", left:-10, top:10, bottom:-6, width:1, background:"var(--line)", display:i===3?"none":"block" }}/>
              <div style={{ position:"absolute", left:-14, top:10, width:8, height:8, borderRadius:"50%", background:warn?"var(--caution)":"var(--pos)", border:"2px solid var(--surface)", boxSizing:"content-box" }}/>
              <div style={{ fontFamily:"var(--font-mono)", fontSize:11, color:"var(--ink-4)" }}>{t}</div>
              <div style={{ fontSize:12.5, color:"var(--ink-2)" }}>{e}</div>
            </div>
          ))}
        </div>
      </Slot>

      <Slot name="PolicyPanel · breach row" tier="T2">
        <div className="ops-breach-row sev-breach" style={{ maxWidth:560 }}>
          <div className="ops-breach-ic"><Icon name="risk" size={14}/></div>
          <div>
            <div className="ops-breach-label">Energy net exposure · 12% / 10%</div>
            <div className="ops-breach-meta">Hard breach · escalated · owner J. Park</div>
          </div>
          <div className="ops-breach-util">
            <div className="bar"><span style={{ width:"100%", background:"var(--breach)" }}/></div>
            <span className="num">120%</span>
            <span className="trend up">+1.9%</span>
          </div>
          <button className="btn ghost sm">Review →</button>
        </div>
      </Slot>

      <Slot name="IncidentCard · sev‑2" tier="T2">
        <div className="ops-incident" style={{ border:"1px solid var(--line)", borderRadius:"var(--r-md)", background:"var(--surface)", width:"100%", maxWidth:560 }}>
          <div className="ops-inc-head">
            <span className="ops-sev-tag sev-sev-2">sev-2</span>
            <span className="ops-inc-id">INC-2026-0419-003</span>
            <span className="ops-inc-status">investigating</span>
            <span className="ops-inc-age">14m ago</span>
          </div>
          <div className="ops-inc-title">Options flow feed — latency spike</div>
          <div className="ops-inc-meta">
            <span>Owner <b>M. Alvarez</b></span>
            <span>11 recs affected</span>
          </div>
        </div>
      </Slot>
    </section>
  );
}

// ─────── Tier 3 ───────
function Tier3Section() {
  return (
    <section id="tier3" className="ds-section">
      <h2>Tier 3 — advanced</h2>
      <p className="lead">
        Sparse, specialized surfaces. These should feel restrained — most workspaces never
        surface them. When they do appear, they earn their weight with information density.
      </p>

      <Slot name="CommandPalette · ⌘K" tier="T3" state="open">
        <div style={{
          width:"100%", maxWidth:460,
          background:"var(--surface)", border:"1px solid var(--line-strong)",
          borderRadius:"var(--r-lg)", boxShadow:"var(--shadow-lg)",
          overflow:"hidden"
        }}>
          <div style={{ display:"flex", alignItems:"center", gap:10, padding:"10px 14px", borderBottom:"1px solid var(--line)" }}>
            <Icon name="search" size={14}/>
            <span style={{ fontSize:13, color:"var(--ink-2)" }}>Jump to NVDA…</span>
            <span style={{ marginLeft:"auto", fontFamily:"var(--font-mono)", fontSize:10, color:"var(--ink-4)" }}>⌘K</span>
          </div>
          {[
            ["decision","REC‑2026‑0419‑NVDA‑L","Decision workspace"],
            ["compare","NVDA · engine comparison","Comparison"],
            ["replay","NVDA · replay 2026‑04‑15","Replay"],
          ].map(([ic,t,s],i)=>(
            <div key={i} style={{
              display:"flex", alignItems:"center", gap:10,
              padding:"8px 14px",
              background: i===0 ? "color-mix(in oklch, var(--primary) 8%, var(--surface))" : "transparent"
            }}>
              <Icon name={ic} size={14}/>
              <div style={{ minWidth:0, flex:1 }}>
                <div style={{ fontSize:12.5, color:"var(--ink)" }}>{t}</div>
                <div style={{ fontSize:10.5, color:"var(--ink-4)" }}>{s}</div>
              </div>
              {i===0 && <span style={{ fontFamily:"var(--font-mono)", fontSize:10, color:"var(--ink-4)" }}>↵</span>}
            </div>
          ))}
        </div>
      </Slot>

      <Slot name="Chart overlay · confidence band + events" tier="T3">
        <div style={{ width:"100%", maxWidth:560, height:160, position:"relative", background:"var(--surface)", border:"1px solid var(--line)", borderRadius:"var(--r-md)", padding:"16px 20px" }}>
          <svg viewBox="0 0 520 128" style={{ width:"100%", height:"100%" }}>
            <defs>
              <linearGradient id="ds-band" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stopColor="var(--primary)" stopOpacity="0.18"/>
                <stop offset="1" stopColor="var(--primary)" stopOpacity="0.02"/>
              </linearGradient>
            </defs>
            <path d="M0,80 C80,72 120,60 180,54 C240,48 300,58 360,48 C420,40 480,30 520,24 L520,128 L0,128 Z" fill="url(#ds-band)"/>
            <path d="M0,80 C80,72 120,60 180,54 C240,48 300,58 360,48 C420,40 480,30 520,24" stroke="var(--primary)" strokeWidth="1.5" fill="none"/>
            <circle cx="180" cy="54" r="4" fill="var(--caution)"/>
            <line x1="180" y1="24" x2="180" y2="54" stroke="var(--caution)" strokeDasharray="2 2" strokeWidth="1"/>
            <text x="186" y="30" fontSize="9" fill="var(--ink-3)" fontFamily="var(--font-mono)">earnings</text>
            <circle cx="360" cy="48" r="4" fill="var(--pos)"/>
          </svg>
        </div>
      </Slot>

      <Slot name="Watchlist · dense row" tier="T3">
        <table className="ov-table" style={{ maxWidth:640, width:"100%" }}>
          <thead><tr><th>Symbol</th><th>Last</th><th>Δ</th><th>Conf</th><th>Flag</th></tr></thead>
          <tbody>
            {[
              ["NVDA",942.18,"+1.2%",0.74,"semis cap"],
              ["AAPL",218.04,"−0.3%",0.71,""],
              ["MSFT",428.90,"+0.8%",0.62,"stale"],
              ["TSM",184.22,"+2.1%",0.66,""],
            ].map((r,i)=>(
              <tr key={i}>
                <td style={{fontWeight:500}}>{r[0]}</td>
                <td className="num">{r[1].toFixed(2)}</td>
                <td className={"num " + (r[2].startsWith("+")?"hl-pos":"hl-neg")}>{r[2]}</td>
                <td className="num">{r[3].toFixed(2)}</td>
                <td>{r[4] ? <span className="flag caution"><Icon name="info" size={10}/>{r[4]}</span> : <span style={{color:"var(--ink-4)"}}>—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Slot>
    </section>
  );
}

// ─────── Patterns ───────
function PatternsSection() {
  return (
    <section id="patterns" className="ds-section">
      <h2>Usage patterns</h2>
      <p className="lead">
        Not every combination is legal. These are the approved patterns for the most common decisions.
      </p>

      <div className="ds-subsection">
        <h3>Confidence trio — always three</h3>
        <div className="sub">Model · data quality · operational readiness. Never merged into a single score.</div>
        <MiniConfTrio/>
      </div>

      <div className="ds-subsection">
        <h3>Disagreement — high confidence dissent is a story</h3>
        <div className="sub">When engines disagree, the dissent is above the fold, not tucked in a tab.</div>
        <div style={{display:"flex",flexDirection:"column",gap:4,maxWidth:420}}>
          {[
            ["Momentum","LONG",0.82,"buy"],
            ["Quality","LONG",0.76,"buy"],
            ["Flow/options","SHORT",0.42,"sell"],
          ].map(([nm,st,c,cls],i)=>(
            <div key={i} style={{ display:"grid", gridTemplateColumns:"110px 60px 1fr 40px", alignItems:"center", gap:8, fontSize:12 }}>
              <span>{nm}</span>
              <span className={"ov-stance "+cls}>{st}</span>
              <div style={{height:5,background:"var(--surface-3)",borderRadius:999,overflow:"hidden"}}>
                <div style={{width:(c*100)+"%",height:"100%",background:st==="SHORT"?"var(--breach)":"var(--primary)"}}/>
              </div>
              <span className="num" style={{fontSize:11}}>{c.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="ds-subsection">
        <h3>Breach severity — three tiers</h3>
        <div className="sub">Approaching (caution) → breached (breach) → escalated (breach + owner + ops).</div>
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          <MiniAlert sev="caution" title="Semis 28.1% / 30%" desc="Approaching sector cap — promotion of NVDA would use 0.6% more."/>
          <MiniAlert sev="breach" title="Energy 12% / 10%" desc="Hard breach · J. Park owns resolution · incident INC-2026-0419-001."/>
        </div>
      </div>

      <div className="ds-callout pos" style={{marginTop:20}}>
        <b>Action accountability:</b> every decision emits a state transition
        (<code>published</code>, <code>deferred</code>, <code>monitored</code>, <code>challenged</code>)
        which appears in the audit log with actor, target, scope, and outcome.
      </div>
    </section>
  );
}

// ─────── States section ───────
function StatesSection() {
  return (
    <section id="states" className="ds-section">
      <h2>All states</h2>
      <p className="lead">
        Every Tier 1 component must support six states: default, loading, empty, degraded,
        error, permission‑limited. These examples use the RecommendationCard to illustrate.
      </p>

      <div className="ds-state-grid">
        <Slot name="RecCard" tier="T1" state="default">
          <MiniRecCard/>
        </Slot>

        <Slot name="RecCard" tier="T1" state="loading">
          <div className="ds-rec-card" style={{width:"100%"}}>
            <div className="head">
              <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                <div className="ds-skel" style={{ width:60, height:22 }}/>
                <div className="ds-skel" style={{ width:180, height:10 }}/>
              </div>
              <div className="ds-skel" style={{ width:52, height:20, borderRadius:4 }}/>
            </div>
            <div className="ds-skel" style={{ width:"100%", height:12 }}/>
            <div className="ds-skel" style={{ width:"88%", height:12 }}/>
            <div className="ds-skel" style={{ width:"100%", height:46, borderRadius:"var(--r-md)" }}/>
          </div>
        </Slot>

        <Slot name="RecCard" tier="T1" state="empty">
          <div className="ds-rec-card" style={{
            width:"100%",
            alignItems:"center",
            justifyContent:"center",
            borderStyle:"dashed",
            background:"transparent",
            boxShadow:"none",
            minHeight:200,
            color:"var(--ink-3)",
            textAlign:"center"
          }}>
            <Icon name="sparkle" size={20}/>
            <div style={{ fontSize:13, fontWeight:500, color:"var(--ink-2)" }}>No recommendation yet</div>
            <div style={{ fontSize:12, color:"var(--ink-4)", maxWidth:240 }}>
              Engines haven't converged. Rescore triggers on the next 15‑min cycle.
            </div>
          </div>
        </Slot>

        <Slot name="RecCard" tier="T1" state="degraded">
          <div className="ds-rec-card" style={{width:"100%"}}>
            <div className="head">
              <div><div className="tk">NVDA</div><div className="id">REC-…NVDA-L · v4</div></div>
              <span className="ov-stance hold">HOLD*</span>
            </div>
            <div style={{
              display:"flex", alignItems:"flex-start", gap:8,
              padding:"8px 10px",
              background:"var(--caution-soft)",
              border:"1px solid color-mix(in oklch, var(--caution) 30%, transparent)",
              borderRadius:"var(--r-sm)",
              color:"var(--caution-soft-ink)",
              fontSize:11.5,
              lineHeight:1.45
            }}>
              <Icon name="alert-triangle" size={13}/>
              <div>Flow/options engine degraded — confidence capped at 0.60. Stance reverts to HOLD until recovery.</div>
            </div>
            <MiniConfTrio model={0.60} data={0.72} ops={0.55}/>
          </div>
        </Slot>

        <Slot name="RecCard" tier="T1" state="error">
          <div className="ds-rec-card" style={{ width:"100%", borderColor:"color-mix(in oklch, var(--breach) 35%, var(--line))", background:"color-mix(in oklch, var(--breach) 4%, var(--surface))" }}>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <div style={{ color:"var(--breach-soft-ink)" }}><Icon name="risk" size={18}/></div>
              <div style={{ fontSize:13, fontWeight:500, color:"var(--breach-soft-ink)" }}>Failed to load recommendation</div>
            </div>
            <div style={{ fontSize:12, color:"var(--ink-2)", lineHeight:1.5 }}>
              Backend returned 503 · retry in 2s. If this persists, the rec engine health check may be failing.
            </div>
            <div style={{ display:"flex", gap:6 }}>
              <button className="btn ghost sm">Open incident</button>
              <button className="btn primary sm"><Icon name="replay" size={12}/> Retry</button>
            </div>
          </div>
        </Slot>

        <Slot name="RecCard" tier="T1" state="permission-limited">
          <div className="ds-rec-card" style={{ width:"100%" }}>
            <div className="head">
              <div><div className="tk">NVDA</div><div className="id">REC-…NVDA-L · v4</div></div>
              <span className="ov-stance buy">LONG</span>
            </div>
            <div className="thesis">Four engines align above 0.68 on Q4 momentum…</div>
            <MiniConfTrio/>
            <div style={{
              display:"flex", gap:8, padding:"8px 10px",
              background:"var(--surface-3)",
              borderRadius:"var(--r-sm)",
              fontSize:11.5, color:"var(--ink-3)",
              lineHeight:1.45
            }}>
              <Icon name="eye" size={13}/>
              <div>Read‑only view · you don't have approval rights for this desk.</div>
            </div>
          </div>
        </Slot>
      </div>
    </section>
  );
}

Object.assign(window, {
  Tier1Section, Tier2Section, Tier3Section, PatternsSection, StatesSection,
  MiniConfTrio, MiniRecCard, MiniAlert, Slot
});
