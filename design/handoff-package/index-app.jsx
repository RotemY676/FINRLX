// Index — catalog of all screens
const { useEffect: useEffectIdx, useState: useStateIdx } = React;

const TWEAK_DEFAULTS_IDX = /*EDITMODE-BEGIN*/{
  "theme": "light"
}/*EDITMODE-END*/;

const SCREEN_GROUPS = [
  {
    eyebrow: "Start here",
    title: "First-run onboarding",
    sub: "How a firm gets from signup to a working tenant. Bounded, opinionated, with separation-of-duties baked in.",
    cards: [
      { file: "Onboarding.html", name: "Onboarding", id: "02 Onboarding",
        preview: "PrevOnboarding", cat: "Flow · 6 steps",
        title: "Sign in, firm setup, role, invite, review",
        desc: "Tenant-isolated setup. SSO-first (Okta, Entra, Google) with email fallback. Role selection shows the permission model before you pick.",
        tags: ["auth", "SSO", "permissions"] },
      { file: "Onboarding.html", name: "Team management",
        preview: "PrevOnboarding", cat: "Admin",
        title: "Members, roles, SSO & audit log",
        desc: "Post-onboarding admin surface. 5 tabs: Members, Pending, Roles & permissions matrix, SSO & security, Audit log.",
        tags: ["admin", "IAM"], hash: "?view=team" },
    ],
  },
  {
    eyebrow: "The work surface",
    title: "Where decisions are made",
    sub: "The heart of the product. A triage-to-decision funnel: Overview shows what needs attention, Decision workspace is where a PM actually decides, and the supporting surfaces (compare, replay) build trust in the call.",
    cards: [
      { file: "Overview.html", name: "Overview", id: "01 Overview",
        preview: "PrevOverview", cat: "Primary surface",
        title: "Morning triage, portfolio health, activity",
        desc: "The first screen each morning. Top recommendations, risk pulse, fresh evidence since yesterday's close. Designed to get a PM from zero to context in under 60 seconds.",
        tags: ["triage", "rec queue", "activity"], feat: true },
      { file: "Decision Workspace.html", name: "Decision Workspace",
        preview: "PrevDecision", cat: "Primary surface",
        title: "Single-recommendation deep dive",
        desc: "Hero with confidence trio, evidence timeline, scenario controls. Publish or ignore, with full audit trail.",
        tags: ["rec detail", "evidence", "scenarios"] },
      { file: "Engine Comparison.html", name: "Engine Comparison",
        preview: "PrevCompare", cat: "Analysis",
        title: "How each engine voted on a rec",
        desc: "Side-by-side view of value / flow / news / quality engine outputs. Disagreement is surfaced, not hidden.",
        tags: ["engines", "disagreement"] },
      { file: "Replay.html", name: "Replay",
        preview: "PrevReplay", cat: "Forensics",
        title: "Time-travel through a past decision",
        desc: "Scrub to any moment in a rec's lifecycle. What did we know? What did the engines say? What evidence arrived after we decided?",
        tags: ["time-travel", "audit"] },
    ],
  },
  {
    eyebrow: "Model lifecycle",
    title: "Propose, validate, guard",
    sub: "Everything upstream of a live decision. How new models get proposed and validated, how policies constrain what ships, how the investable universe is curated.",
    cards: [
      { file: "Backtests.html", name: "Backtests",
        preview: "PrevBacktest", cat: "Model lab",
        title: "Propose and validate new models",
        desc: "Config → run → analyze. Equity curves, drawdowns, rolling Sharpe. Candidate models get PM review before joining live engines.",
        tags: ["research", "model"] },
      { file: "Policy Editor.html", name: "Policy Editor",
        preview: "PrevPolicy", cat: "Guardrails",
        title: "Guardrails with live impact preview",
        desc: "Position limits, concentration caps, VaR ceilings. Every edit shows a diff: which recs get blocked, how exposures shift — before you save.",
        tags: ["policies", "limits"] },
      { file: "Universe.html", name: "Universe browser",
        preview: "PrevUniverse", cat: "Scope",
        title: "Which instruments are in play",
        desc: "Saved universes with filters (min mcap, ADV, liquidity, sectors), factor exposure rollup, and versioned constituent diffs before you commit.",
        tags: ["universe", "factors"] },
      { file: "Paper Portfolio.html", name: "Paper Portfolio",
        preview: "PrevPaper", cat: "Validation",
        title: "Live-but-simulated P&L",
        desc: "Recommendations that got published but not yet routed to real OMS. Track NAV, Sharpe, attribution — prove the engine earns its weight before you connect it.",
        tags: ["paper", "P&L"] },
    ],
  },
  {
    eyebrow: "Operations",
    title: "The machine that runs the machine",
    sub: "Admin surfaces. Who's connected, what's broken, and where the data comes from.",
    cards: [
      { file: "Ops.html", name: "Ops command center",
        preview: "PrevOps", cat: "Command center",
        title: "Publication queue, feeds, incidents",
        desc: "Real-time view of system health. Active incidents with affected-rec counts, feed SLOs, engine status, policy breaches — all on one screen.",
        tags: ["ops", "SRE"], feat: true },
      { file: "Integrations.html", name: "Integrations",
        preview: "PrevIntegrations", cat: "Admin",
        title: "Every data source, traceable",
        desc: "Connected feeds with schema, credentials, usage graph. Catalog of available integrations. Change log for every connect/rotate/disconnect.",
        tags: ["data", "integrations"] },
    ],
  },
  {
    eyebrow: "Craft",
    title: "Design foundations",
    sub: "The raw materials. Not product surfaces — reference material for Claude Code and anyone else building on this system.",
    cards: [
      { file: "Design System.html", name: "Design System",
        preview: "PrevDS", cat: "Reference",
        title: "Tokens, type, icons, components",
        desc: "The full kit. Color system in OKLCH, three-font stack (Fraunces / Inter Tight / JetBrains Mono), 60+ components with all states, motion primitives.",
        tags: ["tokens", "components"], feat: true },
      { file: "States.html", name: "States gallery",
        preview: "PrevStates", cat: "Reference",
        title: "Empty, loading, error, degraded, locked",
        desc: "Every surface, every state. The anti-pixel-perfect: what happens when the data is missing, slow, wrong, or forbidden.",
        tags: ["states"] },
      { file: "iOS App.html", name: "iOS App",
        preview: "PrevIOS", cat: "Mobile",
        title: "Companion mobile app",
        desc: "Today view, decision detail with scenario controls, alerts, compare, replay, watchlist. 18 screens. Same design language, native idioms.",
        tags: ["iOS", "SwiftUI"], feat: true },
    ],
  },
];

