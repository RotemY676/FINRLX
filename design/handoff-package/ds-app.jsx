// Design System — page composer
const { useState: useStateDSApp, useEffect: useEffectDSApp } = React;

function DSApp() {
  const [theme, setTheme] = useStateDSApp("light");
  const [active, setActive] = useStateDSApp("colors");

  useEffectDSApp(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffectDSApp(() => {
    const ids = NAV.flatMap(g => g.items.map(([id]) => id));
    const onScroll = () => {
      let current = ids[0];
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top < 120) current = id;
      }
      setActive(current);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="ds-shell">
      <DSSidebar active={active}/>
      <main className="ds-main">
        <header className="ds-hero">
          <h1>QuantPipeline · Design System</h1>
          <p>
            A living reference for the tokens, type, icons, and components that make up the
            QuantPipeline product surface. Treat <code>styles.css</code> as the source of
            truth; everything here is a rendered demonstration of those tokens in real DOM.
          </p>
          <div className="badges">
            <span className="ds-badge">v0.1 · prototype</span>
            <span className="ds-badge">React + CSS vars</span>
            <span className="ds-badge">light + dark</span>
            <span className="ds-badge">3 densities</span>
          </div>
        </header>

        <ColorsSection/>
        <SpacingSection/>
        <RadiiShadowsSection/>
        <MotionSection/>
        <TypeSection/>
        <IconsSection/>
        <Tier1Section/>
        <Tier2Section/>
        <Tier3Section/>
        <PatternsSection/>
        <StatesSection/>
      </main>

      <DSThemeToggle theme={theme} onChange={setTheme}/>
    </div>
  );
}

const dsRoot = ReactDOM.createRoot(document.getElementById("root"));
dsRoot.render(<DSApp/>);
