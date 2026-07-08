// Design System — data, sections, renderers
const { useState: useStateDS, useEffect: useEffectDS } = React;

// ─────── Token catalog ───────
const COLOR_GROUPS = [
  {
    name: "Canvas & surfaces",
    tokens: [
      ["--canvas", "page background"],
      ["--surface", "card / sheet"],
      ["--surface-2", "subtle surface"],
      ["--surface-3", "deepest surface"],
    ],
  },
  {
    name: "Lines",
    tokens: [
      ["--line", "default border"],
      ["--line-strong", "emphasized border"],
    ],
  },
  {
    name: "Ink (text)",
    tokens: [
      ["--ink", "primary text"],
      ["--ink-2", "body text"],
      ["--ink-3", "secondary / meta"],
      ["--ink-4", "disabled / hint"],
    ],
  },
  {
    name: "Primary — action",
    tokens: [
      ["--primary", "default buttons, links"],
      ["--primary-soft", "backgrounds, tints"],
      ["--primary-soft-ink", "text on soft bg"],
    ],
  },
  {
    name: "Semantic — positive",
    tokens: [
      ["--pos", "positive value, up move"],
      ["--pos-soft", "positive background"],
      ["--pos-soft-ink", "text on positive bg"],
    ],
  },
  {
    name: "Semantic — caution",
    tokens: [
      ["--caution", "warning, approaching limit"],
      ["--caution-soft", "caution background"],
      ["--caution-soft-ink", "text on caution bg"],
    ],
  },
  {
    name: "Semantic — breach",
    tokens: [
      ["--breach", "hard breach, error, loss"],
      ["--breach-soft", "breach background"],
      ["--breach-soft-ink", "text on breach bg"],
    ],
  },
  {
    name: "Accents (charts)",
    tokens: [
      ["--accent", "cyan — secondary series"],
      ["--accent-2", "indigo — tertiary series"],
    ],
  },
];

const RADII = [
  ["--r-sm", "6px", "small inputs, chips"],
  ["--r-md", "8px", "buttons, inputs, rows"],
  ["--r-lg", "12px", "cards, panels"],
  ["--r-xl", "16px", "large containers"],
];

const SHADOWS = [
  ["--shadow-sm", "resting card"],
  ["--shadow-md", "elevated card"],
  ["--shadow-lg", "modal, drawer"],
];

const SPACING = [
  ["4", "4px", "icon gap"],
  ["6", "6px", "inline cluster"],
  ["8", "8px", "chip gap"],
  ["12", "12px", "compact pad"],
  ["16", "16px", "default pad"],
  ["20", "20px", "comfortable pad"],
  ["24", "24px", "section gap"],
  ["32", "32px", "workspace gutter"],
  ["44", "44px", "page gutter"],
];

const TYPE_SCALE = [
  { token: "display/40", face: "Fraunces 500", size: 40, track: -0.02, use: "Page hero h1" },
  { token: "display/28", face: "Fraunces 500", size: 28, track: -0.015, use: "Section h2, modal title" },
  { token: "display/22", face: "Fraunces 500", size: 22, track: -0.015, use: "KPI value, rec ticker" },
  { token: "display/18", face: "Fraunces 500", size: 18, track: -0.01, use: "Card title, dialog header" },
  { token: "body/15", face: "Inter Tight 400", size: 15, track: 0, use: "Body lead, page sub" },
  { token: "body/13.5", face: "Inter Tight 400", size: 13.5, track: 0, use: "Default body" },
  { token: "body/13 medium", face: "Inter Tight 500", size: 13, track: 0, use: "Card head, action label" },
  { token: "meta/12", face: "Inter Tight 400", size: 12, track: 0, use: "Secondary text, caption" },
  { token: "label/10.5", face: "Inter Tight 600", size: 10.5, track: 0.08, caps: true, use: "All‑caps label" },
  { token: "mono/11.5", face: "JetBrains Mono 400", size: 11.5, track: 0, mono: true, use: "Tabular numbers, IDs" },
  { token: "mono/10.5", face: "JetBrains Mono 400", size: 10.5, track: 0, mono: true, use: "Inline meta, timestamps" },
];

