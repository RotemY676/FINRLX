// Index — miniature SVG previews of each screen
// These are evocative abstractions, not screenshots — consistent tokens, minimal detail.

const PrevOverview = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    {/* Top strip */}
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="10" y="8" width="40" height="6" rx="2" fill="var(--ink-4)"/>
    <rect x="260" y="7" width="8" height="8" rx="2" fill="var(--primary)"/>
    {/* Left nav */}
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    <rect x="8" y="32" width="20" height="3" rx="1" fill="var(--primary)"/>
    <rect x="8" y="42" width="16" height="3" rx="1" fill="var(--ink-4)"/>
    <rect x="8" y="52" width="18" height="3" rx="1" fill="var(--ink-4)"/>
    <rect x="8" y="62" width="14" height="3" rx="1" fill="var(--ink-4)"/>
    {/* Big stat tiles */}
    <rect x="44" y="30" width="60" height="42" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="50" y="38" width="16" height="2" rx="1" fill="var(--ink-4)"/>
    <text x="50" y="58" fontFamily="Fraunces, serif" fontSize="14" fill="var(--pos)" fontWeight="500">+2.4%</text>
    <rect x="110" y="30" width="60" height="42" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="116" y="38" width="16" height="2" rx="1" fill="var(--ink-4)"/>
    <text x="116" y="58" fontFamily="Fraunces, serif" fontSize="14" fill="var(--ink)" fontWeight="500">7</text>
    <rect x="176" y="30" width="60" height="42" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="182" y="38" width="16" height="2" rx="1" fill="var(--ink-4)"/>
    <text x="182" y="58" fontFamily="Fraunces, serif" fontSize="14" fill="var(--caution)" fontWeight="500">1.24σ</text>
    <rect x="242" y="30" width="68" height="42" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="248" y="38" width="18" height="2" rx="1" fill="var(--ink-4)"/>
    <text x="248" y="58" fontFamily="Fraunces, serif" fontSize="14" fill="var(--ink)" fontWeight="500">0.74</text>
    {/* Queue rows */}
    <rect x="44" y="82" width="170" height="88" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="50" y="90" width="50" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <rect x="50" y={102 + i*16} width="28" height="5" rx="1" fill={i === 0 ? "var(--pos)" : i === 1 ? "var(--caution)" : "var(--ink-4)"}/>
        <rect x="82" y={102 + i*16} width="80" height="3" rx="1" fill="var(--ink-4)"/>
        <rect x="82" y={108 + i*16} width="50" height="2" rx="1" fill="var(--ink-4)" opacity="0.4"/>
        <rect x="172" y={103 + i*16} width="28" height="5" rx="2" fill={i === 0 ? "var(--pos-soft)" : "var(--surface-3)"}/>
      </g>
    ))}
    {/* Activity rail */}
    <rect x="220" y="82" width="90" height="88" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="226" y="90" width="40" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <circle cx="230" cy={104 + i*14} r="2" fill="var(--primary)"/>
        <rect x="236" y={102 + i*14} width="60" height="2" rx="1" fill="var(--ink-4)"/>
        <rect x="236" y={107 + i*14} width="40" height="2" rx="1" fill="var(--ink-4)" opacity="0.4"/>
      </g>
    ))}
  </svg>
);

