// iOS screens — QuantPipeline mobile app
// All screens as functions returning phone-sized content. Used inside DesignCanvas.

const { useState: useStateIOS } = React;

// Helper: section card (grouped list style)
function Group({ header, footer, children, dark }) {
  const t = useIOS(dark);
  return (
    <div style={{ marginBottom: 22 }}>
      {header && (
        <div style={{
          fontSize: 13, color: t.ink3, textTransform: "uppercase",
          padding: "0 32px 6px", letterSpacing: 0.06,
        }}>{header}</div>
      )}
      <div style={{
        background: t.surface, borderRadius: 14, margin: "0 16px",
        overflow: "hidden",
      }}>{children}</div>
      {footer && (
        <div style={{
          fontSize: 12, color: t.ink3, padding: "6px 32px", lineHeight: 1.35,
        }}>{footer}</div>
      )}
    </div>
  );
}

function Row({ children, dark, last }) {
  const t = useIOS(dark);
  return (
    <div style={{
      padding: "11px 16px", position: "relative",
      borderBottom: last ? 0 : `0.5px solid ${t.sep}`,
    }}>{children}</div>
  );
}

function Pill({ children, bg, color, size = 11 }) {
  return (
    <span style={{
      background: bg, color, fontSize: size, fontWeight: 600,
      padding: "2px 7px", borderRadius: 4, letterSpacing: 0.3,
      textTransform: "uppercase", display: "inline-block", lineHeight: 1.5,
    }}>{children}</span>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 1 — Today / triage (variation A: card list)
// ═════════════════════════════════════════════════════════════
function S_TodayA({ dark = true }) {
  const t = useIOS(dark);
  const recs = [
    { tk:"NVDA", nm:"NVIDIA Corp", stance:"buy", conf:0.74, ed:"+4.8%", age:"12m", status:"fresh",
      reason:"Momentum accelerating · EPS revisions +4.8%" },
    { tk:"MSFT", nm:"Microsoft", stance:"trim", conf:0.62, ed:"−1.8%", age:"8m", status:"provisional",
      reason:"Azure deceleration · relative momentum fading" },
    { tk:"XOM", nm:"Exxon Mobil", stance:"sell", conf:0.68, ed:"−3.1%", age:"22m", status:"fresh",
      reason:"Crude regime shift · margin compression" },
    { tk:"META", nm:"Meta Platforms", stance:"hold", conf:0.58, ed:"+0.9%", age:"3m", status:"pending",
      reason:"Engines split 3/5 · awaiting earnings" },
  ];
  const stanceMap = {
    buy:{bg:"rgba(48,209,88,0.15)",c:t.green,l:"LONG"},
    sell:{bg:"rgba(255,69,58,0.15)",c:t.red,l:"SHORT"},
    trim:{bg:"rgba(255,159,10,0.15)",c:t.orange,l:"TRIM"},
    hold:{bg:t.surface3,c:t.ink2,l:"HOLD"},
  };
  return (
    <IOSPhone dark={dark} label="iOS · Today · A (card list)">
      <IOSNav
        title="Today"
        subtitle="Monday · 19 April · 5 need attention"
        dark={dark}
        trailing={<>
          <div style={{
            width:32,height:32,borderRadius:16,background:t.surface3,
            display:"grid",placeItems:"center",
          }}>{SF.filter(t.blue)}</div>
          <div style={{
            width:32,height:32,borderRadius:16,background:t.surface3,
            display:"grid",placeItems:"center",fontSize:13,fontWeight:700,color:t.ink,
          }}>RM</div>
        </>}
      />
      {/* Scope chip strip */}
      <div style={{ padding:"0 16px 12px", display:"flex", gap:6, overflow:"hidden" }}>
        {["All · 5","Fresh · 3","Flagged · 2","Watched"].map((l,i)=>(
          <div key={i} style={{
            padding:"6px 12px", borderRadius:999, fontSize:13, fontWeight:500,
            background: i===0? t.blue : t.surface,
            color: i===0? "#fff" : t.ink2,
            border: i===0? "none" : `0.5px solid ${t.sep}`,
          }}>{l}</div>
        ))}
      </div>
      {/* Briefing banner */}
      <div style={{
        margin:"0 16px 14px", padding:14, borderRadius:14,
        background: dark ? "rgba(10,132,255,0.14)" : "rgba(10,132,255,0.08)",
        border: `0.5px solid ${dark?"rgba(10,132,255,0.3)":"rgba(10,132,255,0.18)"}`,
      }}>
        <div style={{ fontSize:12, color:t.blue, fontWeight:600, textTransform:"uppercase", letterSpacing:0.5, marginBottom:4 }}>
          Morning briefing
        </div>
        <div style={{ fontSize:14, color:t.ink, lineHeight:1.4 }}>
          Regime remains <b>risk‑on · late‑cycle</b>. Semis approaching <b>28.1%/30%</b> sector cap.
        </div>
      </div>

      {/* Rec list */}
      <div style={{ padding:"0 16px 100px" }}>
        {recs.map((r,i)=>{
          const sm = stanceMap[r.stance];
          const edPos = r.ed.startsWith("+");
          return (
            <div key={i} style={{
              background:t.surface, borderRadius:14, padding:14, marginBottom:10,
              border:`0.5px solid ${t.sep}`,
            }}>
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:6 }}>
                <div style={{
                  fontFamily:IOS.fontDisplay, fontSize:22, fontWeight:600,
                  color:t.ink, letterSpacing:-0.3,
                }}>{r.tk}</div>
                <div style={{ fontSize:13, color:t.ink3, flex:1 }}>{r.nm}</div>
                <Pill bg={sm.bg} color={sm.c}>{sm.l}</Pill>
              </div>
              <div style={{ fontSize:13.5, color:t.ink2, lineHeight:1.4, marginBottom:10 }}>
                {r.reason}
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:14, fontFamily:IOS.fontMono, fontSize:12 }}>
                <div>
                  <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Conf</div>
                  <div style={{ color:t.ink, fontWeight:600 }}>{r.conf.toFixed(2)}</div>
                </div>
                <div>
                  <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Expected</div>
                  <div style={{ color: edPos? t.green : t.red, fontWeight:600 }}>{r.ed}</div>
                </div>
                <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:6, color:t.ink3 }}>
                  {r.status==="fresh" && SF.fresh(t.green,14)}
                  {r.status==="provisional" && SF.warning(t.orange,14)}
                  {r.status==="pending" && <span style={{width:8,height:8,borderRadius:4,background:t.ink3,display:"inline-block"}}/>}
                  <span style={{ fontSize:12 }}>{r.age}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <IOSTabBar dark={dark} active={0} tabs={[
        { label:"Today", icon:SF.house(t.blue,24) },
        { label:"Decisions", icon:SF.decisions(t.ink3,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.ink3,24) },
        { label:"Alerts", icon:SF.bell(t.ink3,24), badge:"3" },
        { label:"Me", icon:SF.person(t.ink3,24) },
      ]}/>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 2 — Today / triage (variation B: stack ranked)
// ═════════════════════════════════════════════════════════════
function S_TodayB({ dark = true }) {
  const t = useIOS(dark);
  const recs = [
    { tk:"XOM", stance:"SHORT", conf:0.68, ed:-3.1, why:"Crude regime shift", flag:"BREACH", flagC:t.red },
    { tk:"NVDA", stance:"LONG", conf:0.74, ed:4.8, why:"Momentum + earnings", flag:"FRESH", flagC:t.green },
    { tk:"MSFT", stance:"TRIM", conf:0.62, ed:-1.8, why:"Azure decel", flag:"WATCH", flagC:t.orange },
    { tk:"META", stance:"HOLD", conf:0.58, ed:0.9, why:"Engines split 3/5", flag:"SPLIT", flagC:t.indigo },
    { tk:"AAPL", stance:"LONG", conf:0.71, ed:2.2, why:"Services growth", flag:"STALE", flagC:t.orange },
  ];
  return (
    <IOSPhone dark={dark} label="iOS · Today · B (stack ranked)">
      <IOSNav
        title="Today"
        subtitle="Ranked by conviction × freshness"
        dark={dark}
        trailing={<>
          <div style={{
            width:32,height:32,borderRadius:16,background:t.surface3,
            display:"grid",placeItems:"center",
          }}>{SF.ellipsis(t.blue)}</div>
        </>}
      />
      {/* Portfolio summary card */}
      <div style={{ padding:"0 16px 16px" }}>
        <div style={{
          background: t.surface, borderRadius: 16, padding: 16,
          border: `0.5px solid ${t.sep}`,
        }}>
          <div style={{ display:"flex", justifyContent:"space-between", marginBottom:14 }}>
            <div>
              <div style={{ fontSize:12, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>AUM</div>
              <div style={{ fontFamily:IOS.fontDisplay, fontSize:26, fontWeight:600, letterSpacing:-0.3 }}>$2.84B</div>
              <div style={{ fontSize:12, color:t.red, fontFamily:IOS.fontMono, marginTop:2 }}>−0.18% intraday</div>
            </div>
            <div style={{ textAlign:"right" }}>
              <div style={{ fontSize:12, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>Regime</div>
              <div style={{ fontSize:15, fontWeight:600, color:t.ink }}>Risk‑on</div>
              <div style={{ fontSize:12, color:t.ink3 }}>late‑cycle · 0.78</div>
            </div>
          </div>
          <div style={{ display:"flex", gap:8 }}>
            {[
              { k:"Queue", v:"7", c:t.blue },
              { k:"Fresh", v:"94%", c:t.green },
              { k:"Breach", v:"2", c:t.red },
            ].map((kpi,i)=>(
              <div key={i} style={{
                flex:1, padding:"8px 10px", borderRadius:10,
                background: t.surface2,
              }}>
                <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>{kpi.k}</div>
                <div style={{ fontSize:18, fontWeight:600, color:kpi.c, fontFamily:IOS.fontDisplay }}>{kpi.v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ fontSize:13, color:t.ink3, textTransform:"uppercase",
        padding:"0 32px 6px", letterSpacing:0.06,
      }}>Need attention · 5</div>

      <div style={{ margin:"0 16px 100px", background:t.surface, borderRadius:14, overflow:"hidden" }}>
        {recs.map((r,i)=>{
          const edPos = r.ed > 0;
          const stanceC = r.stance==="LONG"? t.green : r.stance==="SHORT"? t.red : r.stance==="TRIM"? t.orange : t.ink2;
          return (
            <div key={i} style={{
              display:"grid", gridTemplateColumns:"22px 1fr auto auto",
              gap:10, alignItems:"center",
              padding:"12px 14px",
              borderBottom: i<recs.length-1 ? `0.5px solid ${t.sep}` : 0,
            }}>
              <div style={{ fontSize:11, fontFamily:IOS.fontMono, color:t.ink3 }}>{i+1}</div>
              <div>
                <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                  <span style={{ fontFamily:IOS.fontDisplay, fontSize:17, fontWeight:600 }}>{r.tk}</span>
                  <span style={{ fontSize:11, color:stanceC, fontWeight:700, letterSpacing:0.4 }}>{r.stance}</span>
                </div>
                <div style={{ fontSize:12, color:t.ink3, marginTop:1 }}>{r.why}</div>
              </div>
              <div style={{ textAlign:"right" }}>
                <div style={{ fontFamily:IOS.fontMono, fontSize:13, fontWeight:600, color: edPos?t.green:t.red }}>
                  {edPos?"+":""}{r.ed}%
                </div>
                <div style={{ fontSize:10.5, color:t.ink3, fontFamily:IOS.fontMono }}>c {r.conf.toFixed(2)}</div>
              </div>
              <div style={{
                fontSize:9.5, fontWeight:700, padding:"2px 6px", borderRadius:3,
                background: `${r.flagC}20`, color: r.flagC, letterSpacing:0.3,
              }}>{r.flag}</div>
            </div>
          );
        })}
      </div>

      <IOSTabBar dark={dark} active={0} tabs={[
        { label:"Today", icon:SF.house(t.blue,24) },
        { label:"Decisions", icon:SF.decisions(t.ink3,24), badge:"12" },
        { label:"Compare", icon:SF.compare(t.ink3,24) },
        { label:"Alerts", icon:SF.bell(t.ink3,24), badge:"3" },
        { label:"Me", icon:SF.person(t.ink3,24) },
      ]}/>
    </IOSPhone>
  );
}

Object.assign(window, { S_TodayA, S_TodayB, Group, Row, Pill });
