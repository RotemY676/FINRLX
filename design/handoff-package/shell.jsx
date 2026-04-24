// Shell: topbar, left nav, context pane
const { useState } = React;

const Brand = () => (
  <div className="brand">
    <div className="brand-mark" />
    <div className="brand-name">QuantPipeline<em> · decision</em></div>
  </div>
);

const TopBar = ({ onToggleNav, onToggleCtx, ctxVisible, crumb }) => (
  <header className="topbar">
    <Brand />
    <button className="icon-btn" onClick={onToggleNav} title="Collapse nav">
      <Icon name="panel-left" size={15} />
    </button>
    <nav className="crumbs">
      <span>Workspaces</span>
      <Icon name="chevron-right" size={12} className="sep" />
      <span>Decisions</span>
      <Icon name="chevron-right" size={12} className="sep" />
      <span className="cur">{crumb || "NVDA · long thesis"}</span>
    </nav>
    <div className="scope-strip">
      <div className="scope-chip regime">
        <span className="dot" />
        Regime <b>Risk-on · late-cycle</b>
      </div>
      <div className="scope-chip">
        <Icon name="clock" size={12} />
        Horizon <b>3 months</b>
      </div>
      <div className="scope-chip">
        <Icon name="universe" size={12} />
        Universe <b>US-LargeCap</b>
      </div>
      <div className="topbar-search">
        <Icon name="search" size={13} />
        <input placeholder="Search recommendations, tickers, snapshots…" />
        <span className="kbd">⌘K</span>
      </div>
      <button className="icon-btn" title="Command palette"><Icon name="command" size={15} /></button>
      <button className="icon-btn" title="Notifications">
        <Icon name="bell" size={15} />
        <span className="bell-dot" />
      </button>
      <button className="icon-btn" onClick={onToggleCtx} title="Toggle context pane">
        <Icon name="panel-right" size={15} style={{ opacity: ctxVisible ? 1 : 0.45 }} />
      </button>
      <div className="avatar">RM</div>
    </div>
  </header>
);

const LeftNav = () => {
  const page = (typeof window !== "undefined" && window.__PAGE) || "decision";
  const items = [
    { key: "overview", label: "Overview", icon: "overview", badge: "4", href: "Overview.html" },
    { key: "decision", label: "Decisions", icon: "decision", badge: "12", href: "Decision Workspace.html" },
    { key: "compare", label: "Engine comparison", icon: "compare", href: "Engine Comparison.html" },
    { key: "risk", label: "Risk workspace", icon: "risk", badge: "2", href: "#" },
    { key: "replay", label: "Replay & forensics", icon: "replay", href: "#" },
    { key: "backtest", label: "Backtests", icon: "backtest", href: "#" },
    { key: "paper", label: "Paper portfolio", icon: "paper", href: "#" },
    { key: "universe", label: "Universe", icon: "universe", href: "#" },
    { key: "news", label: "News intelligence", icon: "news", href: "#" },
  ];
  const saved = [
    { label: "Momentum leaders · 3M", c: "" },
    { label: "Breach watch · concentration", c: "a" },
    { label: "Fresh changes · today", c: "g" },
    { label: "Post-mortem cases", c: "r" },
  ];
  return (
    <aside className="leftnav">
      <div className="nav-section">
        <div className="nav-label">Workspaces</div>
        {items.map(it => (
          <a key={it.key} href={it.href} className={"nav-item" + (it.key === page ? " active" : "")}>
            <Icon name={it.icon} size={16} className="nav-ic" />
            <span>{it.label}</span>
            {it.badge && <span className="nav-badge">{it.badge}</span>}
          </a>
        ))}
      </div>
      <div className="nav-section">
        <div className="nav-label">Operations</div>
        <div className="nav-item">
          <Icon name="ops" size={16} className="nav-ic" />
          <span>Ops command</span>
          <span className="nav-badge">1</span>
        </div>
      </div>
      <div className="nav-section">
        <div className="nav-label">Saved views</div>
        <div className="nav-saved">
          {saved.map((s, i) => (
            <div className="saved-item" key={i}>
              <span className={"sw " + s.c} />
              <span>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

Object.assign(window, { Brand, TopBar, LeftNav });