const PrevDecision = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="10" y="8" width="60" height="6" rx="2" fill="var(--ink-4)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    <rect x="8" y="32" width="18" height="3" rx="1" fill="var(--ink-4)"/>
    <rect x="8" y="42" width="20" height="3" rx="1" fill="var(--primary)"/>
    {/* Hero card */}
    <rect x="44" y="30" width="200" height="72" rx="6" fill="var(--surface)" stroke="var(--line)"/>
    <text x="54" y="52" fontFamily="Fraunces, serif" fontSize="15" fontWeight="500" fill="var(--ink)">Long NVDA</text>
    <rect x="54" y="58" width="50" height="14" rx="7" fill="var(--pos-soft)"/>
    <text x="60" y="68" fontFamily="system-ui" fontSize="9" fontWeight="600" fill="var(--pos-soft-ink)">BUY · strong</text>
    <rect x="110" y="62" width="26" height="3" rx="1" fill="var(--ink-4)"/>
    <rect x="110" y="70" width="40" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
    {/* Trio confidence */}
    <rect x="160" y="48" width="78" height="46" rx="4" fill="var(--canvas)"/>
    <rect x="168" y="56" width="20" height="12" rx="2" fill="var(--pos)" opacity="0.7"/>
    <rect x="168" y="72" width="16" height="2" rx="1" fill="var(--ink-4)"/>
    <rect x="194" y="56" width="16" height="12" rx="2" fill="var(--caution)" opacity="0.6"/>
    <rect x="194" y="72" width="12" height="2" rx="1" fill="var(--ink-4)"/>
    <rect x="216" y="56" width="16" height="12" rx="2" fill="var(--primary)" opacity="0.5"/>
    <rect x="216" y="72" width="12" height="2" rx="1" fill="var(--ink-4)"/>
    {/* Context pane */}
    <rect x="252" y="30" width="64" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="258" y="38" width="30" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3].map(i => (
      <rect key={i} x="258" y={50 + i*18} width="52" height="12" rx="2" fill="var(--surface-2)"/>
    ))}
    {/* Evidence timeline */}
    <rect x="44" y="110" width="200" height="60" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="54" y="118" width="40" height="3" rx="1" fill="var(--ink-3)"/>
    <line x1="54" y1="148" x2="234" y2="148" stroke="var(--line)" strokeDasharray="2,3"/>
    {[58, 88, 118, 148, 178, 208].map((x, i) => (
      <circle key={i} cx={x} cy="148" r="3" fill={i % 3 === 0 ? "var(--primary)" : "var(--ink-4)"}/>
    ))}
    <polyline points="58,140 88,134 118,138 148,130 178,125 208,120" fill="none" stroke="var(--primary)" strokeWidth="1.5"/>
  </svg>
);

const PrevCompare = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    <rect x="8" y="52" width="18" height="3" rx="1" fill="var(--primary)"/>
    {/* 4 engine columns */}
    {[0,1,2,3].map(col => {
      const colors = ["var(--primary)", "var(--pos)", "var(--accent-2)", "var(--caution)"];
      const x = 48 + col*68;
      return (
        <g key={col}>
          <rect x={x} y="30" width="60" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
          <rect x={x + 6} y="40" width="30" height="3" rx="1" fill="var(--ink-3)"/>
          <rect x={x + 6} y="50" width="48" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
          {/* Signal dots */}
          {[0,1,2,3,4].map(i => (
            <g key={i}>
              <rect x={x + 6} y={64 + i*18} width="22" height="2" rx="1" fill="var(--ink-4)"/>
              <rect x={x + 30} y={60 + i*18} width={8 + (col + i) % 3 * 6} height="10" rx="2" fill={colors[col]} opacity={0.5 + i*0.1}/>
            </g>
          ))}
        </g>
      );
    })}
    {/* Disagreement banner */}
    <rect x="48" y="154" width="264" height="14" rx="3" fill="var(--caution-soft)"/>
    <rect x="56" y="159" width="4" height="4" rx="2" fill="var(--caution)"/>
    <rect x="64" y="160" width="100" height="2" rx="1" fill="var(--caution-soft-ink)"/>
  </svg>
);