const ALL_ICONS = [
  "overview","decision","compare","risk","replay","backtest","paper","universe","news","ops",
  "search","bell","bookmark","command","chevron-right","chevron-down","arrow-up-right","arrow-down-right",
  "trend-up","plus","minus","check","alert-triangle","info","history","panel-left","panel-right",
  "external","share","pin","dots","filter","eye","database","tag","sparkle","close"
];

const MOTION = [
  { name: "fast", dur: "120ms", easing: "cubic-bezier(0.4, 0, 0.2, 1)", use: "hover, focus, small feedback" },
  { name: "default", dur: "180ms", easing: "cubic-bezier(0.4, 0, 0.2, 1)", use: "button press, input state" },
  { name: "surface", dur: "220ms", easing: "cubic-bezier(0.2, 0.8, 0.2, 1)", use: "panel reveal, drawer slide" },
  { name: "deliberate", dur: "320ms", easing: "cubic-bezier(0.2, 0.8, 0.2, 1)", use: "confirm, publish success" },
];

// ─────── Sidebar nav items ───────
const NAV = [
  { grp: "Foundations", items: [
    ["colors","Colors"],
    ["spacing","Spacing"],
    ["radii","Radii & shadows"],
    ["motion","Motion"],
  ]},
  { grp: "Type & icons", items: [
    ["type","Typography"],
    ["icons","Icons"],
  ]},
  { grp: "Components", items: [
    ["tier1","Tier 1 — core"],
    ["tier2","Tier 2 — contextual"],
    ["tier3","Tier 3 — advanced"],
  ]},
  { grp: "Patterns", items: [
    ["patterns","Usage patterns"],
    ["states","All states"],
  ]},
];

// ─────── Sidebar ───────
function DSSidebar({ active }) {
  return (
    <aside className="ds-sidebar">
      <div className="ds-sb-brand">
        <span className="mark">Q</span> QuantPipeline · DS
      </div>
      {NAV.map(g => (
        <React.Fragment key={g.grp}>
          <div className="ds-sb-section">{g.grp}</div>
          {g.items.map(([id, label]) => (
            <a key={id} href={"#"+id}
               className={"ds-sb-link " + (active===id?"active":"")}>
              {label}
            </a>
          ))}
        </React.Fragment>
      ))}
      <div className="ds-sb-foot">
        v0.1 · Prototype reference.<br/>Not a published package.
      </div>
    </aside>
  );
}

// ─────── Theme toggle ───────
function DSThemeToggle({ theme, onChange }) {
  return (
    <div className="ds-theme-toggle">
      {["light","dark"].map(t => (
        <button key={t}
          className={theme===t?"active":""}
          onClick={()=>onChange(t)}>{t}</button>
      ))}
    </div>
  );
}

// ─────── Color section ───────
function ColorSwatch({ tokenName, desc }) {
  return (
    <div className="ds-swatch">
      <div className="chip" style={{ background: `var(${tokenName})` }}/>
      <div>
        <div className="name">{tokenName}</div>
        <div className="val">{desc}</div>
      </div>
    </div>
  );
}

function ColorsSection() {
  return (
    <section id="colors" className="ds-section">
      <h2>Colors</h2>
      <p className="lead">
        Cool neutral canvas. Disciplined blue as the only "loud" action color. Semantic colors
        (pos / caution / breach) used sparingly and paired with soft tints for annotations.
      </p>

      {COLOR_GROUPS.map(g => (
        <div key={g.name} className="ds-subsection">
          <h3>{g.name}</h3>
          <div className="ds-token-grid">
            {g.tokens.map(([t, desc]) => (
              <ColorSwatch key={t} tokenName={t} desc={desc}/>
            ))}
          </div>
        </div>
      ))}

      <div className="ds-callout" style={{marginTop:28}}>
        <b>Using semantic colors:</b> never use <code>--breach</code> for "hot" or
        "trending" — only for hard limits and errors. Positive movement uses <code>--pos</code>,
        but markets default to neutral — prefer ink colors when direction isn't the point.
      </div>
    </section>
  );
}

