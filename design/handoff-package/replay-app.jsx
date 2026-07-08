// Replay app — orchestrates scrubber state + renders the workspace
const ReplayApp = () => {
  const [t, setT] = React.useState(0.66);  // default cursor on "Trim 30%"
  const [playing, setPlaying] = React.useState(false);
  const [speed, setSpeed] = React.useState(1);
  const [navOpen, setNavOpen] = React.useState(true);
  const [ctxOpen, setCtxOpen] = React.useState(false);

  // Play loop
  React.useEffect(() => {
    if (!playing) return;
    let raf;
    let last = performance.now();
    const tick = (now) => {
      const dt = (now - last) / 1000;
      last = now;
      setT(prev => {
        const nxt = prev + dt * 0.08 * speed;
        if (nxt >= 1) { setPlaying(false); return 1; }
        return nxt;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed]);

  const eventIdx = eventIndexForT(t);
  const event = REPLAY_EVENTS[eventIdx];
  const stateNow = REPLAY_ENGINE_STATES[eventIdx];
  const statePrev = eventIdx > 0 ? REPLAY_ENGINE_STATES[eventIdx - 1] : null;
  const now = interpPrice(t);

  return (
    <div className={"app" + (navOpen ? "" : " nav-collapsed") + (ctxOpen ? "" : " no-context")}>
      <TopBar
        onToggleNav={() => setNavOpen(v => !v)}
        onToggleCtx={() => setCtxOpen(v => !v)}
        ctxVisible={ctxOpen}
        crumb="NVDA · replay"
      />
      <LeftNav />
      <main className="workspace rp-page">
        <ReplayHeader
          event={event}
          priceNow={now.p}
          priceEntry={612.40}
          pos={now.pos}
        />
        <Scrubber
          t={t}
          onT={setT}
          playing={playing}
          onPlay={() => setPlaying(p => !p)}
          speed={speed}
          onSpeed={setSpeed}
          event={event}
        />
        <div className="rp-body">
          <EnginePanel stateNow={stateNow} statePrev={statePrev} />
          <ChartPanel t={t} />
          <LogPanel t={t} onJump={setT} />
        </div>
        <CounterfactualFooter eventIdx={eventIdx} />
      </main>
      {ctxOpen && <ContextPane />}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<ReplayApp />);