const PrevPolicy = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    {/* Left: policy list */}
    <rect x="44" y="30" width="120" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="52" y="40" width="50" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3,4,5].map(i => (
      <g key={i}>
        <rect x="52" y={54 + i*18} width="104" height="14" rx="3" fill={i === 1 ? "var(--primary-soft)" : "var(--surface-2)"}/>
        <rect x="58" y={58 + i*18} width="3" height="6" rx="1" fill={["var(--pos)","var(--primary)","var(--caution)","var(--ink-4)","var(--breach)","var(--ink-4)"][i]}/>
        <rect x="66" y={59 + i*18} width="50" height="2" rx="1" fill={i === 1 ? "var(--primary-soft-ink)" : "var(--ink-2)"}/>
        <rect x="66" y={64 + i*18} width="30" height="2" rx="1" fill="var(--ink-4)" opacity="0.6"/>
      </g>
    ))}
    {/* Right: impact preview */}
    <rect x="172" y="30" width="140" height="80" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="180" y="40" width="50" height="3" rx="1" fill="var(--ink-3)"/>
    <text x="180" y="66" fontFamily="Fraunces, serif" fontSize="16" fill="var(--primary)" fontWeight="500">−3 recs</text>
    <rect x="180" y="76" width="100" height="2" rx="1" fill="var(--ink-4)"/>
    <rect x="180" y="82" width="80" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
    <rect x="180" y="92" width="120" height="12" rx="2" fill="var(--pos-soft)"/>
    {/* Sliders */}
    <rect x="172" y="118" width="140" height="52" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2].map(i => (
      <g key={i}>
        <rect x="180" y={128 + i*14} width="60" height="2" rx="1" fill="var(--ink-4)"/>
        <line x1="180" y1={134 + i*14} x2="300" y2={134 + i*14} stroke="var(--line-strong)" strokeWidth="2" strokeLinecap="round"/>
        <line x1="180" y1={134 + i*14} x2={210 + i*20} y2={134 + i*14} stroke="var(--primary)" strokeWidth="2" strokeLinecap="round"/>
        <circle cx={210 + i*20} cy={134 + i*14} r="3" fill="var(--surface)" stroke="var(--primary)" strokeWidth="1.5"/>
      </g>
    ))}
  </svg>
);

const PrevReplay = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    {/* Scrubber */}
    <rect x="20" y="40" width="280" height="32" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <line x1="32" y1="56" x2="288" y2="56" stroke="var(--line-strong)" strokeWidth="1"/>
    {[50, 80, 110, 140, 170, 200, 230, 260].map((x, i) => (
      <line key={i} x1={x} y1="52" x2={x} y2="60" stroke="var(--ink-4)" strokeWidth="1"/>
    ))}
    {/* Current marker */}
    <line x1="180" y1="44" x2="180" y2="68" stroke="var(--primary)" strokeWidth="2"/>
    <circle cx="180" cy="56" r="4" fill="var(--primary)"/>
    <rect x="155" y="26" width="50" height="14" rx="3" fill="var(--primary)"/>
    <text x="163" y="36" fontFamily="JetBrains Mono, monospace" fontSize="8" fill="white" fontWeight="600">09:14:22</text>
    {/* Reconstructed state below */}
    <rect x="20" y="82" width="132" height="88" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="28" y="92" width="40" height="3" rx="1" fill="var(--ink-3)"/>
    <rect x="28" y="104" width="90" height="5" rx="1" fill="var(--pos)"/>
    <rect x="28" y="114" width="80" height="3" rx="1" fill="var(--ink-4)"/>
    <rect x="28" y="122" width="100" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
    <rect x="28" y="128" width="100" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
    {/* Event list */}
    <rect x="160" y="82" width="140" height="88" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <circle cx="170" cy={96 + i*18} r="2" fill={i === 0 ? "var(--primary)" : "var(--ink-4)"}/>
        <line x1="170" y1={99 + i*18} x2="170" y2={114 + i*18} stroke="var(--line)" strokeDasharray="2,2"/>
        <rect x="178" y={93 + i*18} width="60" height="2" rx="1" fill="var(--ink-2)"/>
        <rect x="178" y={98 + i*18} width="40" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
        <rect x="260" y={93 + i*18} width="30" height="2" rx="1" fill="var(--ink-4)"/>
      </g>
    ))}
  </svg>
);

