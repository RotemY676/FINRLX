// Ops Command Center — page composer

const { useState: useStateOpsApp, useEffect: useEffectOpsApp, useRef: useRefOpsApp } = React;

const TWEAK_DEFAULTS_OPS = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "layout": "2col",
  "pulse": true,
  "bulkMode": false,
  "showSystem": true,
  "showQueue": true,
  "showFeeds": true,
  "showEngines": true,
  "showBreaches": true,
  "showIncidents": true,
  "showAudit": true
}/*EDITMODE-END*/;

function OpsApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_OPS);
  const [navCollapsed, setNavCollapsed] = useStateOpsApp(false);
  const [selectedRec, setSelectedRec] = useStateOpsApp("REC-2026-0419-XOM-S");
  const [activeIncident, setActiveIncident] = useStateOpsApp(null);
  const [lastRefresh, setLastRefresh] = useStateOpsApp("just now");
  const tickRef = useRefOpsApp(0);

  useEffectOpsApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  // Ambient refresh ticker
  useEffectOpsApp(() => {
    if (!tweaks.pulse) return;
    const id = setInterval(() => {
      tickRef.current++;
      const labels = ["just now", "1s ago", "3s ago", "5s ago", "8s ago"];
      setLastRefresh(labels[tickRef.current % labels.length]);
    }, 2500);
    return () => clearInterval(id);
  }, [tweaks.pulse]);

  return (
    <div className={"app" + (navCollapsed ? " nav-collapsed" : "") + " no-context"}
         data-screen-label="05 Ops">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              crumb="Ops · Command center" />
      <LeftNav />
      <main className="canvas">
        <div className="workspace">
          <div className="page-head">
            <div>
              <h1>Ops command center</h1>
              <div className="sub ov-sub">
                <b>2 active incidents</b>, <b>7 recs in queue</b>,
                and one <b>hard policy breach</b> on energy exposure.
                Feed coverage at <b>87%</b> with two degraded sources.
                Last refresh <span style={{fontFamily:"var(--font-mono)",fontSize:12,color:"var(--ink-3)"}}>{lastRefresh}</span>.
              </div>
            </div>
            <div style={{display:"flex",gap:6,alignItems:"center"}}>
              <div style={{
                display:"flex", alignItems:"center", gap:6,
                padding:"4px 10px",
                border:"1px solid var(--line)",
                borderRadius:"var(--r-md)",
                background:"var(--surface-2)",
                fontSize:11, color:"var(--ink-3)"
              }}>
                <span className="ops-pulse" style={{"--pc":"var(--pos)"}}>
                  <span className="dot"/>{tweaks.pulse && <span className="ring"/>}
                </span>
                <span style={{fontFamily:"var(--font-mono)"}}>Live · {lastRefresh}</span>
              </div>
              <button className="btn ghost sm"><Icon name="filter" size={12}/> Filters</button>
              <button className="btn ghost sm" onClick={()=>setLastRefresh("just now")}>
                <Icon name="replay" size={12}/> Refresh now
              </button>
              <button className="btn primary sm"><Icon name="check" size={12}/> Approve queue</button>
            </div>
          </div>

          {tweaks.showSystem && <ModSystemStrip />}

          <div className={"ops-workspace layout-" + tweaks.layout}>
            <div className="ops-main">
              {tweaks.showQueue && (
                <ModQueue
                  selected={selectedRec}
                  onSelect={setSelectedRec}
                  bulkMode={tweaks.bulkMode}
                />
              )}
              {tweaks.showBreaches && <ModBreaches onOpen={()=>{}} />}
              {tweaks.showEngines && <ModEngines />}
              {tweaks.layout === "stack" && tweaks.showFeeds && <ModFeeds pulse={tweaks.pulse} />}
              {tweaks.layout === "stack" && tweaks.showIncidents && <ModIncidents onOpen={setActiveIncident} />}
              {tweaks.showAudit && <ModAudit />}
            </div>

            {tweaks.layout === "2col" && (
              <div className="ops-side">
                {tweaks.showIncidents && <ModIncidents onOpen={setActiveIncident} />}
                {tweaks.showFeeds && <ModFeeds pulse={tweaks.pulse} />}
              </div>
            )}
          </div>
        </div>
      </main>

      {activeIncident && (
        <IncidentDrawer incident={activeIncident} onClose={()=>setActiveIncident(null)} />
      )}

      <TweaksPanel title="Tweaks">
        <TweakSection label="Appearance" />
        <TweakRadio label="Theme" value={tweaks.theme}
          options={["light","dark"]}
          onChange={v => setTweak("theme", v)} />
        <TweakRadio label="Density" value={tweaks.density}
          options={["compact","default","comfortable"]}
          onChange={v => setTweak("density", v)} />

        <TweakSection label="Layout" />
        <TweakRadio label="Shape" value={tweaks.layout}
          options={["2col","stack"]}
          onChange={v => setTweak("layout", v)} />

        <TweakSection label="Behavior" />
        <TweakToggle label="Ambient pulse" value={tweaks.pulse}
          onChange={v => setTweak("pulse", v)} />
        <TweakToggle label="Bulk‑approve mode" value={tweaks.bulkMode}
          onChange={v => setTweak("bulkMode", v)} />

        <TweakSection label="Modules" />
        <TweakToggle label="System strip" value={tweaks.showSystem}
          onChange={v => setTweak("showSystem", v)} />
        <TweakToggle label="Publication queue" value={tweaks.showQueue}
          onChange={v => setTweak("showQueue", v)} />
        <TweakToggle label="Policy breaches" value={tweaks.showBreaches}
          onChange={v => setTweak("showBreaches", v)} />
        <TweakToggle label="Engine health" value={tweaks.showEngines}
          onChange={v => setTweak("showEngines", v)} />
        <TweakToggle label="Data sources" value={tweaks.showFeeds}
          onChange={v => setTweak("showFeeds", v)} />
        <TweakToggle label="Active incidents" value={tweaks.showIncidents}
          onChange={v => setTweak("showIncidents", v)} />
        <TweakToggle label="Audit log" value={tweaks.showAudit}
          onChange={v => setTweak("showAudit", v)} />
      </TweaksPanel>
    </div>
  );
}

const opsRoot = ReactDOM.createRoot(document.getElementById("root"));
opsRoot.render(<OpsApp />);
