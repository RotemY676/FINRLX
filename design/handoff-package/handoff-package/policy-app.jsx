// Policy editor — app shell
const { useState: useStatePolApp } = React;

const filterByCat = (cat) => {
  if (cat === "all") return POLICIES;
  if (cat === "active") return POLICIES.filter(p => p.on);
  if (cat === "draft") return POLICIES.filter(p => p.draft);
  return POLICIES.filter(p => p.cat === cat);
};

const PolicyApp = () => {
  const [navOpen, setNavOpen] = useStatePolApp(true);
  const [ctxOpen, setCtxOpen] = useStatePolApp(false);
  const [cat, setCat] = useStatePolApp("all");
  const [expanded, setExpanded] = useStatePolApp("pol-exp-sector");
  const [toggles, setToggles] = useStatePolApp(() =>
    Object.fromEntries(POLICIES.map(p => [p.id, p.on]))
  );

  const visible = filterByCat(cat);
  const activePolicies = POLICIES.filter(p => toggles[p.id]);

  const catLabel = cat === "all" ? "All rules"
    : cat === "active" ? "Active rules"
    : cat === "draft" ? "Draft rules"
    : POLICY_CATEGORIES.find(c => c.key === cat)?.label || cat;

  return (
    <div className={"app" + (navOpen ? "" : " nav-collapsed") + (ctxOpen ? "" : " no-context")}>
      <TopBar
        onToggleNav={() => setNavOpen(v => !v)}
        onToggleCtx={() => setCtxOpen(v => !v)}
        ctxVisible={ctxOpen}
        crumb="Policies"
      />
      <LeftNav />
      <main className="workspace" style={{ padding: 0, overflow: "hidden" }}>
        <div className="pol-page">
          <PolicyTree active={cat} onPick={setCat} />
          <div className="pol-main">
            <div className="pol-main-head">
              <div>
                <h1>{catLabel}</h1>
                <div className="sub">
                  Guardrails run on every recommendation before publication. Rules compose; the most restrictive wins. Changes go live after save.
                </div>
              </div>
              <div className="pol-main-head-actions">
                <button className="btn ghost">Import YAML</button>
                <button className="btn ghost">History</button>
                <button className="btn primary">+ New rule</button>
              </div>
            </div>

            <div className="pol-list">
              <div className="pol-diff-banner">
                <span className="ic"><Icon name="alert-triangle" size={18} /></span>
                <div className="pol-diff-text">
                  You have <b>2 unsaved rule changes</b>. Simulated impact: <b>+1 blocked</b>, <b>−1 warned</b> vs. current live policy set.
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="pol-btn ghost">Discard</button>
                  <button className="pol-btn primary">Publish changes</button>
                </div>
              </div>

              {visible.map(p => (
                <PolicyCard
                  key={p.id}
                  pol={p}
                  expanded={expanded === p.id}
                  onToggleExpand={() => setExpanded(expanded === p.id ? null : p.id)}
                  on={!!toggles[p.id]}
                  onToggleOn={() => setToggles(t => ({ ...t, [p.id]: !t[p.id] }))}
                />
              ))}
            </div>
          </div>
          <PolicySidePanel policies={activePolicies} />
        </div>
      </main>
      {ctxOpen && <ContextPane />}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<PolicyApp />);