const PrevBacktest = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    {/* Main chart */}
    <rect x="20" y="34" width="220" height="100" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <line x1="30" y1="124" x2="230" y2="124" stroke="var(--line)"/>
    <line x1="30" y1="44" x2="30" y2="124" stroke="var(--line)"/>
    {/* Two series */}
    <polyline points="30,110 50,108 70,100 90,96 110,90 130,82 150,78 170,70 190,64 210,58 230,52"
              fill="none" stroke="var(--primary)" strokeWidth="2"/>
    <polyline points="30,110 50,112 70,108 90,106 110,100 130,98 150,92 170,88 190,82 210,76 230,70"
              fill="none" stroke="var(--ink-4)" strokeWidth="1.5" strokeDasharray="3,2"/>
    <rect x="40" y="40" width="80" height="3" rx="1" fill="var(--ink-3)"/>
    {/* Stats */}
    <rect x="248" y="34" width="64" height="100" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <rect x="254" y={42 + i*22} width="40" height="2" rx="1" fill="var(--ink-4)"/>
        <text x="254" y={58 + i*22} fontFamily="Fraunces, serif" fontSize="12" fill={i === 0 ? "var(--pos)" : "var(--ink)"} fontWeight="500">
          {["+24%", "1.84", "−8.2%", "62%"][i]}
        </text>
      </g>
    ))}
    {/* Parameters */}
    <rect x="20" y="144" width="292" height="26" rx="3" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <rect x={30 + i*70} y="152" width="40" height="2" rx="1" fill="var(--ink-4)"/>
        <rect x={30 + i*70} y="158" width="54" height="6" rx="2" fill="var(--surface-3)"/>
      </g>
    ))}
  </svg>
);

const PrevOps = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    {/* Status strip */}
    <rect x="44" y="30" width="268" height="28" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[
      {c: "var(--pos)", l: "142"},
      {c: "var(--caution)", l: "14m"},
      {c: "var(--primary)", l: "7"},
      {c: "var(--breach)", l: "1"},
    ].map((s, i) => (
      <g key={i}>
        <circle cx={60 + i*67} cy="44" r="3" fill={s.c}/>
        <text x={68 + i*67} y="48" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="600" fill="var(--ink)">{s.l}</text>
      </g>
    ))}
    {/* Feed grid */}
    <rect x="44" y="66" width="130" height="104" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="52" y="74" width="50" height="3" rx="1" fill="var(--ink-3)"/>
    {[
      {c: "var(--pos)"},{c: "var(--pos)"},{c: "var(--caution)"},
      {c: "var(--pos)"},{c: "var(--pos)"},{c: "var(--ink-4)"}
    ].map((f, i) => (
      <g key={i}>
        <circle cx="58" cy={92 + i*12} r="3" fill={f.c}>
          {f.c === "var(--pos)" && <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite"/>}
        </circle>
        <rect x="68" y={90 + i*12} width="70" height="2" rx="1" fill="var(--ink-2)"/>
        <rect x="68" y={95 + i*12} width="40" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
      </g>
    ))}
    {/* Incidents */}
    <rect x="182" y="66" width="130" height="104" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="190" y="74" width="40" height="3" rx="1" fill="var(--ink-3)"/>
    <rect x="190" y="86" width="114" height="34" rx="3" fill="var(--caution-soft)"/>
    <rect x="196" y="92" width="60" height="2" rx="1" fill="var(--caution-soft-ink)"/>
    <rect x="196" y="98" width="80" height="2" rx="1" fill="var(--caution-soft-ink)" opacity="0.7"/>
    <rect x="196" y="105" width="36" height="10" rx="2" fill="var(--surface)"/>
    <rect x="190" y="130" width="114" height="34" rx="3" fill="var(--surface-2)"/>
    <rect x="196" y="136" width="50" height="2" rx="1" fill="var(--ink-2)"/>
    <rect x="196" y="142" width="80" height="2" rx="1" fill="var(--ink-4)" opacity="0.7"/>
  </svg>
);

