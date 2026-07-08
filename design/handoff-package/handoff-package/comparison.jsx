// Engine Comparison workspace
const { useState: useStateCmp } = React;

const ENGINES = [
  { key:"momentum", name:"Momentum", mk:"M", stance:"buy", conf:0.82, w:0.28, risk:"Moderate",
    target:198, weight:4.8, horizon:"3M",
    drivers:["9-wk price acceleration","Factor tilt: momentum +0.62σ","Sector leadership persistence"],
    ignores:["Options positioning","Near-term earnings quality"],
    note:"High conviction long; engine capped at 28% weight in risk-on regimes." },
  { key:"fundamentals", name:"Fundamentals", mk:"F", stance:"buy", conf:0.71, w:0.24, risk:"Moderate",
    target:188, weight:3.8, horizon:"6M",
    drivers:["EPS revisions +4.8% median","Data-center guidance raise","Margin expansion vs peers"],
    ignores:["Short-term flow & positioning"],
    note:"Served fallback path during 09:20 data lag; attribution partial." },
  { key:"narrative", name:"Narrative LLM", mk:"N", stance:"hold", conf:0.58, w:0.18, risk:"Elevated",
    target:175, weight:0.0, horizon:"3M",
    drivers:["Mixed sentiment: supply-chain risk","Sector tone softened −0.22","Retail interest plateau"],
    ignores:["Quantitative factor exposure"],
    note:"Dissents on direction; flags Taiwan logistics narrative as unresolved." },
  { key:"riskparity", name:"Risk-parity", mk:"R", stance:"hold", conf:0.54, w:0.18, risk:"Low",
    target:172, weight:1.2, horizon:"6M",
    drivers:["Correlation to top-5 0.71 (high)","Realized vol 34% (elevated)","Diversification-cost binding"],
    ignores:["Momentum signal","News flow"],
    note:"Trim bias under current concentration; not a directional view." },
  { key:"flow", name:"Flow / options", mk:"O", stance:"sell", conf:0.49, w:0.12, risk:"High",
    target:162, weight:-0.8, horizon:"1M",
    drivers:["Put/call skew widening","Negative gamma through 950","Dealer hedging cross-flow"],
    ignores:["Earnings revisions","Macro regime"],
    note:"Confidence capped while options IV is stale (14m)." },
];

const DIMENSIONS = [
  { key:"stance", label:"Stance" },
  { key:"conf", label:"Confidence" },
  { key:"target", label:"Price target" },
  { key:"weight", label:"Weight" },
  { key:"horizon", label:"Horizon" },
  { key:"risk", label:"Risk read" },
  { key:"drivers", label:"Top drivers" },
];

const StanceCell = ({ v }) => (
  <span className={"engine-stance " + v} style={{display:"inline-block"}}>{v}</span>
);

const ConfCell = ({ v }) => (
  <div style={{display:"flex",alignItems:"center",gap:8}}>
    <div className="engine-conf-bar" style={{width:64}}><span style={{width:(v*100)+"%"}} /></div>
    <span className="num" style={{fontSize:12}}>{v.toFixed(2)}</span>
  </div>
);

const WeightCell = ({ v }) => {
  const cls = v > 0 ? "hl-pos" : v < 0 ? "hl-neg" : "muted";
  const sign = v > 0 ? "+" : "";
  return <span className={"num " + cls} style={{fontSize:12}}>{sign}{v.toFixed(1)}%</span>;
};

const DriversCell = ({ items }) => (
  <ul style={{margin:0,padding:"0 0 0 16px",color:"var(--ink-2)",fontSize:12,lineHeight:1.5}}>
    {items.map((d,i)=><li key={i}>{d}</li>)}
  </ul>
);

