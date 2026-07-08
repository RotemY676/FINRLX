// Paper portfolio — app composer
const { useState: useStatePpApp, useEffect: useEffectPpApp } = React;

const TWEAK_DEFAULTS_PP = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "showDivergence": true
}/*EDITMODE-END*/;

function PaperApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_PP);
  const [navCollapsed, setNavCollapsed] = useStatePpApp(false);
  const [ctxOpen, setCtxOpen] = useStatePpApp(false);

  useEffectPpApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  return (
    <div className={"app" + (ctxOpen ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="06 Paper portfolio">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setCtxOpen(v => !v)}
              ctxVisible={ctxOpen}
              crumb={"Paper · " + PAPER_STRATEGY.name} />
      <LeftNav />
      <main className="canvas">
        <div className="pp-page">
          <PaperBar strat={PAPER_STRATEGY} />
          {tweaks.showDivergence && <DivergenceBanner d={PAPER_DIVERGENCE} />}
          <div className="pp-body">
            <div className="pp-main">
              <PaperKpis />
              <PaperChartCard />
              <ExposureCard />
              <PositionsTable />
            </div>
            <div className="pp-side">
              <FillsPanel />
            </div>
          </div>
          <PromoteFooter strat={PAPER_STRATEGY} />
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

        <TweakSection label="Layout" />
        <TweakToggle label="Show divergence banner" value={tweaks.showDivergence}
          onChange={v => setTweak("showDivergence", v)} />
      </TweaksPanel>
    </div>
  );
}

const ppRoot = ReactDOM.createRoot(document.getElementById("root"));
ppRoot.render(<PaperApp />);
