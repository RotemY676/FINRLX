// iOS decision detail screens (2 variations) + scenario controls + publish flow

// ═════════════════════════════════════════════════════════════
// SCREEN 3 — Decision detail · Variation A (reading-first)
// ═════════════════════════════════════════════════════════════
function S_DecisionA({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Decision · A (reading-first)">
      {/* Nav with back */}
      <div style={{ paddingTop: 4 }}>
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"2px 16px 8px",
        }}>
          <div style={{ display:"flex", alignItems:"center", gap:2, color:t.blue, fontSize:17 }}>
            {SF.chev(t.blue,"left")}<span style={{ marginLeft:2 }}>Today</span>
          </div>
          <div style={{ display:"flex", gap:12, alignItems:"center" }}>
            <div style={{ color:t.blue }}>{SF.ellipsis(t.blue)}</div>
          </div>
        </div>
      </div>

      {/* Recommendation hero */}
      <div style={{ padding:"8px 20px 16px" }}>
        <div style={{ display:"flex", alignItems:"baseline", gap:10, marginBottom:6 }}>
          <div style={{ fontFamily:IOS.fontDisplay, fontSize:38, fontWeight:700, letterSpacing:-0.5 }}>NVDA</div>
          <Pill bg="rgba(48,209,88,0.18)" color={t.green} size={12}>LONG</Pill>
          <Pill bg="rgba(10,132,255,0.18)" color={t.blue} size={11}>FRESH</Pill>
        </div>
        <div style={{ fontSize:14, color:t.ink3, fontFamily:IOS.fontMono, marginBottom:14 }}>
          REC‑2026‑0419‑NVDA‑L · v4 · 12m ago
        </div>
        <div style={{ fontSize:16.5, color:t.ink, lineHeight:1.5, letterSpacing:-0.1 }}>
          Increase weight to <b>+4.2%</b> over a <b>3‑month</b> horizon. Momentum and quality
          engines align; earnings revisions +4.8% in trailing 4w; sector cap at 28.1%/30%.
        </div>
        <div style={{ display:"flex", gap:14, marginTop:18 }}>
          {[
            { k:"Weight", v:"+4.2%", c:t.green },
            { k:"Horizon", v:"3M", c:t.ink },
            { k:"Expected Δ", v:"+4.8%", c:t.green },
          ].map((m,i)=>(
            <div key={i} style={{
              flex:1, padding:"10px 12px", borderRadius:12,
              background:t.surface, border:`0.5px solid ${t.sep}`,
            }}>
              <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>{m.k}</div>
              <div style={{ fontFamily:IOS.fontDisplay, fontSize:19, fontWeight:600, color:m.c, letterSpacing:-0.2 }}>{m.v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Confidence trio */}
      <Group dark={dark} header="Confidence">
        {[
          { k:"Model confidence", v:0.74, s:"4/5 engines aligned" },
          { k:"Data quality", v:0.92, s:"No feed lag · full coverage" },
          { k:"Operational readiness", v:0.68, s:"Sector limit watch" },
        ].map((c,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
              <span style={{ fontSize:15, color:t.ink }}>{c.k}</span>
              <span style={{ fontFamily:IOS.fontMono, fontSize:13, color:t.ink, fontWeight:600 }}>{c.v.toFixed(2)}</span>
            </div>
            <div style={{ height:4, background:t.surface3, borderRadius:2, overflow:"hidden", marginBottom:4 }}>
              <div style={{ height:"100%", width:(c.v*100)+"%",
                background: c.v>0.7? t.green : c.v>0.5? t.orange : t.red }}/>
            </div>
            <div style={{ fontSize:12, color:t.ink3 }}>{c.s}</div>
          </Row>
        ))}
      </Group>

      {/* Evidence narrative */}
      <Group dark={dark} header="Evidence">
        {[
          "12m EPS revisions trend +4.8% · 92nd percentile vs sector",
          "Options flow skew: bullish · put/call 0.47 (5d avg 0.62)",
          "Quality engine: ROIC 28.3%, FCF margin 41% — top quartile",
          "Caveat: attribution from news/intel lags 14m (feed warning)",
        ].map((e,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", gap:10 }}>
              <span style={{
                width:20, height:20, borderRadius:10, flexShrink:0,
                background: i===a.length-1? t.surface3 : `${t.blue}28`,
                color: i===a.length-1? t.ink3 : t.blue,
                display:"grid", placeItems:"center", fontSize:11, fontWeight:700,
                fontFamily:IOS.fontMono,
              }}>{i+1}</span>
              <span style={{ fontSize:14.5, color:t.ink2, lineHeight:1.45 }}>{e}</span>
            </div>
          </Row>
        ))}
      </Group>

      {/* Disagreement block */}
      <Group dark={dark} header="Engine disagreement">
        <Row dark={dark}>
          <div style={{ display:"flex", justifyContent:"space-between", marginBottom:10 }}>
            <span style={{ fontSize:14, color:t.ink2 }}>4 of 5 engines align</span>
            <span style={{ fontFamily:IOS.fontMono, fontSize:13, color:t.ink3 }}>dispersion 0.37</span>
          </div>
          {[
            { n:"Momentum", s:"LONG", c:0.82, col:t.green },
            { n:"Quality", s:"LONG", c:0.76, col:t.green },
            { n:"Earnings revisions", s:"LONG", c:0.71, col:t.green },
            { n:"Value", s:"HOLD", c:0.48, col:t.ink3 },
            { n:"Flow/options", s:"LONG", c:0.54, col:t.green },
          ].map((en,i)=>(
            <div key={i} style={{
              display:"grid", gridTemplateColumns:"1fr 54px 1fr 40px",
              gap:10, alignItems:"center", padding:"6px 0",
            }}>
              <span style={{ fontSize:13, color:t.ink }}>{en.n}</span>
              <span style={{ fontSize:11, fontWeight:700, color:en.col, letterSpacing:0.3 }}>{en.s}</span>
              <div style={{ height:5, background:t.surface3, borderRadius:2, overflow:"hidden" }}>
                <div style={{ height:"100%", width:(en.c*100)+"%", background:en.col }}/>
              </div>
              <span style={{ fontFamily:IOS.fontMono, fontSize:11, color:t.ink3, textAlign:"right" }}>{en.c.toFixed(2)}</span>
            </div>
          ))}
        </Row>
      </Group>

      {/* Actions sticky bottom */}
      <div style={{ height: 180 }}/>
      <div style={{
        position:"absolute", bottom:34, left:0, right:0, padding:"10px 16px 14px",
        background: dark? "rgba(20,20,22,0.88)" : "rgba(255,255,255,0.88)",
        backdropFilter:"saturate(180%) blur(20px)",
        WebkitBackdropFilter:"saturate(180%) blur(20px)",
        borderTop:`0.5px solid ${t.sep}`,
      }}>
        <div style={{ display:"flex", gap:8 }}>
          <button style={{
            flex:1, padding:"13px", border:0, borderRadius:12,
            background:t.surface3, color:t.ink, fontSize:15, fontWeight:600,
            fontFamily:"inherit",
          }}>Defer</button>
          <button style={{
            flex:1, padding:"13px", border:0, borderRadius:12,
            background:t.surface3, color:t.ink, fontSize:15, fontWeight:600,
            fontFamily:"inherit",
          }}>Challenge</button>
          <button style={{
            flex:1.3, padding:"13px", border:0, borderRadius:12,
            background:t.blue, color:"#fff", fontSize:15, fontWeight:600,
            fontFamily:"inherit",
          }}>Promote →</button>
        </div>
        <div style={{ fontSize:11, color:t.ink3, textAlign:"center", marginTop:6 }}>
          Publish requires desktop · Face ID required to promote
        </div>
      </div>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 4 — Decision detail · Variation B (scannable tabs)
// ═════════════════════════════════════════════════════════════
function S_DecisionB({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Decision · B (scannable tabs)">
      <div style={{ paddingTop:4 }}>
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"2px 16px 8px",
        }}>
          <div style={{ display:"flex", alignItems:"center", color:t.blue, fontSize:17 }}>
            {SF.chev(t.blue,"left")}<span style={{ marginLeft:2 }}>Today</span>
          </div>
          <div style={{ color:t.blue }}>{SF.ellipsis(t.blue)}</div>
        </div>
      </div>

      {/* Compact hero */}
      <div style={{
        margin:"4px 16px 12px", padding:16, borderRadius:16,
        background:`linear-gradient(135deg, ${t.surface} 0%, ${t.surface2} 100%)`,
        border:`0.5px solid ${t.sep}`, position:"relative", overflow:"hidden",
      }}>
        <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:3 }}>
          <div style={{ fontFamily:IOS.fontDisplay, fontSize:30, fontWeight:700, letterSpacing:-0.4 }}>NVDA</div>
          <Pill bg="rgba(48,209,88,0.18)" color={t.green} size={11}>LONG · v4</Pill>
        </div>
        <div style={{ fontSize:13, color:t.ink3, marginBottom:14 }}>NVIDIA Corp · Semiconductors · $24.2B position</div>

        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8 }}>
          {[
            { k:"W", v:"+4.2%", c:t.green },
            { k:"CONF", v:"0.74", c:t.ink },
            { k:"Δ 3M", v:"+4.8%", c:t.green },
            { k:"DISP", v:"0.37", c:t.orange },
          ].map((m,i)=>(
            <div key={i} style={{
              padding:"6px 8px", borderRadius:8, background:t.surface3, textAlign:"center",
            }}>
              <div style={{ fontSize:9, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5 }}>{m.k}</div>
              <div style={{ fontFamily:IOS.fontMono, fontSize:14, fontWeight:600, color:m.c }}>{m.v}</div>
            </div>
          ))}
        </div>

        {/* Mini sparkline */}
        <svg viewBox="0 0 300 54" style={{ width:"100%", height:54, marginTop:12 }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="sparkGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={t.green} stopOpacity="0.28"/>
              <stop offset="100%" stopColor={t.green} stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d="M0 40 L20 38 L40 36 L60 32 L80 34 L100 30 L120 26 L140 28 L160 22 L180 18 L200 20 L220 14 L240 12 L260 10 L280 14 L300 8"
            fill="none" stroke={t.green} strokeWidth="2"/>
          <path d="M0 40 L20 38 L40 36 L60 32 L80 34 L100 30 L120 26 L140 28 L160 22 L180 18 L200 20 L220 14 L240 12 L260 10 L280 14 L300 8 L300 54 L0 54 Z"
            fill="url(#sparkGrad)"/>
          <circle cx="300" cy="8" r="3" fill={t.green}/>
        </svg>
      </div>

      {/* Segmented tabs */}
      <div style={{
        margin:"0 16px 12px", padding:2, borderRadius:9,
        background:t.surface3, display:"flex", gap:2,
      }}>
        {["Thesis","Evidence","Risk","Engines"].map((tab,i)=>(
          <div key={i} style={{
            flex:1, padding:"6px 8px", borderRadius:7, textAlign:"center",
            fontSize:13, fontWeight: i===0?600:500,
            background: i===0? t.surface : "transparent",
            color: i===0? t.ink : t.ink3,
            boxShadow: i===0? "0 1px 2px rgba(0,0,0,0.08)" : "none",
          }}>{tab}</div>
        ))}
      </div>

      {/* Thesis content */}
      <div style={{ padding:"0 16px 120px" }}>
        <div style={{ fontSize:13, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:6 }}>
          Thesis
        </div>
        <p style={{ fontSize:16, color:t.ink, lineHeight:1.55, letterSpacing:-0.1, margin:"0 0 14px" }}>
          Increase weight to <b>+4.2%</b> on a 3‑month horizon. Momentum and quality
          engines align with the strongest conviction we've seen since February.
        </p>
        <div style={{
          padding:"10px 12px", background:`${t.orange}15`,
          border:`0.5px solid ${t.orange}40`, borderRadius:10, marginBottom:14,
          display:"flex", gap:10,
        }}>
          {SF.warning(t.orange, 16)}
          <div style={{ fontSize:13, color:t.ink, lineHeight:1.4 }}>
            <b>Sector cap approaching</b> — Semis at 28.1% / 30% hard limit.
            This recommendation adds ~0.6% exposure.
          </div>
        </div>

        <div style={{ fontSize:13, color:t.ink3, textTransform:"uppercase", letterSpacing:0.5, marginBottom:8 }}>
          Risk posture
        </div>
        {[
          { k:"Drawdown budget", v:"2.1% of 3.0%", pct:0.70, c:t.orange },
          { k:"VaR contribution", v:"+0.18% of 2%", pct:0.35, c:t.green },
          { k:"Liquidity (days to unwind)", v:"0.7 days", pct:0.15, c:t.green },
          { k:"Single-name", v:"4.2% of 5.0%", pct:0.84, c:t.orange },
        ].map((r,i)=>(
          <div key={i} style={{ marginBottom:10 }}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
              <span style={{ fontSize:13.5, color:t.ink2 }}>{r.k}</span>
              <span style={{ fontFamily:IOS.fontMono, fontSize:12, color:t.ink }}>{r.v}</span>
            </div>
            <div style={{ height:4, background:t.surface3, borderRadius:2, overflow:"hidden" }}>
              <div style={{ height:"100%", width:(r.pct*100)+"%", background:r.c }}/>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom sheet handle */}
      <div style={{
        position:"absolute", bottom:34, left:0, right:0,
        background: dark? "rgba(20,20,22,0.92)" : "rgba(255,255,255,0.92)",
        backdropFilter:"saturate(180%) blur(20px)",
        WebkitBackdropFilter:"saturate(180%) blur(20px)",
        borderTop:`0.5px solid ${t.sep}`,
        padding:"8px 16px 12px",
      }}>
        <div style={{
          width:36, height:4, borderRadius:2, background:t.ink4,
          margin:"0 auto 10px",
        }}/>
        <div style={{ display:"flex", gap:8 }}>
          <button style={{
            padding:"12px 14px", border:0, borderRadius:12,
            background:t.surface3, color:t.ink, fontSize:14, fontWeight:600,
            fontFamily:"inherit",
          }}>Scenario</button>
          <button style={{
            padding:"12px 14px", border:0, borderRadius:12,
            background:t.surface3, color:t.ink, fontSize:14, fontWeight:600,
            fontFamily:"inherit",
          }}>Compare</button>
          <button style={{
            flex:1, padding:"12px", border:0, borderRadius:12,
            background:t.blue, color:"#fff", fontSize:14, fontWeight:600,
            fontFamily:"inherit",
          }}>Promote to paper</button>
        </div>
      </div>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 5 — Scenario controls
// ═════════════════════════════════════════════════════════════
function S_Scenario({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Scenario controls">
      <div style={{ paddingTop:4 }}>
        <div style={{
          display:"flex", alignItems:"center", justifyContent:"space-between",
          padding:"2px 16px 8px",
        }}>
          <div style={{ color:t.blue, fontSize:17 }}>Cancel</div>
          <div style={{ fontSize:17, fontWeight:600, color:t.ink }}>Scenario · NVDA</div>
          <div style={{ color:t.blue, fontSize:17, fontWeight:600 }}>Apply</div>
        </div>
      </div>

      <div style={{ padding:"0 16px 12px" }}>
        <div style={{ fontSize:13, color:t.ink3, marginBottom:12 }}>
          Adjust inputs · see delta before committing. Saved scenarios persist to the decision.
        </div>
      </div>

      {/* Delta preview strip */}
      <div style={{
        margin:"0 16px 16px", padding:"12px 14px", borderRadius:14,
        background:`${t.blue}14`, border:`0.5px solid ${t.blue}40`,
      }}>
        <div style={{ fontSize:10.5, color:t.blue, fontWeight:700, textTransform:"uppercase", letterSpacing:0.6, marginBottom:8 }}>
          Delta preview
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8 }}>
          {[
            { k:"Weight", a:"+4.2%", b:"+3.1%", pos:false },
            { k:"Conf", a:"0.74", b:"0.69", pos:false },
            { k:"Exp Δ", a:"+4.8%", b:"+5.4%", pos:true },
          ].map((d,i)=>(
            <div key={i}>
              <div style={{ fontSize:10, color:t.ink3, textTransform:"uppercase", letterSpacing:0.4 }}>{d.k}</div>
              <div style={{ display:"flex", alignItems:"baseline", gap:4, marginTop:2 }}>
                <span style={{
                  fontFamily:IOS.fontMono, fontSize:12, color:t.ink4,
                  textDecoration:"line-through",
                }}>{d.a}</span>
                {SF.chev(t.ink3)}
                <span style={{
                  fontFamily:IOS.fontMono, fontSize:14, fontWeight:700,
                  color: d.pos? t.green : t.red,
                }}>{d.b}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sliders */}
      <Group dark={dark} header="Assumptions">
        {[
          { k:"Momentum weight", v:0.75, lo:"value", hi:"momentum" },
          { k:"Horizon", v:0.5, lo:"1M", hi:"12M", val:"3M" },
          { k:"Volatility regime", v:0.35, lo:"calm", hi:"stressed" },
          { k:"Earnings surprise", v:0.60, lo:"−5σ", hi:"+5σ", val:"+0.8σ" },
        ].map((s,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
              <span style={{ fontSize:15, color:t.ink }}>{s.k}</span>
              {s.val && <span style={{ fontFamily:IOS.fontMono, fontSize:13, color:t.blue, fontWeight:600 }}>{s.val}</span>}
            </div>
            <div style={{ position:"relative", height:28, display:"flex", alignItems:"center" }}>
              <div style={{ height:4, background:t.surface3, width:"100%", borderRadius:2, position:"relative" }}>
                <div style={{ height:"100%", width:(s.v*100)+"%", background:t.blue, borderRadius:2 }}/>
                <div style={{
                  position:"absolute", left:`calc(${s.v*100}% - 14px)`, top:-10,
                  width:28, height:28, borderRadius:14, background:"#fff",
                  boxShadow:"0 2px 6px rgba(0,0,0,0.3)", border:`0.5px solid ${t.sep}`,
                }}/>
              </div>
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:t.ink3, marginTop:2 }}>
              <span>{s.lo}</span><span>{s.hi}</span>
            </div>
          </Row>
        ))}
      </Group>

      {/* Toggles */}
      <Group dark={dark} header="Overrides">
        {[
          { k:"Stress test · crude shock", on:false },
          { k:"Stress test · rate shock", on:true },
          { k:"Exclude stale engines", on:true },
        ].map((s,i,a)=>(
          <Row dark={dark} key={i} last={i===a.length-1}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span style={{ fontSize:15, color:t.ink }}>{s.k}</span>
              <div style={{
                width:51, height:31, borderRadius:16,
                background: s.on? t.green : t.surface3, padding:2,
                display:"flex", alignItems:"center",
              }}>
                <div style={{
                  width:27, height:27, borderRadius:14, background:"#fff",
                  marginLeft: s.on? 20 : 0,
                  boxShadow:"0 2px 4px rgba(0,0,0,0.2)",
                }}/>
              </div>
            </div>
          </Row>
        ))}
      </Group>

      <div style={{ padding:"0 16px 60px" }}>
        <button style={{
          width:"100%", padding:14, borderRadius:14, border:0,
          background:t.surface, color:t.blue, fontSize:16, fontWeight:500,
          fontFamily:"inherit",
        }}>Save as scenario</button>
      </div>
    </IOSPhone>
  );
}

// ═════════════════════════════════════════════════════════════
// SCREEN 6 — Publish / promote sheet
// ═════════════════════════════════════════════════════════════
function S_Publish({ dark = true }) {
  const t = useIOS(dark);
  return (
    <IOSPhone dark={dark} label="iOS · Promote sheet (Face ID)">
      {/* Dimmed parent */}
      <div style={{ position:"absolute", inset:0, background:"rgba(0,0,0,0.55)", zIndex:1 }}/>
      {/* blurred preview of underlying */}
      <div style={{ padding:"8px 20px 0", opacity:0.35, filter:"blur(3px)" }}>
        <div style={{ fontFamily:IOS.fontDisplay, fontSize:38, fontWeight:700 }}>NVDA</div>
        <div style={{ fontSize:14, color:t.ink3 }}>REC‑2026‑0419‑NVDA‑L · v4</div>
      </div>

      {/* Bottom sheet */}
      <div style={{
        position:"absolute", bottom:0, left:0, right:0,
        background:t.surface, borderTopLeftRadius:22, borderTopRightRadius:22,
        padding:"10px 0 40px", zIndex:10,
      }}>
        <div style={{
          width:36, height:4, borderRadius:2, background:t.ink4,
          margin:"6px auto 18px",
        }}/>

        <div style={{ padding:"0 20px", textAlign:"center", marginBottom:22 }}>
          <div style={{
            width:66, height:66, borderRadius:33, margin:"0 auto 14px",
            background:`${t.blue}18`, display:"grid", placeItems:"center",
          }}>
            <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
              <rect x="3" y="3" width="28" height="28" rx="7" stroke={t.blue} strokeWidth="2"/>
              <path d="M10 13c0-1.5 1.5-3 3.5-3M24 21c0 1.5-1.5 3-3.5 3M12 17v0.5M22 17v0.5M14 22c1 1 3 1 3 1s2 0 3-1" stroke={t.blue} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div style={{ fontSize:20, fontWeight:600, color:t.ink, marginBottom:6, letterSpacing:-0.2 }}>
            Promote to paper portfolio
          </div>
          <div style={{ fontSize:14, color:t.ink3, lineHeight:1.45 }}>
            This creates a paper position at v4. Publishing to live requires desktop review.
          </div>
        </div>

        {/* Summary card */}
        <div style={{ margin:"0 20px 18px", padding:14, borderRadius:14, background:t.surface2 }}>
          <div style={{ display:"flex", justifyContent:"space-between", padding:"4px 0" }}>
            <span style={{ fontSize:13, color:t.ink3 }}>Recommendation</span>
            <span style={{ fontSize:13, color:t.ink, fontWeight:600 }}>NVDA · LONG · v4</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", padding:"4px 0" }}>
            <span style={{ fontSize:13, color:t.ink3 }}>Weight</span>
            <span style={{ fontSize:13, color:t.green, fontFamily:IOS.fontMono, fontWeight:600 }}>+4.2%</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", padding:"4px 0" }}>
            <span style={{ fontSize:13, color:t.ink3 }}>Scenario</span>
            <span style={{ fontSize:13, color:t.ink }}>Default · no overrides</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", padding:"4px 0" }}>
            <span style={{ fontSize:13, color:t.ink3 }}>Approver</span>
            <span style={{ fontSize:13, color:t.ink }}>R. Mikhailov (you)</span>
          </div>
        </div>

        <div style={{ padding:"0 20px" }}>
          <button style={{
            width:"100%", padding:14, borderRadius:14, border:0,
            background:t.blue, color:"#fff", fontSize:16, fontWeight:600,
            fontFamily:"inherit", marginBottom:8,
            display:"flex", alignItems:"center", justifyContent:"center", gap:8,
          }}>
            Confirm with Face ID
          </button>
          <button style={{
            width:"100%", padding:14, borderRadius:14, border:0,
            background:"transparent", color:t.blue, fontSize:16, fontWeight:500,
            fontFamily:"inherit",
          }}>Cancel</button>
        </div>
      </div>
    </IOSPhone>
  );
}

Object.assign(window, { S_DecisionA, S_DecisionB, S_Scenario, S_Publish });