function ComparisonMatrix({ selected, onSelect }) {
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="compare" size={14} />
        <h3>Comparison matrix</h3>
        <div className="meta">
          <span>Rows = engines · columns = dimensions</span>
          <button className="btn ghost sm"><Icon name="filter" size={12}/> Dimensions</button>
        </div>
      </div>
      <div className="card-body" style={{padding:0,overflowX:"auto"}}>
        <table className="cmp-table">
          <thead>
            <tr>
              <th style={{position:"sticky",left:0,zIndex:2,background:"var(--surface-2)"}}>Engine</th>
              {DIMENSIONS.map(d=><th key={d.key}>{d.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {ENGINES.map(e => (
              <tr key={e.key} className={selected === e.key ? "sel" : ""} onClick={()=>onSelect(e.key)}>
                <th className="engine-col" style={{position:"sticky",left:0,zIndex:1}}>
                  <div className="engine-name">
                    <span className="mk">{e.mk}</span>
                    <span style={{display:"flex",flexDirection:"column",lineHeight:1.2}}>
                      <span>{e.name}</span>
                      <span className="muted" style={{fontSize:11}}>w {e.w.toFixed(2)}</span>
                    </span>
                  </div>
                </th>
                <td><StanceCell v={e.stance} /></td>
                <td><ConfCell v={e.conf} /></td>
                <td className="num" style={{fontSize:12}}>${e.target}</td>
                <td><WeightCell v={e.weight} /></td>
                <td className="num" style={{fontSize:12}}>{e.horizon}</td>
                <td>
                  <span className={"risk-pill " + e.risk.toLowerCase()}>{e.risk}</span>
                </td>
                <td><DriversCell items={e.drivers.slice(0,2)} /></td>
              </tr>
            ))}
            <tr className="synth">
              <th style={{position:"sticky",left:0,background:"var(--primary-soft)"}}>
                <div className="engine-name">
                  <span className="mk" style={{background:"var(--primary)",color:"var(--primary-ink)"}}>Σ</span>
                  <span style={{display:"flex",flexDirection:"column",lineHeight:1.2}}>
                    <span>Synthesis</span>
                    <span className="muted" style={{fontSize:11}}>weighted</span>
                  </span>
                </div>
              </th>
              <td><StanceCell v="buy" /></td>
              <td><ConfCell v={0.74} /></td>
              <td className="num" style={{fontSize:12}}>$184</td>
              <td><WeightCell v={4.2} /></td>
              <td className="num" style={{fontSize:12}}>3M</td>
              <td><span className="risk-pill moderate">Moderate</span></td>
              <td style={{fontSize:12,color:"var(--ink-2)"}}>Long with trim bias; provisional on options freshness.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Alignment chart: scatter of engines on (stance axis × confidence), size = weight
function AlignmentChart() {
  // x: -1 sell, 0 hold, +1 buy; y: confidence 0..1
  const stanceX = s => s === "sell" ? -1 : s === "hold" ? 0 : 1;
  const W = 560, H = 260, PAD = 36;
  const sx = x => PAD + ((x + 1) / 2) * (W - PAD * 2);
  const sy = y => H - PAD - y * (H - PAD * 2);
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="trend-up" size={14} />
        <h3>Alignment view</h3>
        <div className="meta"><span>Stance × confidence · bubble = weight</span></div>
      </div>
      <div className="card-body">
        <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:260,display:"block"}}>
          <defs>
            <linearGradient id="agreeBand" x1="0" x2="1">
              <stop offset="0%" stopColor="var(--breach)" stopOpacity="0.08" />
              <stop offset="50%" stopColor="var(--caution)" stopOpacity="0.05" />
              <stop offset="100%" stopColor="var(--pos)" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          <rect x={PAD} y={PAD} width={W-PAD*2} height={H-PAD*2} fill="url(#agreeBand)" rx="6" />
          {/* grid */}
          <line x1={sx(0)} x2={sx(0)} y1={PAD} y2={H-PAD} stroke="var(--line)" strokeDasharray="3 3" />
          {[0.25,0.5,0.75].map(v=>(
            <line key={v} x1={PAD} x2={W-PAD} y1={sy(v)} y2={sy(v)} stroke="var(--line)" strokeDasharray="2 3" />
          ))}
          {/* axis labels */}
          <text x={PAD} y={H-12} fontSize="10.5" fill="var(--ink-4)" style={{fontFamily:"var(--font-mono)"}}>SELL</text>
          <text x={W/2} y={H-12} fontSize="10.5" textAnchor="middle" fill="var(--ink-4)" style={{fontFamily:"var(--font-mono)"}}>HOLD</text>
          <text x={W-PAD} y={H-12} fontSize="10.5" textAnchor="end" fill="var(--ink-4)" style={{fontFamily:"var(--font-mono)"}}>BUY</text>
          <text x={8} y={PAD+4} fontSize="10.5" fill="var(--ink-4)" style={{fontFamily:"var(--font-mono)"}}>1.0</text>
          <text x={8} y={H-PAD} fontSize="10.5" fill="var(--ink-4)" style={{fontFamily:"var(--font-mono)"}}>0.0</text>
          <text x={12} y={PAD-14} fontSize="10.5" fill="var(--ink-3)">Confidence</text>
          {/* engine bubbles */}
          {ENGINES.map(e => {
            const c = e.stance === "buy" ? "var(--pos)" : e.stance === "sell" ? "var(--breach)" : "var(--caution)";
            const x = sx(stanceX(e.stance) + (e.key==="narrative"? -0.08 : e.key==="riskparity"? 0.08 : 0));
            const y = sy(e.conf);
            const r = 14 + e.w * 40;
            return (
              <g key={e.key}>
                <circle cx={x} cy={y} r={r} fill={c} opacity="0.18" />
                <circle cx={x} cy={y} r={8} fill="var(--surface)" stroke={c} strokeWidth="2" />
                <text x={x} y={y+3} fontSize="10.5" textAnchor="middle" fill="var(--ink)"
                  style={{fontFamily:"var(--font-mono)",fontWeight:600}}>{e.mk}</text>
                <text x={x + r + 6} y={y - 2} fontSize="11" fill="var(--ink-2)">{e.name}</text>
                <text x={x + r + 6} y={y + 11} fontSize="10" fill="var(--ink-4)"
                  style={{fontFamily:"var(--font-mono)"}}>{e.conf.toFixed(2)} · w{e.w.toFixed(2)}</text>
              </g>
            );
          })}
          {/* synthesis point */}
          <g>
            <circle cx={sx(0.55)} cy={sy(0.74)} r="10" fill="var(--primary)" stroke="var(--surface)" strokeWidth="3" />
            <text x={sx(0.55)+16} y={sy(0.74)-2} fontSize="11" fill="var(--ink)" fontWeight="600">Synthesis</text>
            <text x={sx(0.55)+16} y={sy(0.74)+11} fontSize="10" fill="var(--ink-3)"
                  style={{fontFamily:"var(--font-mono)"}}>Long · 0.74</text>
          </g>
        </svg>
        <div className="chart-legend" style={{marginTop:6}}>
          <span className="item"><span className="sw" style={{background:"var(--pos)"}}/> Buy</span>
          <span className="item"><span className="sw" style={{background:"var(--caution)"}}/> Hold</span>
          <span className="item"><span className="sw" style={{background:"var(--breach)"}}/> Sell</span>
          <span className="item" style={{marginLeft:"auto",color:"var(--ink-3)"}}>
            Dispersion 0.37 / 1 · mixed
          </span>
        </div>
      </div>
    </div>
  );
}

function MethodologyCard({ selected }) {
  const e = ENGINES.find(x => x.key === selected) || ENGINES[0];
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="info" size={14} />
        <h3>What {e.name} sees & ignores</h3>
        <div className="meta">
          <div style={{display:"inline-flex",gap:2,padding:2,border:"1px solid var(--line)",borderRadius:6,background:"var(--surface-2)"}}>
            {ENGINES.map(x => (
              <button key={x.key} className="btn sm" style={{height:22,padding:"0 8px",fontSize:11,
                background: x.key===selected ? "var(--surface)" : "transparent",
                border: x.key===selected ? "1px solid var(--line-strong)" : "1px solid transparent",
                color: x.key===selected ? "var(--ink)" : "var(--ink-3)"}}>{x.mk}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="card-body">
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
          <div>
            <div className="ctx-kv" style={{marginBottom:10}}>
              <span className="k">Stance</span><span className="v"><StanceCell v={e.stance}/></span>
              <span className="k">Confidence</span><span className="v num">{e.conf.toFixed(2)}</span>
              <span className="k">Price target</span><span className="v num">${e.target}</span>
              <span className="k">Engine weight</span><span className="v num">{e.w.toFixed(2)}</span>
              <span className="k">Horizon</span><span className="v num">{e.horizon}</span>
              <span className="k">Risk read</span><span className="v">{e.risk}</span>
            </div>
          </div>
          <div>
            <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:"0.07em",color:"var(--ink-3)",fontWeight:600,marginBottom:6}}>What it sees</div>
            <ul style={{margin:0,padding:"0 0 0 16px",fontSize:12.5,lineHeight:1.6,color:"var(--ink-2)"}}>
              {e.drivers.map((d,i)=><li key={i}>{d}</li>)}
            </ul>
            <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:"0.07em",color:"var(--ink-3)",fontWeight:600,margin:"12px 0 6px"}}>What it ignores</div>
            <ul style={{margin:0,padding:"0 0 0 16px",fontSize:12.5,lineHeight:1.6,color:"var(--ink-3)"}}>
              {e.ignores.map((d,i)=><li key={i}>{d}</li>)}
            </ul>
          </div>
        </div>
        <div className="caveat-row" style={{marginTop:14}}>
          <Icon name="info" size={14} className="ic"/>
          <span><b>Note:</b> {e.note}</span>
        </div>
      </div>
    </div>
  );
}

