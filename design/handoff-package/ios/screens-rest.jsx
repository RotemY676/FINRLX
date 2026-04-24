// iOS screens part 2 — alerts, comparison, replay, watchlist, settings, notes

// ═════════════════════════════════════════════════════════════
// SCREEN 7 — Alerts inbox
// ═════════════════════════════════════════════════════════════
function S_Alerts({ dark = true }) {
  const t = useIOS(dark);
  const alerts = [
    { kind:"breach", sev:"high", title:"Semis sector nearing cap",
      body:"28.1% of 30% hard limit. NVDA promotion would add ~0.6%.",
      when:"3m ago", badge:"BREACH" },
    { kind:"freshness", sev:"mid", title:"Flow/options engine down‑weighted",
      body:"Data stale 14m. Confidence capped at 0.60 until recovery.",
      when:"18m ago", badge:"DATA" },
    { kind:"policy", sev:"mid", title:"Single‑name limit on NVDA",
      body:"Approaching 4.2% of 5.0% hard cap. Review on next edit.",
      when:"44m ago", badge:"POLICY" },
    { kind:"info", sev:"low", title:"Reuters feed recovered",
      body:"Backfilled 09:14 → 09:27. 11 recommendations re‑scored.",
      when:"1h ago", badge:"INFO" },
    { kind:"info", sev:"low", title:"Backtest #204 complete",
      body:"Momentum + quality · 5y IR 1.32 · ready for review.",
      when:"3h ago", badge:"INFO" },
  ];
  const sevColor = { high: t.red, mid: t.orange, low: t.ink3 };
  return (
    <IOSPhone dark={dark} label="iOS · Alerts inbox">
      <IOSNav title="Alerts" dark={dark} subtitle="5 new · 2 require action"
        trailing={<div style={{ color:t.blue, fontSize:16 }}>Edit</div>}/>

      {/* filter pills */}
      <div style={{ padding:"0 16px 12px", display:"flex", gap:6 }}>
        {["All · 5","Breach · 1","Policy · 1","Data · 1","Info · 2"].map((l,i)=>(
          <div key={i} style={{
            padding:"5px 10px", borderRadius:999, fontSize:12, fontWeight:500,
            background: i===0? t.blue : t.surface,
            color: i===0? "#fff" : t.ink2,
            border: i===0? "none" : `0.5px solid ${t.sep}`,
            whiteSpace:"nowrap",
          }}>{l}</div>
        ))}
      </div>

      <div style={{ padding:"0 16px 110px" }}>
        {alerts.map((a,i)=>(
          <div key={i} style={{
            background:t.surface, borderRadius:14, padding:14, marginBottom:10,
            border: `0.5px solid ${a.sev==="high"? t.red+"60" : t.sep}`,
            position:"relative",
          }}>
            <div style={{ display:"flex", alignItems:"flex-start", gap:10, marginBottom:6 }}>
              <div style={{
                width:28, height:28, borderRadius:14, flexShrink:0,
                background:`${sevColor[a.sev]}20`,
                display:"grid", placeItems:"center",
              }}>
                {a.sev==="high" && SF.breach(t.red, 16)}
                {a.sev==="mid" && SF.warning(t.orange, 16)}
                {a.sev==="low" && <div style={{width:6,height:6,borderRadius:3,background:t.blue}}/>}
              </div>
              <div style={{ flex:1 }}>
                <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:2 }}>
                  <span style={{ fontSize:15, fontWeight:600, color:t.ink }}>{a.title}</span>
                </div>
                <div style={{ fontSize:13, color:t.ink2, lineHeight:1.4 }}>{a.body}</div>
              </div>
            </div>
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginTop:8 }}>
              <div style={{ display:"flex", gap:6 }}>
                <span style={{
                  fontSize:10, fontWeight:700, padding:"2px 6px", borderRadius:3,
                  background:`${sevColor[a.sev]}20`, color:sevColor[a.sev], letterSpacing:0.4,
                }}>{a.badge}</span>
                <span style={{ fontSize:11, color:t.ink3, fontFamily:IOS.fontMono }}>{a.when}</span>
              </div>
              {a.sev === "high" && (
                <span style={{ fontSize:13, color:t.blue, fontWeight:500 }}>Review →</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <IOSTabBar dark={dark} active={3} tabs={[
        { label:"Today", icon:SF.house(t.ink3,24) },
        { label:"Decisions", icon:SF.decisions(t.ink3,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.ink3,24) },
        { label:"Alerts", icon:SF.bell(t.blue,24), badge:"3" },
        { label:"Me", icon:SF.person(t.ink3,24) },
      ]}/>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 8 — Engine comparison (condensed matrix)
// ═════════════════════════════════════════════════════════════
function S_Compare({ dark = true }) {
  const t = useIOS(dark);
  const engines = [
    { n:"Momentum", w:0.28, stance:"LONG", c:0.82, col:t.green },
    { n:"Quality", w:0.22, stance:"LONG", c:0.76, col:t.green },
    { n:"Earnings rev.", w:0.18, stance:"LONG", c:0.71, col:t.green },
    { n:"Value", w:0.18, stance:"HOLD", c:0.48, col:t.ink3 },
    { n:"Flow/options", w:0.14, stance:"LONG", c:0.54, col:t.green },
  ];
  return (
    <IOSPhone dark={dark} label="iOS · Engine comparison">
      <IOSNav title="Compare" dark={dark}
        subtitle="NVDA · 4 of 5 align · dispersion 0.37"
        trailing={<div style={{ color:t.blue, fontSize:16 }}>Replay</div>}
      />

      {/* Summary card */}
      <div style={{ margin:"0 16px 16px", padding:14, borderRadius:14, background:t.surface, border:`0.5px solid ${t.sep}` }}>
        <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:8 }}>
          Composite stance
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:10 }}>
          <div style={{
            padding:"6px 12px", borderRadius:6, background:`${t.green}18`,
            color:t.green, fontWeight:700, letterSpacing:0.5, fontSize:15,
          }}>LONG</div>
          <span style={{ fontFamily:IOS.fontMono, fontSize:14, color:t.ink, fontWeight:600 }}>
            conf 0.74
          </span>
          <span style={{ fontSize:12, color:t.ink3, marginLeft:"auto" }}>weighted vote</span>
        </div>

        {/* Stacked bar */}
        <div style={{ height:28, display:"flex", borderRadius:6, overflow:"hidden" }}>
          {engines.map((e,i)=>(
            <div key={i} style={{
              width:(e.w*100)+"%", background:e.col,
              display:"grid", placeItems:"center", opacity: e.stance==="HOLD"? 0.4 : 1,
              borderRight: i<engines.length-1? `1px solid ${t.bg}` : 0,
            }}>
              <span style={{ fontSize:10, color:"#fff", fontWeight:700 }}>
                {(e.w*100).toFixed(0)}
              </span>
            </div>
          ))}
        </div>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:t.ink3, marginTop:6 }}>
          <span>4 LONG · 72% weight</span>
          <span>1 HOLD · 18%</span>
        </div>
      </div>

      {/* Engine rows */}
      <div style={{ fontSize:13, color:t.ink3, textTransform:"uppercase",
        padding:"0 32px 6px", letterSpacing:0.06,
      }}>Per engine</div>
      <div style={{ margin:"0 16px 16px", background:t.surface, borderRadius:14, overflow:"hidden" }}>
        {engines.map((e,i)=>(
          <div key={i} style={{
            padding:"12px 14px",
            borderBottom: i<engines.length-1? `0.5px solid ${t.sep}` : 0,
            display:"grid", gridTemplateColumns:"1fr 64px 54px", gap:10, alignItems:"center",
          }}>
            <div>
              <div style={{ fontSize:15, color:t.ink, fontWeight:500 }}>{e.n}</div>
              <div style={{ fontSize:11, color:t.ink3, marginTop:1 }}>weight {(e.w*100).toFixed(0)}%</div>
            </div>
            <div style={{ textAlign:"center" }}>
              <span style={{
                fontSize:11, fontWeight:700, padding:"3px 8px", borderRadius:4,
                background: `${e.col}20`, color: e.col, letterSpacing:0.5,
              }}>{e.stance}</span>
            </div>
            <div style={{ textAlign:"right" }}>
              <div style={{ fontFamily:IOS.fontMono, fontSize:14, color:t.ink, fontWeight:600 }}>{e.c.toFixed(2)}</div>
              <div style={{ fontSize:10, color:t.ink3 }}>conf</div>
            </div>
          </div>
        ))}
      </div>

      {/* Resolution guidance */}
      <div style={{ margin:"0 16px 120px", padding:14, borderRadius:14,
        background:`${t.blue}12`, border:`0.5px solid ${t.blue}30`,
      }}>
        <div style={{ fontSize:11, color:t.blue, textTransform:"uppercase", letterSpacing:0.5, fontWeight:600, marginBottom:6 }}>
          Resolution guidance
        </div>
        <div style={{ fontSize:13.5, color:t.ink2, lineHeight:1.45 }}>
          Value dissents on valuation (P/E 42x). Historical resolution: value lags
          6‑8w in momentum regimes; composite LONG has resolved correctly in 7 of
          9 similar disagreements since 2023.
        </div>
      </div>

      <IOSTabBar dark={dark} active={2} tabs={[
        { label:"Today", icon:SF.house(t.ink3,24) },
        { label:"Decisions", icon:SF.decisions(t.ink3,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.blue,24) },
        { label:"Alerts", icon:SF.bell(t.ink3,24), badge:"3" },
        { label:"Me", icon:SF.person(t.ink3,24) },
      ]}/>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 9 — Replay (time travel)