const IAMap = () => (
  <div className="idx-ia">
    <div className="idx-ia-key">
      <h4>Lanes</h4>
      <div className="idx-ia-key-row">
        <span className="sw" style={{background:"var(--primary)"}} />
        <span>Primary surfaces</span>
      </div>
      <div className="idx-ia-key-row">
        <span className="sw" style={{background:"var(--pos)"}} />
        <span>Analysis & forensics</span>
      </div>
      <div className="idx-ia-key-row">
        <span className="sw" style={{background:"var(--accent-2)"}} />
        <span>Model lifecycle</span>
      </div>
      <div className="idx-ia-key-row">
        <span className="sw" style={{background:"var(--caution)"}} />
        <span>Admin & ops</span>
      </div>
      <div style={{fontSize:11, color:"var(--ink-3)", marginTop:14, lineHeight:1.5}}>
        Each node is clickable and opens that surface.
        Arrows show the handoff — a rec moves from Overview → Decision → (Compare · Replay) before Publish.
      </div>
    </div>
    <div className="idx-ia-map">
      <div className="idx-ia-lane">
        <div className="idx-ia-lane-label">Daily flow<span className="s">triage → decide</span></div>
        <div className="idx-ia-chain">
          <a className="idx-ia-node" href="Overview.html"><span className="dot" style={{background:"var(--primary)"}}/>Overview</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Decision Workspace.html"><span className="dot" style={{background:"var(--primary)"}}/>Decision Workspace</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Engine Comparison.html"><span className="dot" style={{background:"var(--pos)"}}/>Compare</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Replay.html"><span className="dot" style={{background:"var(--pos)"}}/>Replay</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Paper Portfolio.html"><span className="dot" style={{background:"var(--accent-2)"}}/>Paper P&amp;L</a>
        </div>
      </div>
      <div className="idx-ia-lane">
        <div className="idx-ia-lane-label">Model lab<span className="s">propose → ship</span></div>
        <div className="idx-ia-chain">
          <a className="idx-ia-node" href="Universe.html"><span className="dot" style={{background:"var(--accent-2)"}}/>Universe</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Backtests.html"><span className="dot" style={{background:"var(--accent-2)"}}/>Backtest</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Policy Editor.html"><span className="dot" style={{background:"var(--accent-2)"}}/>Policy check</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Paper Portfolio.html"><span className="dot" style={{background:"var(--accent-2)"}}/>Paper</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Overview.html"><span className="dot" style={{background:"var(--primary)"}}/>Live</a>
        </div>
      </div>
      <div className="idx-ia-lane">
        <div className="idx-ia-lane-label">Admin<span className="s">setup + run</span></div>
        <div className="idx-ia-chain">
          <a className="idx-ia-node" href="Onboarding.html"><span className="dot" style={{background:"var(--caution)"}}/>Onboarding</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Integrations.html"><span className="dot" style={{background:"var(--caution)"}}/>Integrations</a>
          <span className="idx-ia-arrow">→</span>
          <a className="idx-ia-node" href="Ops.html"><span className="dot" style={{background:"var(--caution)"}}/>Ops</a>
          <span className="idx-ia-arrow">↻</span>
          <a className="idx-ia-node" href="Onboarding.html?view=team"><span className="dot" style={{background:"var(--caution)"}}/>Team mgmt</a>
        </div>
      </div>
      <div className="idx-ia-lane">
        <div className="idx-ia-lane-label">Reference<span className="s">craft</span></div>
        <div className="idx-ia-chain">
          <a className="idx-ia-node" href="Design System.html"><span className="dot" style={{background:"var(--ink-3)"}}/>Design system</a>
          <a className="idx-ia-node" href="States.html"><span className="dot" style={{background:"var(--ink-3)"}}/>States gallery</a>
          <a className="idx-ia-node" href="iOS App.html"><span className="dot" style={{background:"var(--ink-3)"}}/>iOS</a>
        </div>
      </div>
    </div>
  </div>
);

