// Universe browser — app composer
const { useState: useStateUnApp, useEffect: useEffectUnApp } = React;

const TWEAK_DEFAULTS_UN = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "activeUniverse": "us-lc-500"
}/*EDITMODE-END*/;

function UniverseApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_UN);
  const [navCollapsed, setNavCollapsed] = useStateUnApp(false);
  const [ctxOpen, setCtxOpen] = useStateUnApp(false);
  const [activeId, setActiveId] = useStateUnApp(tweaks.activeUniverse);
  const [rows, setRows] = useStateUnApp(CONSTITUENTS);
  const [filters, setFilters] = useStateUnApp(FILTER_DEFAULTS);
  const [search, setSearch] = useStateUnApp("");

  useEffectUnApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const active = UNIVERSES.find(u => u.id === activeId) || UNIVERSES[0];

  const filtered = rows.filter(r => {
    if (search && !(r.tk.toLowerCase().includes(search.toLowerCase()) || r.name.toLowerCase().includes(search.toLowerCase()))) return false;
    if (filters.basketOnly && !r.inBasket) return false;
    return true;
  });

  const toggleRow = (tk) => setRows(rs => rs.map(r => r.tk === tk ? { ...r, inBasket: !r.inBasket } : r));

  return (
    <div className={"app" + (ctxOpen ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="07 Universe browser">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setCtxOpen(v => !v)}
              ctxVisible={ctxOpen}
              crumb={"Universe · " + active.name} />
      <LeftNav />
      <main className="canvas">
        <div className="un-page">
          <UnBar active={active} />
          <div className="un-body">
            <UniverseList activeId={activeId} onSelect={id => { setActiveId(id); setTweak("activeUniverse", id); }} />
            <div className="un-main">
              <div className="un-search">
                <input
                  placeholder="Search ticker, name, or sector…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
                <div className="un-search-actions">
                  <button className="btn ghost sm"><Icon name="filter" size={12}/></button>
                  <button className="btn ghost sm"><kbd className="kbd">⌘K</kbd></button>
                </div>
              </div>
              <FilterRow filters={filters} setFilters={setFilters} />
              <DiffBanner rows={filtered} />
              <ConstituentsTable rows={filtered} onToggle={toggleRow} />
            </div>
            <FactorPanel rows={filtered} />
          </div>
        </div>
      </main>
      {ctxOpen && <ContextPane />}

      <TweaksPanel title="Tweaks">
        <TweakSection label="Appearance" />
        <TweakRadio label="Theme" value={tweaks.theme}
          options={["light","dark"]}
          onChange={v => setTweak("theme", v)} />
        <TweakRadio label="Density" value={tweaks.density}
          options={["compact","default","comfortable"]}
          onChange={v => setTweak("density", v)} />
      </TweaksPanel>
    </div>
  );
}

const unRoot = ReactDOM.createRoot(document.getElementById("root"));
unRoot.render(<UniverseApp />);