// ═════════════════════════════════════════════════════════════
function S_Replay({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Replay">
      <div style={{ paddingTop:4 }}>
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"2px 16px 8px",
        }}>
          <div style={{ display:"flex", alignItems:"center", color:t.blue, fontSize:17 }}>
            {SF.chev(t.blue,"left")}<span style={{ marginLeft:2 }}>Decision</span>
          </div>
          <div style={{ color:t.blue, fontSize:17, fontWeight:600 }}>Done</div>
        </div>
      </div>

      <div style={{ padding:"0 20px 14px" }}>
        <div style={{ fontFamily:IOS.fontDisplay, fontSize:28, fontWeight:700, letterSpacing:-0.3 }}>Replay</div>
        <div style={{ fontSize:14, color:t.ink3, marginTop:2 }}>NVDA · v1 → v4 · 12d timeline</div>
      </div>

      {/* Chart area */}
      <div style={{ margin:"0 16px 16px", padding:"14px 12px", borderRadius:14,
        background:t.surface, border:`0.5px solid ${t.sep}`,
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
          <div>
            <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Snapshot · 12 Apr 14:22</div>
            <div style={{ fontSize:16, fontWeight:600, color:t.ink }}>Confidence 0.62</div>
          </div>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Stance</div>
            <div style={{
              display:"inline-block", padding:"2px 8px", borderRadius:4,
              background:`${t.orange}20`, color:t.orange, fontSize:12, fontWeight:700, letterSpacing:0.5,
            }}>HOLD</div>
          </div>
        </div>

        {/* Mini chart with marker */}
        <svg viewBox="0 0 300 90" style={{ width:"100%", height:110 }} preserveAspectRatio="none">
          <path d="M0 70 L30 68 L60 72 L90 55 L120 50 L150 42 L180 30 L210 32 L240 22 L270 18 L300 12"
            fill="none" stroke={t.blue} strokeWidth="2"/>
          {/* Event markers */}
          {[
            {x:30,l:"v1"},{x:90,l:"v2"},{x:180,l:"v3"},{x:300,l:"v4"}
          ].map((m,i)=>(
            <g key={i}>
              <line x1={m.x} y1="0" x2={m.x} y2="90" stroke={t.ink4} strokeDasharray="2,3" strokeWidth="1"/>
              <circle cx={m.x} cy={[70,55,30,12][i]} r="4" fill={i===1? t.orange : t.blue}/>
              <text x={m.x} y="88" textAnchor="middle" fontSize="10" fill={t.ink3} fontFamily={IOS.fontMono}>{m.l}</text>
            </g>
          ))}
          {/* Current marker */}
          <line x1="90" y1="0" x2="90" y2="90" stroke={t.orange} strokeWidth="1.5"/>
        </svg>
      </div>

      {/* Scrub timeline */}
      <div style={{ margin:"0 16px 18px" }}>
        <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4, marginBottom:8, padding:"0 4px" }}>
          Scrub
        </div>
        <div style={{ position:"relative", height:36, background:t.surface, borderRadius:10, padding:"0 12px",
          border:`0.5px solid ${t.sep}`, display:"flex", alignItems:"center",
        }}>
          <div style={{ height:3, background:t.surface3, width:"100%", borderRadius:2, position:"relative" }}>
            <div style={{ height:"100%", width:"30%", background:t.blue, borderRadius:2 }}/>
            <div style={{
              position:"absolute", left:"calc(30% - 11px)", top:-10,
              width:22, height:22, borderRadius:11, background:"#fff",
              boxShadow:"0 2px 6px rgba(0,0,0,0.3)",
            }}/>
          </div>
        </div>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:t.ink3, marginTop:4, padding:"0 4px", fontFamily:IOS.fontMono }}>
          <span>7 Apr</span><span>12 Apr 14:22</span><span>19 Apr</span>
        </div>
      </div>

      {/* State at snapshot */}
      <Group dark={dark} header="State at this moment">
        {[
          { k:"Confidence", v:"0.62", s:"−0.12 from latest" },
          { k:"Weight (proposed)", v:"+2.1%", s:"−2.1% from latest" },
          { k:"Engines aligned", v:"3 / 5", s:"Momentum, Quality, Flow" },
          { k:"Regime", v:"Risk‑off rotation", s:"switched at 10:18" },
        ].map((r,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:14.5, color:t.ink }}>{r.k}</span>
              <span style={{ fontFamily:IOS.fontMono, fontSize:14, color:t.ink, fontWeight:600 }}>{r.v}</span>
            </div>
            <div style={{ fontSize:12, color:t.ink3, marginTop:2 }}>{r.s}</div>
          </Row>
        ))}
      </Group>

      <div style={{ height:20 }}/>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 10 — Watchlist / saved views