// ─────── Spacing ───────
function SpacingSection() {
  return (
    <section id="spacing" className="ds-section">
      <h2>Spacing</h2>
      <p className="lead">
        Base unit is <b>4px</b>. Density tokens (<code>--dens-pad</code>, <code>--dens-gap</code>,
        <code> --dens-row</code>, <code>--dens-text</code>) shift the whole system compact ↔ comfortable.
      </p>

      <div className="ds-demo-row">
        {SPACING.map(([n, px, use]) => (
          <div key={n} className="ds-demo-item">
            <div className="box" style={{ width: px, height: px }}/>
            <div className="meta"><b>{n}</b> · {px}</div>
            <div className="meta">{use}</div>
          </div>
        ))}
      </div>

      <div className="ds-subsection">
        <h3>Density presets</h3>
        <div className="sub">Applied by toggling <code>data-density</code> on <code>:root</code>.</div>
        <table className="ov-table" style={{marginTop:8}}>
          <thead><tr><th>Token</th><th>compact</th><th>default</th><th>comfortable</th></tr></thead>
          <tbody>
            <tr><td>--dens-pad</td><td className="num">12px</td><td className="num">16px</td><td className="num">20px</td></tr>
            <tr><td>--dens-row</td><td className="num">30px</td><td className="num">36px</td><td className="num">42px</td></tr>
            <tr><td>--dens-gap</td><td className="num">12px</td><td className="num">16px</td><td className="num">20px</td></tr>
            <tr><td>--dens-text</td><td className="num">12.5px</td><td className="num">13.5px</td><td className="num">14px</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ─────── Radii & shadows ───────
function RadiiShadowsSection() {
  return (
    <section id="radii" className="ds-section">
      <h2>Radii &amp; shadows</h2>
      <p className="lead">
        Radii scale with container size. Shadows are disciplined — three levels, all cool and low‑saturation
        so they feel like depth, not decoration.
      </p>

      <div className="ds-subsection">
        <h3>Radii</h3>
        <div className="ds-demo-row">
          {RADII.map(([t, px, use]) => (
            <div key={t} className="ds-demo-item">
              <div className="box" style={{ width: 84, height: 56, borderRadius: `var(${t})` }}/>
              <div className="meta"><b>{t}</b></div>
              <div className="meta">{px} · {use}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="ds-subsection">
        <h3>Shadows</h3>
        <div className="ds-demo-row">
          {SHADOWS.map(([t, use]) => (
            <div key={t} className="ds-demo-item">
              <div className="box" style={{
                width: 140, height: 80,
                borderRadius: "var(--r-md)",
                boxShadow: `var(${t})`,
                border: "1px solid var(--line)"
              }}/>
              <div className="meta"><b>{t}</b></div>
              <div className="meta">{use}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────── Motion ───────
function MotionSection() {
  return (
    <section id="motion" className="ds-section">
      <h2>Motion</h2>
      <p className="lead">
        Motion signals causality, never decoration. Four durations covering the range 120–320ms.
        Everything respects <code>prefers-reduced-motion</code>.
      </p>

      <div className="ds-subsection">
        {MOTION.map(m => (
          <div key={m.name} className="ds-motion-row">
            <div className="ds-motion-label">
              <b>{m.name}</b>
              {m.dur} · {m.easing}
              <div style={{marginTop:4, fontStyle:"italic"}}>{m.use}</div>
            </div>
            <div className="ds-motion-stage">
              <div className="dot" style={{ transition: `transform ${m.dur} ${m.easing}` }}/>
              <div className="hint">hover →</div>
            </div>
          </div>
        ))}
      </div>

      <div className="ds-callout caution" style={{marginTop:20}}>
        <b>Reduced motion:</b> every animation is wrapped in
        <code> @media (prefers-reduced-motion: reduce)</code> and disabled.
        Pulse indicators, drawer slides, and skeleton shimmer all fall back to static states.
      </div>
    </section>
  );
}

// ─────── Typography ───────
function TypeSection() {
  return (
    <section id="type" className="ds-section">
      <h2>Typography</h2>
      <p className="lead">
        Three families. Fraunces for display and key numeric values — gives analytical copy a
        serious, editorial feel. Inter Tight for all body and UI. JetBrains Mono for tabular numbers,
        IDs, timestamps, and any value that needs to align in a column.
      </p>

      <div className="ds-subsection">
        <h3>Scale</h3>
        <div>
          {TYPE_SCALE.map(t => {
            const style = {
              fontSize: t.size + "px",
              letterSpacing: t.track + "em",
              fontFamily: t.mono ? "var(--font-mono)" :
                          t.face.startsWith("Fraunces") ? "var(--font-display)" : "var(--font-sans)",
              fontWeight: t.face.includes("500") ? 500 : t.face.includes("600") ? 600 : 400,
              textTransform: t.caps ? "uppercase" : "none",
            };
            return (
              <div key={t.token} className="ds-type-row">
                <div className="ds-type-meta">
                  <b>{t.token}</b>
                  {t.face}<br/>
                  {t.size}px {t.track!==0 && `· track ${t.track}em`}
                  <div style={{marginTop:4, fontStyle:"italic"}}>{t.use}</div>
                </div>
                <div className="ds-type-sample" style={style}>
                  {t.token.startsWith("mono") ? "0.748 · REC-2026-0419-NVDA-L" : "Recommendation · 12% upside"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="ds-subsection">
        <h3>Paragraph specimen</h3>
        <div className="sub">Body text at default size, for comparison.</div>
        <div className="ds-type-sample long" style={{ maxWidth:640, fontSize:13.5 }}>
          The recommendation is a <b>LONG</b> stance on NVDA at +4.2% portfolio weight over a 3‑month horizon.
          Five engines scored this name on Friday's close; four align above 0.68 confidence, one dissents.
          Data freshness is 94% and operational readiness is full. Promoting this recommendation to paper
          would push the semiconductor sector exposure from 27.5% to 28.1%, within the 30% policy cap.
        </div>
      </div>
    </section>
  );
}

// ─────── Icons ───────
function IconsSection() {
  return (
    <section id="icons" className="ds-section">
      <h2>Icons</h2>
      <p className="lead">
        One stroke weight (1.5px at 16/20px), square corners, no fills. Icons live in
        <code> icons.jsx</code> as inline SVG — each paired with a name string.
      </p>

      <div className="ds-subsection">
        <h3>Set</h3>
        <div className="sub">{ALL_ICONS.length} icons · rendered at 20px here, used at 12–16px in product.</div>
        <div className="ds-icon-grid">
          {ALL_ICONS.map(n => (
            <div key={n} className="ds-icon-cell">
              <div className="ic"><Icon name={n} size={20}/></div>
              <div className="nm">{n}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="ds-subsection">
        <h3>Sizes</h3>
        <div className="ds-demo-row" style={{alignItems:"center"}}>
          {[10,12,14,16,20,24,32].map(s => (
            <div key={s} className="ds-demo-item">
              <Icon name="decision" size={s}/>
              <div className="meta">{s}px</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, {
  DSSidebar, DSThemeToggle,
  ColorsSection, SpacingSection, RadiiShadowsSection,
  MotionSection, TypeSection, IconsSection,
  ALL_ICONS, NAV
});
