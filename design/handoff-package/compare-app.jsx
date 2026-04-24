// Compare App — Engine Comparison workspace
const { useState: useStateCmpA, useEffect: useEffectCmpA } = React;

const TWEAK_DEFAULTS_CMP = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "layout": "three-zone",
  "showAlignment": true
}/*EDITMODE-END*/;

function CompareApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_CMP);
  const [navCollapsed, setNavCollapsed] = useStateCmpA(false);
  const [selected, setSelected] = useStateCmpA("momentum");

  useEffectCmpA(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const ctxVisible = tweaks.layout !== "two-zone";

  return (
    <div className={"app" + (ctxVisible ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="02 Engine Comparison">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setTweak("layout", ctxVisible ? "two-zone" : "three-zone")}
              ctxVisible={ctxVisible}
              crumb="NVDA · engine comparison" />
      <LeftNav />
      <main className="canvas">
        <div className="workspace">
          <div className="page-head">
            <div>
              <h1>Engine comparison</h1>
              <div className="sub">
                Five engines scored <b>NVDA</b> for the 3-month horizon. They agree on
                direction <b>4 of 5</b>, but disagree on <b>magnitude and timing</b>.
                Review methodology, reconcile, and return to the decision with a synthesis.
              </div>
            </div>
            <div style={{display:"flex",gap:6}}>
              <a href="Decision Workspace.html" className="btn ghost sm" style={{textDecoration:"none"}}>
                <Icon name="chevron-right" size={12} style={{transform:"rotate(180deg)"}} /> Back to decision
              </a>
              <button className="btn ghost sm"><Icon name="external" size={12} /> Methodology</button>
            </div>
          </div>

          <div className="tab-row">
            <div className="tab active">Matrix</div>
            <div className="tab">Timeline</div>
            <div className="tab">Historical agreement</div>
            <div className="tab">Methodology</div>
          </div>

          <ComparisonMatrix selected={selected} onSelect={setSelected} />

          {tweaks.showAlignment ? (
            <div className="grid-2">
              <AlignmentChart />
              <MethodologyCard selected={selected} />
            </div>
          ) : (
            <MethodologyCard selected={selected} />
          )}

          <SynthesisCard />
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
        <TweakToggle label="Alignment chart" value={tweaks.showAlignment}
          onChange={v => setTweak("showAlignment", v)} />
      </TweaksPanel>
    </div>
  );
}

const cmpRoot = ReactDOM.createRoot(document.getElementById("root"));
cmpRoot.render(<CompareApp />);
