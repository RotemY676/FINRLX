// Overview page composer
const { useState: useStateOvApp, useEffect: useEffectOvApp } = React;

const TWEAK_DEFAULTS_OV = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "layout": "two-zone",
  "showRegime": true
}/*EDITMODE-END*/;

function OverviewApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_OV);
  const [navCollapsed, setNavCollapsed] = useStateOvApp(false);

  useEffectOvApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const ctxVisible = tweaks.layout !== "two-zone";

  return (
    <div className={"app" + (ctxVisible ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="00 Overview">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setTweak("layout", ctxVisible ? "two-zone" : "three-zone")}
              ctxVisible={ctxVisible}
              crumb="Overview · Monday morning triage" />
      <LeftNav />
      <main className="canvas">
        <div className="workspace">
          <div className="page-head">
            <div>
              <h1>Good morning, Rivka</h1>
              <div className="sub ov-sub">
                <b>5 recommendations</b> need your attention today. Portfolio freshness
                is <b>94%</b>, one sector breach is approaching (Semis 28.1% / 30%),
                and the overnight regime remains <b>risk‑on · late‑cycle</b>.
              </div>
            </div>
            <div style={{display:"flex",gap:6}}>
              <button className="btn ghost sm"><Icon name="filter" size={12}/> Filters</button>
              <button className="btn ghost sm"><Icon name="external" size={12}/> Export briefing</button>
              <button className="btn primary sm"><Icon name="decision" size={12}/> Start review</button>
            </div>
          </div>

          <HealthStrip />

          <div className="ov-workspace">
            <div className="ov-main">
              <TriageTable />
              {tweaks.showRegime && <RegimeStrip />}
            </div>
            <div className="ov-side">
              <ActivityFeed />
            </div>
          </div>
        </div>
      </main>
      {ctxVisible && <ContextPane />}

      <TweaksPanel title="Tweaks">
        <TweakSection label="Appearance" />
        <TweakRadio label="Theme" value={tweaks.theme}
          options={["light","dark"]}
          onChange={v => setTweak("theme", v)} />
        <TweakRadio label="Density" value={tweaks.density}
          options={["compact","default","comfortable"]}
          onChange={v => setTweak("density", v)} />

        <TweakSection label="Layout" />
        <TweakRadio label="Shell" value={tweaks.layout}
          options={["two-zone","three-zone"]}
          onChange={v => setTweak("layout", v)} />

        <TweakSection label="Modules" />
        <TweakToggle label="Regime & posture" value={tweaks.showRegime}
          onChange={v => setTweak("showRegime", v)} />
      </TweaksPanel>
    </div>
  );
}

const ovRoot = ReactDOM.createRoot(document.getElementById("root"));
ovRoot.render(<OverviewApp />);
