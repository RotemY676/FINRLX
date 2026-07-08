// Small, consistent line icon set — single stroke-weight, meaningful only alongside labels.
const Icon = ({ name, size = 16, className = "", strokeWidth = 1.6, style }) => {
  const p = { width: size, height: size, viewBox: "0 0 24 24", fill: "none",
    stroke: "currentColor", strokeWidth, strokeLinecap: "round", strokeLinejoin: "round",
    className, style };
  switch (name) {
    case "overview": return (<svg {...p}><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>);
    case "decision": return (<svg {...p}><path d="M12 2 22 8v8l-10 6L2 16V8Z"/><path d="m7 10 5 3 5-3"/><path d="M12 13v8"/></svg>);
    case "compare": return (<svg {...p}><path d="M8 3v18M16 3v18"/><path d="M3 8h5M3 16h5M16 8h5M16 16h5"/></svg>);
    case "risk": return (<svg {...p}><path d="M12 3 2 20h20Z"/><path d="M12 10v4M12 17v.5"/></svg>);
    case "replay": return (<svg {...p}><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>);
    case "backtest": return (<svg {...p}><path d="M3 3v18h18"/><path d="m7 15 4-5 3 3 6-7"/></svg>);
    case "paper": return (<svg {...p}><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>);
    case "universe": return (<svg {...p}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>);
    case "news": return (<svg {...p}><path d="M4 5h13a2 2 0 0 1 2 2v12a2 2 0 0 0 2-2V8"/><path d="M4 5v14a2 2 0 0 0 2 2h13"/><path d="M8 9h7M8 13h7M8 17h4"/></svg>);
    case "ops": return (<svg {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .4 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.4 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.4l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .4-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.4-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.4h0a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5h0a1.7 1.7 0 0 0 1.9-.4l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.4 1.9v0a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>);
    case "search": return (<svg {...p}><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>);
    case "bell": return (<svg {...p}><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></svg>);
    case "bookmark": return (<svg {...p}><path d="M19 21 12 16l-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z"/></svg>);
    case "command": return (<svg {...p}><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3Z"/></svg>);
    case "chevron-right": return (<svg {...p}><path d="m9 6 6 6-6 6"/></svg>);
    case "chevron-down": return (<svg {...p}><path d="m6 9 6 6 6-6"/></svg>);
    case "arrow-up-right": return (<svg {...p}><path d="M7 17 17 7M8 7h9v9"/></svg>);
    case "arrow-down-right": return (<svg {...p}><path d="M7 7l10 10M17 8v9H8"/></svg>);
    case "trend-up": return (<svg {...p}><path d="M3 17 9 11l4 4 8-9"/><path d="M14 6h7v7"/></svg>);
    case "plus": return (<svg {...p}><path d="M12 5v14M5 12h14"/></svg>);
    case "minus": return (<svg {...p}><path d="M5 12h14"/></svg>);
    case "check": return (<svg {...p}><path d="M5 12l5 5L20 7"/></svg>);
    case "alert-triangle": return (<svg {...p}><path d="M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17v.5"/></svg>);
    case "info": return (<svg {...p}><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>);
    case "history": return (<svg {...p}><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/></svg>);
    case "panel-left": return (<svg {...p}><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>);
    case "panel-right": return (<svg {...p}><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/></svg>);
    case "external": return (<svg {...p}><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>);
    case "share": return (<svg {...p}><path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7"/><path d="m16 6-4-4-4 4"/><path d="M12 2v13"/></svg>);
    case "pin": return (<svg {...p}><path d="m12 17-5 5"/><path d="M9 11V4h6v7l3 3H6Z"/></svg>);
    case "dots": return (<svg {...p}><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg>);
    case "filter": return (<svg {...p}><path d="M3 4h18l-7 9v6l-4-2v-4Z"/></svg>);
    case "eye": return (<svg {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>);
    case "clock": return (<svg {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>);
    case "database": return (<svg {...p}><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>);
    case "tag": return (<svg {...p}><path d="M20.5 12.5 12 21l-9-9V3h9Z"/><circle cx="7.5" cy="7.5" r="1"/></svg>);
    case "sparkle": return (<svg {...p}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></svg>);
    case "close": return (<svg {...p}><path d="M6 6l12 12M18 6L6 18"/></svg>);
    default: return null;
  }
};
window.Icon = Icon;