const PrevPaper = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    {/* NAV + chart */}
    <rect x="44" y="30" width="190" height="80" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <text x="56" y="54" fontFamily="Fraunces, serif" fontSize="18" fontWeight="500" fill="var(--ink)">$1.24M</text>
    <text x="110" y="54" fontFamily="Fraunces, serif" fontSize="14" fill="var(--pos)" fontWeight="500">+$48.2K</text>
    <polyline points="54,96 74,92 94,86 114,88 134,80 154,78 174,70 194,66 214,60 224,56"
              fill="none" stroke="var(--pos)" strokeWidth="1.5"/>
    <polyline points="54,96 74,92 94,86 114,88 134,80 154,78 174,70 194,66 214,60 224,56 224,104 54,104"
              fill="var(--pos)" opacity="0.1" stroke="none"/>
    {/* KPI stack */}
    <rect x="240" y="30" width="72" height="80" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2].map(i => (
      <g key={i}>
        <rect x="248" y={40 + i*22} width="30" height="2" rx="1" fill="var(--ink-4)"/>
        <text x="248" y={56 + i*22} fontFamily="Fraunces, serif" fontSize="12" fontWeight="500" fill={i === 2 ? "var(--breach)" : "var(--ink)"}>
          {["1.62", "0.84", "−6.2%"][i]}
        </text>
      </g>
    ))}
    {/* Positions table */}
    <rect x="44" y="118" width="268" height="52" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2].map(i => (
      <g key={i}>
        <rect x="54" y={128 + i*14} width="24" height="4" rx="1" fill="var(--ink-2)" opacity={1 - i*0.15}/>
        <rect x="88" y={128 + i*14} width="80" height="4" rx="1" fill="var(--ink-4)"/>
        <rect x="180" y={128 + i*14} width="30" height="4" rx="1" fill={i === 2 ? "var(--breach)" : "var(--pos)"}/>
        <rect x="240" y={128 + i*14} width="50" height="4" rx="1" fill="var(--ink-4)"/>
      </g>
    ))}
  </svg>
);

const PrevUniverse = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    {/* Universe list */}
    <rect x="44" y="30" width="60" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[0,1,2,3].map(i => (
      <g key={i}>
        <rect x="50" y={38 + i*30} width="48" height="24" rx="3" fill={i === 0 ? "var(--primary-soft)" : "transparent"}/>
        <rect x="54" y={44 + i*30} width="36" height="2" rx="1" fill={i === 0 ? "var(--primary-soft-ink)" : "var(--ink-2)"}/>
        <rect x="54" y={50 + i*30} width="24" height="2" rx="1" fill="var(--ink-4)" opacity="0.6"/>
      </g>
    ))}
    {/* Constituents table */}
    <rect x="110" y="30" width="140" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="116" y="38" width="20" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3,4,5].map(i => (
      <g key={i}>
        <rect x="116" y={52 + i*18} width="18" height="4" rx="1" fill="var(--ink)"/>
        <rect x="140" y={52 + i*18} width="30" height="3" rx="1" fill="var(--ink-4)"/>
        {[0,1,2,3,4].map(j => (
          <rect key={j} x={176 + j*14} y={52 + i*18} width="10" height="4" rx="1"
                fill={(i + j) % 3 === 0 ? "var(--pos)" : (i + j) % 3 === 1 ? "var(--caution)" : "var(--ink-4)"} opacity={0.6}/>
        ))}
      </g>
    ))}
    {/* Factor bars */}
    <rect x="256" y="30" width="56" height="140" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <rect x="262" y="38" width="30" height="3" rx="1" fill="var(--ink-3)"/>
    {[0,1,2,3,4].map(i => (
      <g key={i}>
        <rect x="262" y={54 + i*22} width="30" height="2" rx="1" fill="var(--ink-4)"/>
        <line x1="262" y1={62 + i*22} x2="306" y2={62 + i*22} stroke="var(--line)" strokeWidth="1"/>
        <line x1="284" y1={58 + i*22} x2="284" y2={66 + i*22} stroke="var(--line-strong)" strokeWidth="1"/>
        <rect x={i % 2 === 0 ? 284 : 272} y={60 + i*22} width={i % 2 === 0 ? 16 : 12} height="4" rx="1"
              fill={i % 2 === 0 ? "var(--primary)" : "var(--breach)"} opacity="0.8"/>
      </g>
    ))}
  </svg>
);

