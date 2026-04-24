// Main App: composition + tweaks
const { useState: useStateApp, useEffect: useEffectApp } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "layout": "three-zone",
  "showBand": true,
  "showDisagreement": true
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [navCollapsed, setNavCollapsed] = useStateApp(false);

  useEffectApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const ctxVisible = tweaks.layout !== "two-zone";

  return (
    <div className={"app" + (ctxVisible ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="01 Decision Workspace">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setTweak("layout", ctxVisible ? "two-zone" : "three-zone")}
              ctxVisible={ctxVisible} />
      <LeftNav />
      <main className="canvas">
        <div className="workspace">
          <div className="page-head">
            <div>
              <h1>Decision workspace</h1>
              <div className="sub">
                Review, challenge, and publish the thesis for <b>NVDA</b>.
                Last re-scored <b>12 min ago</b> · next automated refresh in 18 min.
              </div>
            </div>
            <div style={{display:"flex",gap:6}}>
              <button className="btn ghost sm"><Icon name="pin" size={12} /> Pin</button>
              <button className="btn ghost sm"><Icon name="external" size={12} /> Open full</button>
            </div>
          </div>

          <div className="tab-row">
            <div className="tab active">Thesis <span className="pill">v4</span></div>
            <div className="tab">Evidence</div>
            <div className="tab">Challenge <span className="pill">3</span></div>
            <div className="tab">Risk</div>
            <div className="tab">History</div>
            <div className="tab">Methodology</div>
          </div>

          <HeroStrip tweaks={tweaks} />

          <div className="grid-2">
            <EvidenceCard />
            <RiskCard />
          </div>

          <ChartCard tweaks={tweaks} />

          {tweaks.showDisagreement ? (
            <div className="grid-2">
              <ScenarioCard />
              <DisagreementCard />
            </div>
          ) : (
            <ScenarioCard />
          )}
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
          options={["three-zone","two-zone"]}
          onChange={v => setTweak("layout", v)} />

        <TweakSection label="Modules" />
        <TweakToggle label="Engine disagreement" value={tweaks.showDisagreement}
          onChange={v => setTweak("showDisagreement", v)} />
        <TweakToggle label="Confidence band" value={tweaks.showBand}
          onChange={v => setTweak("showBand", v)} />
      </TweaksPanel>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
