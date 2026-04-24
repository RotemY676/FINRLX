// iPad screen — master-detail layout for Decision + Today split view

function S_iPad({ dark = true }) {
  const t = useIOS(dark);
  const recs = [
    { tk:"NVDA", nm:"NVIDIA", stance:"LONG", conf:0.74, ed:"+4.8%", sel:true, c:t.green, status:"fresh" },
    { tk:"MSFT", nm:"Microsoft", stance:"TRIM", conf:0.62, ed:"−1.8%", c:t.orange, status:"provisional" },
    { tk:"XOM", nm:"Exxon", stance:"SHORT", conf:0.68, ed:"−3.1%", c:t.red, status:"fresh" },
    { tk:"META", nm:"Meta", stance:"HOLD", conf:0.58, ed:"+0.9%", c:t.ink3, status:"pending" },
    { tk:"AAPL", nm:"Apple", stance:"LONG", conf:0.71, ed:"+2.2%", c:t.green, status:"stale" },
    { tk:"TSM", nm:"TSMC", stance:"LONG", conf:0.66, ed:"+1.9%", c:t.green, status:"fresh" },
    { tk:"JPM", nm:"JPMorgan", stance:"HOLD", conf:0.55, ed:"+0.4%", c:t.ink3, status:"pending" },
  ];

  return (
    <div data-screen-label="iPad · Decisions split view" style={{
      width: 1180, height: 820, borderRadius: 36, position: "relative",
      background: t.bg, overflow: "hidden",
      fontFamily: IOS.font, color: t.ink,
      boxShadow: "0 0 0 2px rgba(0,0,0,0.1), 0 40px 80px rgba(0,0,0,0.22)",
    }}>
      {/* status bar */}
      <div style={{
        display:"flex", justifyContent:"space-between", alignItems:"center",
        padding:"10px 24px 4px", fontSize:14, fontWeight:600, color:t.ink,
      }}>
        <span>9:41 Mon 19 Apr</span>
        <div style={{ display:"flex", gap:8 }}>
          <span style={{ fontSize:12 }}>100%</span>
          <svg width="20" height="10" viewBox="0 0 20 10">
            <rect x="0.5" y="0.5" width="17" height="9" rx="2" stroke={t.ink} fill="none"/>
            <rect x="2" y="2" width="14" height="6" fill={t.ink}/>
          </svg>
        </div>
      </div>

      {/* Three-column layout */}
      <div style={{ display:"grid", gridTemplateColumns:"220px 360px 1fr", height:"calc(100% - 28px)" }}>
        {/* Sidebar */}
        <div style={{
          background:t.surface2, borderRight:`0.5px solid ${t.sep}`,
          padding:"14px 12px",
        }}>
          <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.6, padding:"0 8px 8px", fontWeight:600 }}>
            QuantPipeline
          </div>
          {[
            { k:"Today", ic:"house", ct:"5", active:false },
            { k:"Decisions", ic:"decisions", ct:"12", active:true },
            { k:"Compare", ic:"compare" },
            { k:"Alerts", ic:"bell", ct:"3" },
            { k:"Replay" },
            { k:"Paper", ct:"4" },
            { k:"Watchlist", ic:"person" },
          ].map((n,i)=>(
            <div key={i} style={{
              display:"flex", alignItems:"center", gap:10, padding:"8px 10px",
              borderRadius:8, background: n.active? t.blue+"22" : "transparent",
              color: n.active? t.blue : t.ink2,
              fontSize:14, fontWeight: n.active? 600 : 400, marginBottom:2,
            }}>
              <div style={{ width:20, height:20, borderRadius:4, background: n.active? t.blue : t.ink4 }}/>
              <span style={{ flex:1 }}>{n.k}</span>
              {n.ct && <span style={{ fontSize:11, color:t.ink3, fontFamily:IOS.fontMono }}>{n.ct}</span>}
            </div>
          ))}
          <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.6, padding:"18px 8px 8px", fontWeight:600 }}>
            Saved views
          </div>
          {["Momentum leaders","Breach watch","Earnings week"].map((v,i)=>(
            <div key={i} style={{
              padding:"6px 10px", fontSize:13, color:t.ink3, display:"flex", alignItems:"center", gap:8,
            }}>
              <div style={{ width:6, height:6, borderRadius:3, background:t.ink4 }}/>
              <span>{v}</span>
            </div>
          ))}
        </div>

        {/* Middle — list */}
        <div style={{
          background:t.surface, borderRight:`0.5px solid ${t.sep}`,
          display:"flex", flexDirection:"column", overflow:"hidden",
        }}>
          <div style={{ padding:"14px 18px 10px" }}>
            <div style={{ fontFamily:IOS.fontDisplay, fontSize:28, fontWeight:700, letterSpacing:-0.3 }}>
              Decisions
            </div>
            <div style={{ fontSize:12, color:t.ink3, marginTop:1 }}>12 open · ranked by conviction</div>
          </div>
          {/* Scope chips */}
          <div style={{ padding:"0 18px 10px", display:"flex", gap:6 }}>
            {["All","Fresh","Flagged","Mine"].map((l,i)=>(
              <div key={i} style={{
                padding:"4px 10px", borderRadius:999, fontSize:12, fontWeight:500,
                background: i===0? t.blue : t.surface3,
                color: i===0? "#fff" : t.ink2,
              }}>{l}</div>
            ))}
          </div>
          {/* Rec list */}
          <div style={{ flex:1, overflow:"auto" }}>
            {recs.map((r,i)=>{
              const edPos = r.ed.startsWith("+");
              return (
                <div key={i} style={{
                  padding:"12px 18px", borderBottom:`0.5px solid ${t.sep}`,
                  background: r.sel? t.blue+"12" : "transparent",
                  borderLeft: r.sel? `3px solid ${t.blue}` : "3px solid transparent",
                }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:3 }}>
                    <span style={{ fontFamily:IOS.fontDisplay, fontSize:17, fontWeight:600, letterSpacing:-0.2 }}>{r.tk}</span>
                    <span style={{ fontSize:11, fontWeight:700, color:r.c, letterSpacing:0.4 }}>{r.stance}</span>
                    <span style={{
                      fontSize:9.5, fontWeight:700, padding:"1px 5px", borderRadius:3, marginLeft:"auto",
                      background: r.status==="fresh"? `${t.green}22` : r.status==="provisional"? `${t.orange}22` : t.surface3,
                      color: r.status==="fresh"? t.green : r.status==="provisional"? t.orange : t.ink3,
                      letterSpacing:0.3,
                    }}>{r.status.toUpperCase()}</span>
                  </div>
                  <div style={{ fontSize:12, color:t.ink3, marginBottom:6 }}>{r.nm}</div>
                  <div style={{ display:"flex", gap:14, fontFamily:IOS.fontMono, fontSize:11 }}>
                    <span style={{ color:t.ink3 }}>c {r.conf.toFixed(2)}</span>
                    <span style={{ color:edPos? t.green : t.red, fontWeight:600 }}>{r.ed}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detail pane */}
        <div style={{ overflow:"auto", padding:"18px 24px 32px" }}>
          <div style={{ display:"flex", alignItems:"baseline", gap:12, marginBottom:4 }}>
            <div style={{ fontFamily:IOS.fontDisplay, fontSize:36, fontWeight:700, letterSpacing:-0.5 }}>NVDA</div>
            <Pill bg="rgba(48,209,88,0.18)" color={t.green} size={12}>LONG</Pill>
            <Pill bg="rgba(10,132,255,0.18)" color={t.blue} size={11}>FRESH · v4</Pill>
            <div style={{ marginLeft:"auto", display:"flex", gap:6 }}>
              <button style={{
                padding:"8px 14px", border:0, borderRadius:9,
                background:t.surface3, color:t.ink, fontSize:13, fontWeight:500,
                fontFamily:"inherit",
              }}>Defer</button>
              <button style={{
                padding:"8px 14px", border:0, borderRadius:9,
                background:t.surface3, color:t.ink, fontSize:13, fontWeight:500,
                fontFamily:"inherit",
              }}>Challenge</button>
              <button style={{
                padding:"8px 14px", border:0, borderRadius:9,
                background:t.blue, color:"#fff", fontSize:13, fontWeight:600,
                fontFamily:"inherit",
              }}>Promote to paper</button>
            </div>
          </div>
          <div style={{ fontSize:13, color:t.ink3, fontFamily:IOS.fontMono, marginBottom:14 }}>
            REC‑2026‑0419‑NVDA‑L · 12m ago · NVIDIA Corp · Semiconductors
          </div>

          {/* Metric row */}
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:16 }}>
            {[
              { k:"Weight", v:"+4.2%", c:t.green },
              { k:"Horizon", v:"3M", c:t.ink },
              { k:"Expected Δ", v:"+4.8%", c:t.green },
              { k:"Confidence", v:"0.74", c:t.ink },
            ].map((m,i)=>(
              <div key={i} style={{
                padding:"10px 12px", borderRadius:10,
                background:t.surface, border:`0.5px solid ${t.sep}`,
              }}>
                <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>{m.k}</div>
                <div style={{ fontFamily:IOS.fontDisplay, fontSize:22, fontWeight:600, color:m.c, letterSpacing:-0.2 }}>{m.v}</div>
              </div>
            ))}
          </div>

          {/* Thesis block */}
          <div style={{
            padding:16, background:t.surface, borderRadius:14,
            border:`0.5px solid ${t.sep}`, marginBottom:16,
          }}>
            <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:8, fontWeight:600 }}>
              Thesis
            </div>
            <p style={{ fontSize:14.5, color:t.ink2, lineHeight:1.55, margin:0 }}>
              Increase weight to <b>+4.2%</b> on a 3‑month horizon. Momentum and quality
              engines align; earnings revisions at the 92nd percentile; flow turning
              constructive (put/call 0.47 vs 5d avg 0.62). Sector cap at 28.1%/30%.
            </p>
          </div>

          {/* Chart + engines grid */}
          <div style={{ display:"grid", gridTemplateColumns:"1.4fr 1fr", gap:12, marginBottom:16 }}>
            <div style={{ padding:14, background:t.surface, borderRadius:14, border:`0.5px solid ${t.sep}` }}>
              <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:10, fontWeight:600 }}>
                Confidence history · 30d
              </div>
              <svg viewBox="0 0 380 110" style={{ width:"100%", height:130 }} preserveAspectRatio="none">
                <path d="M0 80 L25 75 L50 82 L75 65 L100 60 L125 52 L150 42 L175 48 L200 40 L225 28 L250 35 L275 20 L300 18 L325 14 L350 22 L380 12"
                  fill="none" stroke={t.blue} strokeWidth="2"/>
                <path d="M0 70 L50 68 L100 50 L150 35 L200 35 L250 25 L300 20 L350 15 L380 10"
                  fill="none" stroke={t.ink4} strokeWidth="1.2" strokeDasharray="3,3"/>
                <circle cx="380" cy="12" r="3.5" fill={t.blue}/>
              </svg>
              <div style={{ display:"flex", gap:16, fontSize:11, color:t.ink3, marginTop:6 }}>
                <span style={{ display:"flex", alignItems:"center", gap:5 }}>
                  <span style={{ width:10, height:2, background:t.blue }}/> NVDA conf
                </span>
                <span style={{ display:"flex", alignItems:"center", gap:5 }}>
                  <span style={{ width:10, height:2, background:t.ink4, borderTop:"1px dashed" }}/> Composite avg
                </span>
              </div>
            </div>

            <div style={{ padding:14, background:t.surface, borderRadius:14, border:`0.5px solid ${t.sep}` }}>
              <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:10, fontWeight:600 }}>
                Engine stance · 4 of 5 align
              </div>
              {[
                { n:"Momentum", s:"LONG", c:0.82, col:t.green },
                { n:"Quality", s:"LONG", c:0.76, col:t.green },
                { n:"Earnings rev.", s:"LONG", c:0.71, col:t.green },
                { n:"Value", s:"HOLD", c:0.48, col:t.ink3 },
                { n:"Flow/options", s:"LONG", c:0.54, col:t.green },
              ].map((en,i)=>(
                <div key={i} style={{
                  display:"grid", gridTemplateColumns:"1fr 38px 58px",
                  gap:8, alignItems:"center", padding:"4px 0",
                  borderBottom:i<4?`0.5px solid ${t.sep}`:0,
                }}>
                  <span style={{ fontSize:12, color:t.ink }}>{en.n}</span>
                  <span style={{ fontSize:10, fontWeight:700, color:en.col, letterSpacing:0.3 }}>{en.s}</span>
                  <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                    <div style={{ flex:1, height:3, background:t.surface3, borderRadius:1.5, overflow:"hidden" }}>
                      <div style={{ height:"100%", width:(en.c*100)+"%", background:en.col }}/>
                    </div>
                    <span style={{ fontFamily:IOS.fontMono, fontSize:10, color:t.ink3 }}>{en.c.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence row */}
          <div style={{ fontSize:11, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:8, fontWeight:600 }}>
            Evidence
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
            {[
              "12m EPS revisions +4.8% · 92nd percentile in sector",
              "Put/call ratio 0.47 (5d avg 0.62) · bullish flow skew",
              "ROIC 28.3%, FCF margin 41% · top quartile quality",
              "News attribution lags 14m · caveat applied to scoring",
            ].map((e,i)=>(
              <div key={i} style={{
                padding:12, borderRadius:10,
                background:t.surface, border:`0.5px solid ${t.sep}`,
                display:"flex", gap:10,
              }}>
                <span style={{
                  width:22, height:22, borderRadius:11, flexShrink:0,
                  background: i===3? t.surface3 : `${t.blue}28`,
                  color: i===3? t.ink3 : t.blue,
                  display:"grid", placeItems:"center",
                  fontSize:11, fontWeight:700, fontFamily:IOS.fontMono,
                }}>{i+1}</span>
                <span style={{ fontSize:13, color:t.ink2, lineHeight:1.45 }}>{e}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { S_iPad });
