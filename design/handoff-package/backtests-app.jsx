// Backtests app composer
const { useState: useStateBtApp, useEffect: useEffectBtApp } = React;

const TWEAK_DEFAULTS_BT = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "default",
  "activeRun": "run-momx3",
  "showBench": true
}/*EDITMODE-END*/;

function BacktestsApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_BT);
  const [navCollapsed, setNavCollapsed] = useStateBtApp(false);
  const [ctxOpen, setCtxOpen] = useStateBtApp(false);
  const [active, setActive] = useStateBtApp(tweaks.activeRun);
  const [compareIds, setCompareIds] = useStateBtApp(["run-valmom", "run-rvn"]);

  useEffectBtApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
    document.documentElement.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.density]);

  const run = BT_RUNS.find(r => r.id === active) || BT_RUNS[0];
  const comparisons = BT_RUNS.filter(r => compareIds.includes(r.id) && r.id !== active);

  return (
    <div className={"app" + (ctxOpen ? "" : " no-context") + (navCollapsed ? " nav-collapsed" : "")}
         data-screen-label="05 Backtests">
      <TopBar onToggleNav={() => setNavCollapsed(v => !v)}
              onToggleCtx={() => setCtxOpen(v => !v)}
              ctxVisible={ctxOpen}
              crumb={"Backtests · " + run.name} />
      <LeftNav />
      <main className="canvas">
        <div className="bt-page">
          <StrategyBar run={run} />
          <div className="bt-body">
            <RunsList active={active} onSelect={id => { setActive(id); setTweak("activeRun", id); }} />
            <BtMain run={run} comparisons={comparisons} />
            <TradeBlotter />
          </div>
          <CompareStrip
            comparisons={comparisons}
            onRemove={id => setCompareIds(ids => ids.filter(x => x !== id))}
            onAdd={() => {
              const next = BT_RUNS.find(r => !compareIds.includes(r.id) && r.id !== active);
              if (next) setCompareIds(ids => [...ids, next.id]);
            }}
          />
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

        <TweakSection label="Run" />
        <TweakSelect label="Active strategy" value={active}
          options={BT_RUNS.map(r => ({ value: r.id, label: r.name }))}
          onChange={v => { setActive(v); setTweak("activeRun", v); }} />
        <TweakToggle label="Show SPY benchmark" value={tweaks.showBench}
          onChange={v => setTweak("showBench", v)} />
      </TweaksPanel>
    </div>
  );
}

const btRoot = ReactDOM.createRoot(document.getElementById("root"));
btRoot.render(<BacktestsApp />);