// ═════════════════════════════════════════════════════════════
function S_Watchlist({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Watchlist & views">
      <IOSNav title="Watchlist" dark={dark}
        subtitle="3 lists · 2 saved views"
        trailing={<div style={{ width:32,height:32,borderRadius:16,background:t.surface3,display:"grid",placeItems:"center" }}>{SF.plus(t.blue)}</div>}
      />

      {/* Saved views */}
      <Group dark={dark} header="Saved views">
        {[
          { nm:"Momentum leaders", ct:"24 names · refreshed 8m", ic:t.green },
          { nm:"Breach watch", ct:"2 names · 1 flagged", ic:t.red },
          { nm:"Earnings this week", ct:"11 names", ic:t.blue },
        ].map((v,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", alignItems:"center", gap:12 }}>
              <div style={{
                width:30, height:30, borderRadius:8,
                background:`${v.ic}22`, display:"grid", placeItems:"center", flexShrink:0,
              }}>
                <div style={{ width:8, height:8, borderRadius:4, background:v.ic }}/>
              </div>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:15, color:t.ink, fontWeight:500 }}>{v.nm}</div>
                <div style={{ fontSize:12, color:t.ink3, marginTop:1 }}>{v.ct}</div>
              </div>
              {SF.chev(t.ink4)}
            </div>
          </Row>
        ))}
      </Group>

      {/* Main watchlist */}
      <div style={{ fontSize:13, color:t.ink3, textTransform:"uppercase",
        padding:"0 32px 6px", letterSpacing:0.06,
      }}>My watchlist · 8 names</div>
      <div style={{ margin:"0 16px 16px", background:t.surface, borderRadius:14, overflow:"hidden" }}>
        {[
          { tk:"NVDA", nm:"NVIDIA", px:"$892.40", d:"+2.4%", pos:true, flag:"REC" },
          { tk:"MSFT", nm:"Microsoft", px:"$412.18", d:"−0.8%", pos:false, flag:"TRIM" },
          { tk:"META", nm:"Meta", px:"$498.02", d:"+0.3%", pos:true, flag:"SPLIT" },
          { tk:"AAPL", nm:"Apple", px:"$224.31", d:"+0.1%", pos:true, flag:"STALE" },
          { tk:"XOM", nm:"Exxon", px:"$108.77", d:"−3.1%", pos:false, flag:"SHORT" },
          { tk:"TSM", nm:"TSMC", px:"$188.90", d:"+1.2%", pos:true, flag:"—" },
        ].map((r,i,a)=>(
          <div key={i} style={{
            padding:"11px 14px", display:"grid",
            gridTemplateColumns:"1fr auto auto",
            gap:12, alignItems:"center",
            borderBottom: i<a.length-1 ? `0.5px solid ${t.sep}` : 0,
          }}>
            <div>
              <div style={{ fontSize:15, fontWeight:600, color:t.ink, fontFamily:IOS.fontDisplay, letterSpacing:-0.1 }}>{r.tk}</div>
              <div style={{ fontSize:12, color:t.ink3 }}>{r.nm}</div>
            </div>
            <div style={{ textAlign:"right" }}>
              <div style={{ fontFamily:IOS.fontMono, fontSize:14, color:t.ink, fontWeight:500 }}>{r.px}</div>
              <div style={{ fontFamily:IOS.fontMono, fontSize:12, color: r.pos? t.green : t.red }}>{r.d}</div>
            </div>
            <div style={{ minWidth:48, textAlign:"right" }}>
              {r.flag !== "—" ? (
                <span style={{
                  fontSize:10, fontWeight:700, padding:"2px 6px", borderRadius:3,
                  background: t.surface3, color: t.ink3, letterSpacing:0.3,
                }}>{r.flag}</span>
              ) : (
                <span style={{ color:t.ink4 }}>—</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ height: 120 }}/>
      <IOSTabBar dark={dark} active={1} tabs={[
        { label:"Today", icon:SF.house(t.ink3,24) },
        { label:"Decisions", icon:SF.decisions(t.blue,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.ink3,24) },
        { label:"Alerts", icon:SF.bell(t.ink3,24), badge:"3" },
        { label:"Me", icon:SF.person(t.ink3,24) },
      ]}/>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 11 — Notes / thesis annotations
// ═════════════════════════════════════════════════════════════
function S_Notes({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Notes & annotations">
      <div style={{ paddingTop:4 }}>
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"2px 16px 8px",
        }}>
          <div style={{ display:"flex", alignItems:"center", color:t.blue, fontSize:17 }}>
            {SF.chev(t.blue,"left")}<span style={{ marginLeft:2 }}>NVDA</span>
          </div>
          <div style={{ color:t.blue, fontSize:17, fontWeight:600 }}>Post</div>
        </div>
      </div>

      <div style={{ padding:"0 20px 14px" }}>
        <div style={{ fontFamily:IOS.fontDisplay, fontSize:28, fontWeight:700, letterSpacing:-0.3 }}>Notes</div>
        <div style={{ fontSize:13, color:t.ink3, marginTop:2 }}>3 threads · 7 messages</div>
      </div>

      {/* Attach context */}
      <div style={{ margin:"0 16px 12px", padding:"10px 12px", borderRadius:10,
        background:t.surface, border:`0.5px solid ${t.sep}`,
        display:"flex", alignItems:"center", gap:10,
      }}>
        <div style={{ width:6, height:30, borderRadius:3, background:t.blue }}/>
        <div style={{ flex:1 }}>
          <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Attached to</div>
          <div style={{ fontSize:13, color:t.ink }}>REC‑2026‑0419‑NVDA‑L · v4 · Evidence #3</div>
        </div>
      </div>

      {/* Thread */}
      <div style={{ padding:"0 16px 120px" }}>
        {[
          { who:"J. Park", whoC:t.indigo, when:"2h ago",
            body:"Quality engine weight looks high. Haven't we been leaning on momentum this cycle? Is the 0.22 fair if they agree on stance?" },
          { who:"R. Mikhailov", whoC:t.blue, when:"1h ago", you:true,
            body:"Quality is anchoring the thesis when momentum cools. Keeping at 0.22 for the 3M horizon. We can revisit if IR drifts." },
          { who:"M. Alvarez", whoC:t.green, when:"32m ago",
            body:"Attached backtest #204 — momentum+quality IR 1.32 over 5y. Value dissent resolved in 7 of 9 cases." },
        ].map((n,i)=>(
          <div key={i} style={{
            background: n.you? `${t.blue}14` : t.surface,
            borderRadius:14, padding:14, marginBottom:10,
            border: n.you? `0.5px solid ${t.blue}30` : `0.5px solid ${t.sep}`,
          }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:6 }}>
              <div style={{
                width:26, height:26, borderRadius:13, background:`${n.whoC}30`,
                color:n.whoC, display:"grid", placeItems:"center",
                fontSize:11, fontWeight:700,
              }}>{n.who.split(" ").map(s=>s[0]).join("")}</div>
              <span style={{ fontSize:14, color:t.ink, fontWeight:600 }}>{n.who}</span>
              {n.you && <span style={{ fontSize:10, color:t.blue, fontWeight:600, padding:"1px 5px", background:`${t.blue}20`, borderRadius:3 }}>YOU</span>}
              <span style={{ fontSize:11, color:t.ink3, fontFamily:IOS.fontMono, marginLeft:"auto" }}>{n.when}</span>
            </div>
            <div style={{ fontSize:14, color:t.ink2, lineHeight:1.5 }}>{n.body}</div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div style={{
        position:"absolute", bottom:34, left:0, right:0, padding:"10px 12px 14px",
        background: dark? "rgba(20,20,22,0.92)" : "rgba(255,255,255,0.92)",
        backdropFilter:"saturate(180%) blur(20px)",
        WebkitBackdropFilter:"saturate(180%) blur(20px)",
        borderTop:`0.5px solid ${t.sep}`,
        display:"flex", gap:8, alignItems:"center",
      }}>
        <div style={{
          width:32, height:32, borderRadius:16, background:t.surface3,
          display:"grid", placeItems:"center", flexShrink:0,
        }}>{SF.plus(t.blue)}</div>
        <div style={{
          flex:1, background:t.surface2, borderRadius:18, padding:"8px 14px",
          fontSize:14, color:t.ink3, minHeight:20,
        }}>Reply to thread…</div>
      </div>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 12 — Settings / profile / team
// ═════════════════════════════════════════════════════════════
function S_Settings({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Settings">
      <IOSNav title="Me" dark={dark} subtitle="R. Mikhailov · Portfolio Manager"/>

      {/* Profile card */}
      <div style={{
        margin:"0 16px 20px", padding:16, borderRadius:16,
        background:`linear-gradient(135deg, ${t.blue}15, ${t.indigo}08)`,
        border:`0.5px solid ${t.sep}`,
        display:"flex", alignItems:"center", gap:14,
      }}>
        <div style={{
          width:56, height:56, borderRadius:28,
          background:t.blue, color:"#fff",
          display:"grid", placeItems:"center",
          fontSize:22, fontWeight:600, fontFamily:IOS.fontDisplay,
        }}>RM</div>
        <div style={{ flex:1 }}>
          <div style={{ fontSize:17, fontWeight:600, color:t.ink }}>Rivka Mikhailov</div>
          <div style={{ fontSize:13, color:t.ink3 }}>Macro / Quant · Team Alpha</div>
          <div style={{ fontSize:12, color:t.ink3, marginTop:4, fontFamily:IOS.fontMono }}>
            Seat 14 of 18 · Read+Edit+Promote
          </div>
        </div>
      </div>

      <Group dark={dark} header="Preferences">
        {[
          { k:"Appearance", v:"Dark" },
          { k:"Density", v:"Default" },
          { k:"Default universe", v:"US LargeCap" },
          { k:"Default horizon", v:"3M" },
        ].map((s,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:15, color:t.ink }}>{s.k}</span>
              <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                <span style={{ fontSize:14, color:t.ink3 }}>{s.v}</span>
                {SF.chev(t.ink4)}
              </div>
            </div>
          </Row>
        ))}
      </Group>

      <Group dark={dark} header="Security">
        {[
          { k:"Face ID for promote", toggle:true },
          { k:"Biometric for reads", toggle:false },
          { k:"Auto-lock", v:"2 minutes" },
        ].map((s,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:15, color:t.ink }}>{s.k}</span>
              {s.toggle !== undefined ? (
                <div style={{
                  width:51, height:31, borderRadius:16,
                  background: s.toggle? t.green : t.surface3, padding:2,
                  display:"flex", alignItems:"center",
                }}>
                  <div style={{
                    width:27, height:27, borderRadius:14, background:"#fff",
                    marginLeft: s.toggle? 20 : 0,
                    boxShadow:"0 2px 4px rgba(0,0,0,0.2)",
                  }}/>
                </div>
              ) : (
                <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                  <span style={{ fontSize:14, color:t.ink3 }}>{s.v}</span>
                  {SF.chev(t.ink4)}
                </div>
              )}
            </div>
          </Row>
        ))}
      </Group>

      <Group dark={dark} header="Team" footer="Your actions are visible to your team lead (J. Park).">
        {[
          { k:"Team Alpha", v:"7 members" },
          { k:"Publication queue", v:"Team · 12" },
          { k:"Activity visibility", v:"Team only" },
        ].map((s,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:15, color:t.ink }}>{s.k}</span>
              <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                <span style={{ fontSize:14, color:t.ink3 }}>{s.v}</span>
                {SF.chev(t.ink4)}
              </div>
            </div>
          </Row>
        ))}
      </Group>

      <div style={{ padding:"6px 16px 110px" }}>
        <button style={{
          width:"100%", padding:14, borderRadius:14, border:0,
          background:t.surface, color:t.red, fontSize:16, fontWeight:500,
          fontFamily:"inherit",
        }}>Sign out</button>
      </div>

      <IOSTabBar dark={dark} active={4} tabs={[
        { label:"Today", icon:SF.house(t.ink3,24) },
        { label:"Decisions", icon:SF.decisions(t.ink3,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.ink3,24) },
        { label:"Alerts", icon:SF.bell(t.ink3,24), badge:"3" },
        { label:"Me", icon:SF.person(t.blue,24) },
      ]}/>
    </IOSPhone>
  );
}

Object.assign(window, { S_Alerts, S_Compare, S_Replay, S_Watchlist, S_Notes, S_Settings });