function SynthesisCard() {
  return (
    <div className="card" style={{borderColor:"color-mix(in oklch, var(--primary) 28%, var(--line))"}}>
      <div className="card-head">
        <Icon name="sparkle" size={14} style={{color:"var(--primary)"}}/>
        <h3>Resolution guidance</h3>
        <div className="meta"><span>Synthesis rules · weighted engine vote</span></div>
      </div>
      <div className="card-body">
        <div style={{display:"grid",gridTemplateColumns:"1.3fr 1fr",gap:16}}>
          <div>
            <div style={{fontSize:13,lineHeight:1.6,color:"var(--ink-2)",textWrap:"pretty"}}>
              Synthesis favours <b style={{color:"var(--ink)"}}>long with trim bias</b>: weighted vote is 4 of 5 engines directional‑positive,
              confidence <b style={{color:"var(--ink)"}}>0.74</b>, and sector concentration constrains additional adds. Platform down‑weights the
              flow/options dissent while IV is stale (14m) and surfaces the recommendation as{" "}
              <b style={{color:"var(--caution-soft-ink)"}}>provisional</b> rather than assertive.
            </div>
            <div style={{marginTop:14,display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8}}>
              <div className="synth-kpi"><div className="l">Weighted stance</div><div className="v hl-pos">Long</div></div>
              <div className="synth-kpi"><div className="l">Agreement</div><div className="v">4 of 5</div></div>
              <div className="synth-kpi"><div className="l">Dispersion</div><div className="v hl-cau">0.37</div></div>
            </div>
          </div>
          <div style={{borderLeft:"1px solid var(--line)",paddingLeft:16}}>
            <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:"0.07em",color:"var(--ink-3)",fontWeight:600,marginBottom:8}}>Rules applied</div>
            <ol style={{margin:0,padding:"0 0 0 18px",fontSize:12.5,lineHeight:1.7,color:"var(--ink-2)"}}>
              <li>Down‑weight engines with <b>stale data</b> (options &gt; 10m)</li>
              <li>Use <b>median</b> price target when dispersion &gt; 10%</li>
              <li>Cap weight at <b>sector limit</b> (30% semis)</li>
              <li>Mark tone <b>provisional</b> when 1+ engine dissents on direction</li>
            </ol>
          </div>
        </div>

        <div className="action-bar" style={{borderTop:"1px solid var(--line)"}}>
          <div className="group">
            <button className="btn primary"><Icon name="check" size={14}/> Return to decision with synthesis</button>
            <button className="btn ghost"><Icon name="bookmark" size={14}/> Save alternative synthesis</button>
          </div>
          <div className="spacer"/>
          <div className="group">
            <button className="btn ghost sm"><Icon name="replay" size={12}/> Replay from snapshot</button>
            <button className="btn ghost sm"><Icon name="external" size={12}/> Methodology doc</button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ComparisonMatrix, AlignmentChart, MethodologyCard, SynthesisCard });