const IdxCard = ({ card }) => {
  const PreviewComp = window[card.preview];
  const href = card.hash ? `${card.file}${card.hash}` : card.file;
  return (
    <a href={href} className={"idx-card" + (card.feat ? " feat" : "")}>
      <div className="idx-card-preview">
        {PreviewComp && <PreviewComp />}
      </div>
      <div className="idx-card-body">
        <span className="tag">
          {card.cat}
        </span>
        <h3>{card.title}</h3>
        <p>{card.desc}</p>
        <div className="foot">
          <span>{card.tags.map(t => "#" + t).join(" · ")}</span>
          <span className="open">Open →</span>
        </div>
      </div>
    </a>
  );
};

function IndexApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_IDX);

  useEffectIdx(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
  }, [tweaks.theme]);

  const totalScreens = SCREEN_GROUPS.reduce((s, g) => s + g.cards.length, 0);

  return (
    <div className="idx-page" data-screen-label="00 Index">
      {/* Top strip */}
      <div className="idx-topstrip">
        <div className="brand">
          <div className="brand-mark" />
          <span>QuantPipeline<em> · design deck</em></span>
        </div>
        <div className="actions">
          <a href="HANDOFF.md" className="btn ghost sm"><Icon name="external" size={12}/> Handoff doc</a>
          <a href="Design System.html" className="btn ghost sm"><Icon name="sparkle" size={12}/> Design system</a>
          <a href="Overview.html" className="btn primary sm">Enter product →</a>
        </div>
      </div>

      {/* Hero */}
      <div className="idx-hero">
        <div>
          <div className="idx-hero-eyebrow">Internal design · Rivka Capital · v14</div>
          <h1>A decision OS for <em>quantitative</em> portfolio managers.</h1>
          <p className="idx-hero-lede">
            QuantPipeline turns an ensemble of competing models into publishable,
            auditable trades. This deck documents the full surface area — web, iOS,
            admin, design foundations — with every state and permission accounted for.
          </p>
          <div className="idx-hero-meta">
            <span><b>{totalScreens}</b> surfaces</span>
            <span><b>2</b> platforms</span>
            <span><b>4</b> roles</span>
            <span><b>60+</b> components</span>
            <span style={{color:"var(--ink-4)"}}>· ready for Claude Code handoff</span>
          </div>
        </div>
        <aside className="idx-hero-aside">
          <div className="idx-hero-aside-head">
            <h4>Project scope</h4>
            <span className="meta">internal</span>
          </div>
          <div className="idx-aside-row">
            <span className="k">Target user</span>
            <span className="v" style={{fontSize:14}}>3-8 PMs<span className="u">+ support staff</span></span>
          </div>
          <div className="idx-aside-row">
            <span className="k">AUM served</span>
            <span className="v">$400<span className="u">M – $4B</span></span>
          </div>
          <div className="idx-aside-row">
            <span className="k">Decisions / day</span>
            <span className="v">8<span className="u">–25</span></span>
          </div>
          <div className="idx-aside-row">
            <span className="k">Engines</span>
            <span className="v">4<span className="u">value · flow · news · quality</span></span>
          </div>
          <div className="idx-aside-row">
            <span className="k">Asset classes</span>
            <span className="v">6<span className="u">eq, FI, FX, macro, crypto, alt</span></span>
          </div>
          <div style={{paddingTop:10, marginTop:2, borderTop:"1px solid var(--line)", fontSize:11, color:"var(--ink-3)", lineHeight:1.5}}>
            Designed against the "<i>trust us, the model is right</i>" failure mode.
            Every recommendation traces to sources. Every decision is replayable.
          </div>
        </aside>
      </div>

      {/* IA map */}
      <div className="idx-section">
        <div className="idx-section-head">
          <div>
            <span className="eyebrow">How it fits together</span>
            <h2>Information architecture</h2>
            <p className="sub">
              Four lanes. A recommendation flows along the daily lane. New models are validated on the model-lab lane.
              Admin surfaces the full-product. Reference material stays out of the product chrome.
            </p>
          </div>
          <div className="ct">{totalScreens} surfaces · 4 lanes</div>
        </div>
        <IAMap />
      </div>

      {/* Screen groups */}
      {SCREEN_GROUPS.map((g, i) => (
        <div key={i} className="idx-section">
          <div className="idx-section-head">
            <div>
              <span className="eyebrow">{g.eyebrow}</span>
              <h2>{g.title}</h2>
              <p className="sub">{g.sub}</p>
            </div>
            <div className="ct">{g.cards.length} surface{g.cards.length > 1 ? "s" : ""}</div>
          </div>
          <div className="idx-grid">
            {g.cards.map((c, j) => (
              <IdxCard key={j} card={c} />
            ))}
          </div>
        </div>
      ))}

      {/* Footer */}
      <footer className="idx-footer">
        <div className="left">
          <b>QuantPipeline design deck</b>
          <div>Designed for Rivka Capital · v14 · April 2026</div>
          <div style={{color:"var(--ink-4)"}}>Internal reference. Not a shipping marketing page.</div>
        </div>
        <div className="resources">
          <a href="HANDOFF.md">HANDOFF.md</a>
          <a href="Design System.html">Design system</a>
          <a href="States.html">States gallery</a>
          <a href="iOS App.html">iOS reference</a>
        </div>
      </footer>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Appearance" />
        <TweakRadio label="Theme" value={tweaks.theme}
          options={["light","dark"]}
          onChange={v => setTweak("theme", v)} />
      </TweaksPanel>
    </div>
  );
}

const idxRoot = ReactDOM.createRoot(document.getElementById("root"));
idxRoot.render(<IndexApp />);