const PrevOnboarding = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <defs>
      <radialGradient id="obg" cx="90%" cy="0%" r="100%">
        <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.15"/>
        <stop offset="100%" stopColor="transparent"/>
      </radialGradient>
    </defs>
    <rect width="320" height="180" fill="var(--surface)"/>
    <rect width="320" height="180" fill="url(#obg)"/>
    {/* Stepper */}
    <rect x="0" y="0" width="320" height="28" fill="var(--surface)" stroke="var(--line)" strokeWidth="0"/>
    <line x1="0" y1="28" x2="320" y2="28" stroke="var(--line)"/>
    {[0,1,2,3,4].map(i => {
      const cx = 92 + i*34;
      const active = i === 2;
      const done = i < 2;
      return (
        <g key={i}>
          {i > 0 && <line x1={cx - 28} y1="14" x2={cx - 10} y2="14" stroke="var(--line-strong)" strokeWidth="1"/>}
          <circle cx={cx} cy="14" r="8" fill={active ? "var(--primary)" : done ? "var(--pos-soft)" : "var(--surface-3)"}
                  stroke={active ? "var(--primary)" : done ? "transparent" : "var(--line)"}/>
          <text x={cx} y="17" textAnchor="middle" fontFamily="system-ui" fontSize="9" fontWeight="600"
                fill={active ? "white" : done ? "var(--pos-soft-ink)" : "var(--ink-3)"}>
            {done ? "✓" : (i + 1)}
          </text>
        </g>
      );
    })}
    {/* Form card */}
    <rect x="50" y="46" width="220" height="120" rx="8" fill="var(--canvas)" stroke="var(--line)"/>
    <rect x="62" y="58" width="30" height="10" rx="5" fill="var(--primary-soft)"/>
    <text x="64" y="65" fontFamily="system-ui" fontSize="6" fontWeight="600" fill="var(--primary-soft-ink)">STEP 3/5</text>
    <text x="62" y="86" fontFamily="Fraunces, serif" fontSize="14" fontWeight="500" fill="var(--ink)">What's your role?</text>
    {[
      {c: "var(--primary-soft)", label: "Admin", active: true},
      {c: "var(--surface-2)", label: "PM"},
      {c: "var(--surface-2)", label: "Analyst"},
    ].map((r, i) => (
      <g key={i}>
        <rect x="62" y={96 + i*20} width="196" height="16" rx="4" fill={r.c} stroke={r.active ? "var(--primary)" : "var(--line)"}/>
        <circle cx="72" cy={104 + i*20} r="3" fill={r.active ? "var(--primary)" : "var(--surface)"} stroke={r.active ? "var(--primary)" : "var(--line-strong)"}/>
        <rect x="84" y={102 + i*20} width="60" height="2" rx="1" fill="var(--ink-2)"/>
        <rect x="84" y={107 + i*20} width="100" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
      </g>
    ))}
  </svg>
);

const PrevIntegrations = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    <rect x="0" y="22" width="36" height="158" fill="var(--surface)"/>
    {/* Stats strip */}
    <rect x="44" y="30" width="268" height="24" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    {[
      {v: "7", l: "Connected", c: "var(--pos-soft-ink)"},
      {v: "1", l: "Degraded", c: "var(--caution-soft-ink)"},
      {v: "1", l: "Paused", c: "var(--ink-3)"},
      {v: "$9.5K", l: "Spend", c: "var(--ink)"}
    ].map((s, i) => (
      <g key={i}>
        <text x={60 + i*66} y="42" fontFamily="Fraunces, serif" fontSize="11" fontWeight="500" fill={s.c}>{s.v}</text>
        <text x={60 + i*66} y="49" fontFamily="system-ui" fontSize="6" fill="var(--ink-4)">{s.l}</text>
      </g>
    ))}
    {/* Integration rows */}
    {[
      {n: "Bloomberg", mark: "B", c: "var(--ink)", status: "var(--pos)"},
      {n: "Refinitiv", mark: "R", c: "var(--breach)", status: "var(--pos)"},
      {n: "CBOE Flow", mark: "C", c: "var(--primary)", status: "var(--caution)"},
      {n: "FactSet",   mark: "F", c: "var(--accent-2)", status: "var(--pos)"},
      {n: "Reuters",   mark: "R", c: "var(--breach)", status: "var(--pos)"},
    ].map((ig, i) => (
      <g key={i}>
        <rect x="44" y={62 + i*22} width="268" height="18" rx="4" fill="var(--surface)" stroke="var(--line)"/>
        <rect x="50" y={66 + i*22} width="10" height="10" rx="2" fill={ig.c}/>
        <text x="55" y={74 + i*22} textAnchor="middle" fontFamily="system-ui" fontSize="7" fontWeight="700" fill="white">{ig.mark}</text>
        <rect x="66" y={68 + i*22} width="60" height="2" rx="1" fill="var(--ink)"/>
        <rect x="66" y={73 + i*22} width="80" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
        <circle cx="200" cy={71 + i*22} r="3" fill={ig.status}/>
        <rect x="210" y={70 + i*22} width="30" height="2" rx="1" fill="var(--ink-4)"/>
        <rect x="260" y={68 + i*22} width="40" height="6" rx="2" fill="var(--surface-3)"/>
      </g>
    ))}
  </svg>
);

