// Chart: price + feature contribution + events
const ChartCard = ({ tweaks }) => {
  // simulated series
  const points = [
    { x: 0, y: 62, e: null },
    { x: 1, y: 60 },
    { x: 2, y: 64 },
    { x: 3, y: 67, e: "Q4 earnings · beat +8%" },
    { x: 4, y: 66 },
    { x: 5, y: 71 },
    { x: 6, y: 74 },
    { x: 7, y: 70, e: "Sector downgrade" },
    { x: 8, y: 73 },
    { x: 9, y: 79 },
    { x: 10, y: 82 },
    { x: 11, y: 85 },
    { x: 12, y: 83 },
    { x: 13, y: 88, e: "Guidance raise" },
    { x: 14, y: 92 },
    { x: 15, y: 89 },
    { x: 16, y: 94 },
    { x: 17, y: 91 },
    { x: 18, y: 95 },
  ];
  const bench = points.map((p, i) => ({ x: p.x, y: 60 + i * 1.2 + Math.sin(i*0.7)*1.8 }));
  const W = 720, H = 220, L = 40, R = 10, T = 12, B = 28;
  const sx = i => L + (i / (points.length - 1)) * (W - L - R);
  const sy = v => T + (1 - (v - 55) / 45) * (H - T - B);
  const line = pts => pts.map((p, i) => (i ? "L" : "M") + sx(i) + "," + sy(p.y)).join(" ");
  const area = pts => line(pts) + ` L ${sx(pts.length-1)},${H - B} L ${sx(0)},${H - B} Z`;
  const band = points.map((p, i) => ({ x: sx(i), top: sy(p.y + 4 + i*0.15), bot: sy(p.y - 4 - i*0.15) }));
  const bandPath = "M " + band.map(b => b.x + "," + b.top).join(" L ") +
                   " L " + [...band].reverse().map(b => b.x + "," + b.bot).join(" L ") + " Z";
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="trend-up" size={14} />
        <h3>Price, attribution & events</h3>
        <div className="meta">
          <div style={{display:"inline-flex",gap:2,padding:2,border:"1px solid var(--line)",borderRadius:6,background:"var(--surface-2)"}}>
            {["1M","3M","6M","1Y","3Y"].map((t,i)=>(
              <button key={t} className="btn sm" style={{height:22,padding:"0 9px",fontSize:11.5,
                background: t === "3M" ? "var(--surface)" : "transparent",
                border: t === "3M" ? "1px solid var(--line-strong)" : "1px solid transparent",
                color: t === "3M" ? "var(--ink)" : "var(--ink-3)"}}>{t}</button>
            ))}
          </div>
          <button className="btn ghost sm"><Icon name="eye" size={12} /> Overlays</button>
        </div>
      </div>
      <div className="card-body">
        <div className="chart-wrap" style={{padding:0,height:260}}>
          <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
            <defs>
              <linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.18" />
                <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* gridlines */}
            {[0.25, 0.5, 0.75].map(p => (
              <line key={p} x1={L} x2={W - R} y1={T + p*(H-T-B)} y2={T + p*(H-T-B)}
                    stroke="var(--line)" strokeDasharray="2 3" />
            ))}
            {/* y labels */}
            {[100, 85, 70, 55].map((v, i) => (
              <text key={v} x={L - 8} y={T + i * ((H-T-B)/3) + 4} fontSize="10.5"
                    textAnchor="end" fill="var(--ink-4)"
                    style={{fontFamily:"var(--font-mono)"}}>{v}</text>
            ))}
            {/* confidence band */}
            {tweaks.showBand && (
              <path d={bandPath} fill="var(--primary)" opacity="0.08" />
            )}
            {/* benchmark */}
            <path d={line(bench)} fill="none" stroke="var(--ink-4)" strokeWidth="1.5"
                  strokeDasharray="4 3" />
            {/* area */}
            <path d={area(points)} fill="url(#areaFill)" />
            {/* price line */}
            <path d={line(points)} fill="none" stroke="var(--primary)" strokeWidth="2" />
            {/* event markers */}
            {points.map((p, i) => p.e && (
              <g key={i}>
                <line x1={sx(i)} x2={sx(i)} y1={sy(p.y)-4} y2={T+6}
                      stroke="var(--caution)" strokeDasharray="2 2" />
                <circle cx={sx(i)} cy={sy(p.y)} r="4" fill="var(--surface)"
                        stroke="var(--caution)" strokeWidth="2" />
                <rect x={sx(i)-3} y={T} width={p.e.length*5.2+14} height={16} rx={4}
                      className="event-tag" />
                <text x={sx(i)+4} y={T+11} className="event-tag-text">{p.e}</text>
              </g>
            ))}
            {/* x axis labels */}
            {["Jan","Feb","Mar","Apr"].map((m, i) => (
              <text key={m} x={L + (i+0.5) * (W-L-R)/4} y={H - 8} fontSize="10.5"
                    textAnchor="middle" fill="var(--ink-4)"
                    style={{fontFamily:"var(--font-mono)"}}>{m}</text>
            ))}
            {/* current price dot */}
            <circle cx={sx(points.length-1)} cy={sy(points[points.length-1].y)} r="5"
                    fill="var(--primary)" stroke="var(--surface)" strokeWidth="2" />
          </svg>
        </div>
        <div className="chart-legend">
          <span className="item"><span className="sw" style={{background:"var(--primary)"}}/> NVDA <b>+52.4% 3M</b></span>
          <span className="item"><span className="sw" style={{background:"var(--ink-4)"}}/> SOXX <b>+19.1% 3M</b></span>
          {tweaks.showBand && <span className="item"><span className="sw" style={{background:"color-mix(in oklch, var(--primary) 20%, transparent)"}}/> Confidence band 80%</span>}
          <span className="item" style={{marginLeft:"auto",color:"var(--ink-3)"}}>
            <Icon name="info" size={12} style={{marginRight:4}} />
            Direct-labeled · 3 event markers
          </span>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { ChartCard });
