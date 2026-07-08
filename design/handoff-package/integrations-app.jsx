// Integrations — app composer
const { useState: useStateIgApp, useEffect: useEffectIgApp, useMemo: useMemoIgApp } = React;

const TWEAK_DEFAULTS_IG = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "tab": "connected"
}/*EDITMODE-END*/;

function IntegrationsApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_IG);
  const [navCollapsed, setNavCollapsed] = useStateIgApp(false);
  const [tab, setTab] = useStateIgApp(tweaks.tab);
  const [query, setQuery] = useStateIgApp("");
  const [cat, setCat] = useStateIgApp("all");
  const [openDetail, setOpenDetail] = useStateIgApp(null);
  const [openCatalog, setOpenCatalog] = useStateIgApp(null);

  useEffectIgApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const stats = useMemoIgApp(() => ({
    ok: IG_ACTIVE.filter(i => i.status === "ok").length,
    degraded: IG_ACTIVE.filter(i => i.status === "degraded").length,
    paused: IG_ACTIVE.filter(i => i.status === "paused").length,
    total: IG_ACTIVE.length,
  }), []);

  const filteredActive = IG_ACTIVE.filter(ig => {
    if (cat !== "all" && ig.catId !== cat) return false;
    if (query && !(ig.name.toLowerCase().includes(query.toLowerCase()) || ig.desc.toLowerCase().includes(query.toLowerCase()) || ig.cat.toLowerCase().includes(query.toLowerCase()))) return false;
    return true;
  });

  const filteredCatalog = IG_CATALOG.filter(ig => {
    if (cat !== "all" && ig.catId !== cat) return false;
    if (query && !(ig.name.toLowerCase().includes(query.toLowerCase()) || ig.desc.toLowerCase().includes(query.toLowerCase()))) return false;
    return true;
  });

  return (
    <div className={"app" + (navCollapsed ? " nav-collapsed" : "") + " no-context"}
         data-screen-label="09 Integrations">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => {}}
              ctxVisible={false}
              crumb="Admin · Integrations" />
      <LeftNav />
      <main className="canvas">
        <div className="ig-page">
          <IgHero stats={stats} />
          <IgTabs tab={tab} setTab={(t) => { setTab(t); setTweak("tab", t); }}
                  counts={{ connected: IG_ACTIVE.length, catalog: IG_CATALOG.length }} />
          <div className="ig-body">
            {(tab === "connected" || tab === "catalog") && (
              <IgFilterBar query={query} setQuery={setQuery} cat={cat} setCat={setCat} />
            )}

            {tab === "connected" && (
              <>
                <div className="ig-section-head">
                  <div>
                    <h2>Active integrations</h2>
                    <div className="sub">{filteredActive.length} of {IG_ACTIVE.length} shown · click any row to inspect schema, usage, and credentials.</div>
                  </div>
                </div>
                <div className="ig-list">
                  {filteredActive.map(ig => (
                    <IgRow key={ig.id} ig={ig} onOpen={setOpenDetail} />
                  ))}
                  {filteredActive.length === 0 && (
                    <div style={{padding:"40px 20px", textAlign:"center", color:"var(--ink-3)", fontSize:13, border:"1px dashed var(--line)", borderRadius:"var(--r-lg)"}}>
                      No connected integrations match this filter. Try the <a onClick={() => setTab("catalog")} style={{color:"var(--primary)", cursor:"pointer"}}>Catalog</a>.
                    </div>
                  )}
                </div>
              </>
            )}

            {tab === "catalog" && (
              <>
                <div className="ig-section-head">
                  <div>
                    <h2>Available integrations</h2>
                    <div className="sub">{filteredCatalog.length} available · 14-day trial on paid feeds · no contract required.</div>
                  </div>
                </div>
                <div className="ig-catalog">
                  {filteredCatalog.map(ig => (
                    <IgCatalogCard key={ig.id} ig={ig} onOpen={setOpenCatalog} />
                  ))}
                </div>
              </>
            )}

            {tab === "history" && <IgChangeLog />}
            {tab === "keys" && <IgApiKeys />}
          </div>
        </div>
      </main>

      {openDetail && <IgDrawer ig={openDetail} onClose={() => setOpenDetail(null)} />}
      {openCatalog && <IgCatalogDrawer ig={openCatalog} onClose={() => setOpenCatalog(null)} />}

      <TweaksPanel title="Tweaks">
        <TweakSection label="View" />
        <TweakRadio label="Tab" value={tab}
          options={["connected","catalog","history","keys"]}
          onChange={v => { setTab(v); setTweak("tab", v); }} />
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

const igRoot = ReactDOM.createRoot(document.getElementById("root"));
igRoot.render(<IntegrationsApp />);