const PrevDS = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface)"/>
    {/* Serif heading */}
    <text x="24" y="40" fontFamily="Fraunces, serif" fontSize="22" fontWeight="400" fill="var(--ink)">Aa</text>
    <text x="24" y="62" fontFamily="Inter Tight, system-ui" fontSize="13" fontWeight="500" fill="var(--ink-2)">Design system</text>
    {/* Color swatches */}
    <rect x="24" y="80" width="24" height="40" rx="4" fill="var(--primary)"/>
    <rect x="52" y="80" width="24" height="40" rx="4" fill="var(--pos)"/>
    <rect x="80" y="80" width="24" height="40" rx="4" fill="var(--caution)"/>
    <rect x="108" y="80" width="24" height="40" rx="4" fill="var(--breach)"/>
    <rect x="136" y="80" width="24" height="40" rx="4" fill="var(--accent)"/>
    <rect x="164" y="80" width="24" height="40" rx="4" fill="var(--accent-2)"/>
    <rect x="192" y="80" width="24" height="40" rx="4" fill="var(--ink)"/>
    <rect x="220" y="80" width="24" height="40" rx="4" fill="var(--ink-3)"/>
    {/* Type scale */}
    <text x="24" y="138" fontFamily="Fraunces, serif" fontSize="18" fontWeight="500" fill="var(--ink)">Headline</text>
    <text x="24" y="156" fontFamily="Inter Tight, system-ui" fontSize="12" fill="var(--ink-2)">Body text · multiple weights</text>
    <text x="24" y="170" fontFamily="JetBrains Mono, monospace" fontSize="10" fill="var(--ink-3)">0.62 · +2.1σ · numeric</text>
    {/* Components sample */}
    <rect x="210" y="135" width="90" height="30" rx="6" fill="var(--primary)"/>
    <text x="222" y="154" fontFamily="Inter Tight, system-ui" fontSize="11" fontWeight="600" fill="var(--primary-ink)">Primary action</text>
    <rect x="248" y="80" width="64" height="24" rx="4" fill="var(--surface)" stroke="var(--line)"/>
    <circle cx="258" cy="92" r="3" fill="var(--pos)"/>
    <rect x="264" y="88" width="40" height="2" rx="1" fill="var(--ink-2)"/>
    <rect x="264" y="94" width="30" height="2" rx="1" fill="var(--ink-4)"/>
  </svg>
);

const PrevStates = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <rect width="320" height="180" fill="var(--surface-2)"/>
    <rect x="0" y="0" width="320" height="22" fill="var(--surface)"/>
    {/* 6 state tiles */}
    {[
      {l: "default", c: "var(--primary)", bg: "var(--surface)"},
      {l: "loading", c: "var(--ink-4)",   bg: "var(--surface-2)", anim: true},
      {l: "empty",   c: "var(--ink-4)",   bg: "var(--surface-2)"},
      {l: "degraded", c: "var(--caution)", bg: "var(--caution-soft)"},
      {l: "error",   c: "var(--breach)",  bg: "var(--breach-soft)"},
      {l: "locked",  c: "var(--ink-3)",   bg: "var(--surface-2)"},
    ].map((s, i) => {
      const x = 16 + (i % 3) * 102;
      const y = 40 + Math.floor(i / 3) * 72;
      return (
        <g key={s.l}>
          <rect x={x} y={y} width="90" height="60" rx="5" fill={s.bg} stroke="var(--line)"/>
          <rect x={x + 8} y={y + 8} width="40" height="3" rx="1" fill={s.c}/>
          <text x={x + 8} y={y + 30} fontFamily="Fraunces, serif" fontSize="12" fontWeight="500" fill={s.c}>
            {s.l}
          </text>
          {s.anim ? (
            <>
              <rect x={x + 8} y={y + 40} width="74" height="3" rx="1" fill="var(--line-strong)" opacity="0.5">
                <animate attributeName="width" values="20;74;20" dur="1.4s" repeatCount="indefinite"/>
              </rect>
              <rect x={x + 8} y={y + 48} width="50" height="3" rx="1" fill="var(--line-strong)" opacity="0.3"/>
            </>
          ) : (
            <>
              <rect x={x + 8} y={y + 40} width="50" height="2" rx="1" fill="var(--ink-4)" opacity="0.5"/>
              <rect x={x + 8} y={y + 46} width="70" height="2" rx="1" fill="var(--ink-4)" opacity="0.4"/>
            </>
          )}
        </g>
      );
    })}
  </svg>
);

const PrevIOS = () => (
  <svg className="idx-prev" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="iosbg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="var(--surface-2)"/>
        <stop offset="100%" stopColor="var(--canvas)"/>
      </linearGradient>
    </defs>
    <rect width="320" height="180" fill="url(#iosbg)"/>
    {/* 3 phone mockups */}
    {[
      {x: 50, status: "var(--pos)"},
      {x: 132, status: "var(--caution)"},
      {x: 214, status: "var(--primary)"},
    ].map((p, i) => (
      <g key={i}>
        <rect x={p.x} y="18" width="56" height="144" rx="10" fill="var(--ink)" opacity="0.95"/>
        <rect x={p.x + 3} y="21" width="50" height="138" rx="8" fill="var(--surface)"/>
        {/* notch */}
        <rect x={p.x + 20} y="23" width="16" height="3" rx="1.5" fill="var(--ink)"/>
        {/* content */}
        <rect x={p.x + 8} y="34" width="40" height="3" rx="1" fill="var(--ink-3)"/>
        <rect x={p.x + 8} y="44" width="24" height="2" rx="1" fill="var(--ink-4)" opacity="0.6"/>
        {/* rec card */}
        <rect x={p.x + 8} y="54" width="40" height="44" rx="4" fill="var(--surface-2)" stroke="var(--line)"/>
        <rect x={p.x + 12} y="60" width="18" height="3" rx="1" fill="var(--ink)"/>
        <rect x={p.x + 12} y="68" width="14" height="6" rx="3" fill={p.status}/>
        <rect x={p.x + 12} y="80" width="28" height="2" rx="1" fill="var(--ink-4)"/>
        <rect x={p.x + 12} y="85" width="20" height="2" rx="1" fill="var(--ink-4)" opacity="0.6"/>
        {/* secondary */}
        <rect x={p.x + 8} y="104" width="40" height="20" rx="3" fill="var(--surface-2)"/>
        <rect x={p.x + 12} y="110" width="24" height="2" rx="1" fill="var(--ink-3)"/>
        <rect x={p.x + 12} y="116" width="18" height="2" rx="1" fill="var(--ink-4)"/>
        {/* tab bar */}
        <rect x={p.x + 3} y="146" width="50" height="13" fill="var(--surface-2)"/>
        {[0,1,2,3].map(t => (
          <circle key={t} cx={p.x + 11 + t*11} cy="152" r="1.5" fill={t === 0 ? "var(--primary)" : "var(--ink-4)"}/>
        ))}
      </g>
    ))}
  </svg>
);

Object.assign(window, {
  PrevOverview, PrevDecision, PrevCompare, PrevPolicy, PrevReplay, PrevBacktest,
  PrevOps, PrevPaper, PrevUniverse, PrevOnboarding, PrevIntegrations, PrevDS, PrevStates, PrevIOS,
});
