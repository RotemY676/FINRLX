// Integrations — components
const { useState: useStateIg, useMemo: useMemoIg } = React;

const IgHero = ({ stats }) => (
  <div className="ig-hero">
    <div className="ig-hero-head">
      <div>
        <h1 className="ig-hero-title">Data sources & integrations</h1>
        <p className="ig-hero-sub">
          Every signal in your recommendations traces back to a source here.
          When a feed degrades, we show it — and we show which decisions depend on it before you decide what to do.
        </p>
      </div>
      <div style={{display:"flex", gap:8}}>
        <button className="btn ghost sm"><Icon name="history" size={12}/> Change log</button>
        <button className="btn ghost sm"><Icon name="external" size={12}/> API keys</button>
        <button className="btn primary sm"><Icon name="plus" size={12}/> Add integration</button>
      </div>
    </div>
    <div className="ig-stats">
      <div className="ig-stat good">
        <div className="l">Connected</div>
        <div className="v">{stats.ok}<span className="unit">of {stats.total}</span></div>
        <div className="s">healthy and in active use</div>
      </div>
      <div className="ig-stat warn">
        <div className="l">Degraded</div>
        <div className="v">{stats.degraded}</div>
        <div className="s">SLA below target — affecting 11 recs</div>
      </div>
      <div className="ig-stat">
        <div className="l">Paused</div>
        <div className="v">{stats.paused}</div>
        <div className="s">manually disabled</div>
      </div>
      <div className="ig-stat">
        <div className="l">Monthly spend</div>
        <div className="v">$9.5<span className="unit">K</span></div>
        <div className="s">across 7 paid feeds</div>
      </div>
    </div>
  </div>
);

const IgTabs = ({ tab, setTab, counts }) => {
  const tabs = [
    { id: "connected", label: "Connected", ct: counts.connected },
    { id: "catalog",   label: "Catalog",   ct: counts.catalog },
    { id: "history",   label: "Change log" },
    { id: "keys",      label: "API keys" },
  ];
  return (
    <div className="ig-tabs">
      {tabs.map(t => (
        <div key={t.id} className={"ig-tab" + (tab === t.id ? " active" : "")}
             onClick={() => setTab(t.id)}>
          {t.label}
          {t.ct !== undefined && <span className="ct">{t.ct}</span>}
        </div>
      ))}
    </div>
  );
};

const IgFilterBar = ({ query, setQuery, cat, setCat }) => (
  <div className="ig-filter-bar">
    <div className="ig-search">
      <span className="ico"><Icon name="search" size={13}/></span>
      <input placeholder="Search integrations…" value={query} onChange={e => setQuery(e.target.value)} />
    </div>
    {IG_CATEGORIES.map(c => (
      <span key={c.id} className={"ig-cat-chip" + (cat === c.id ? " active" : "")}
            onClick={() => setCat(c.id)}>
        {c.label}
      </span>
    ))}
  </div>
);

const IgRow = ({ ig, onOpen }) => (
  <div className={"ig-row " + (ig.status === "degraded" ? "degraded" : ig.status === "bad" ? "bad" : "")}
       onClick={() => onOpen(ig)}>
    <div className={"ig-logo " + ig.logo}>{ig.mark}</div>
    <div className="ig-main">
      <div className="nm">
        {ig.name}
        <span className="cat">{ig.cat}</span>
      </div>
      <div className="desc">{ig.desc}</div>
      <div className="meta">
        <span>lag {ig.lag}</span>
        <span className="dot">·</span>
        <span>coverage {ig.coverage}</span>
        <span className="dot">·</span>
        <span>SLO {ig.slo}</span>
        <span className="dot">·</span>
        <span className="used-by">used by {ig.usedByCt} surfaces</span>
      </div>
    </div>
    <div className="ig-metric good">
      <div className="v">{ig.lastSync}</div>
      <div className="l">Last sync</div>
    </div>
    <span className={"ig-status-badge " + ig.status}>
      <span className="d" />
      {ig.status === "ok" ? "Healthy" : ig.status === "degraded" ? "Degraded" : ig.status === "bad" ? "Breached" : "Paused"}
    </span>
    <div className="ig-row-actions">
      <button className="btn ghost sm" onClick={e => { e.stopPropagation(); onOpen(ig); }}>Manage</button>
    </div>
  </div>
);

const IgCatalogCard = ({ ig, onOpen }) => (
  <div className="ig-cat-card" onClick={() => onOpen(ig)}>
    <div className="top">
      <div className={"ig-logo " + ig.logo} style={{width:36, height:36, fontSize:12}}>{ig.mark}</div>
      <div>
        <div className="nm">{ig.name}</div>
        <div className="tag">{ig.cat}</div>
      </div>
    </div>
    <div className="desc">{ig.desc}</div>
    <div className="foot">
      <span>{ig.tag}</span>
      <span style={{color:"var(--primary)", fontFamily:"var(--font-sans)", fontWeight:600, fontSize:12}}>Connect →</span>
    </div>
  </div>
);

const IgSpark = ({ data, kind }) => (
  <div className="ig-spark">
    {data.map((v, i) => (
      <div key={i} className={"bar " + (kind === "down" && v < 0.6 ? "down" : kind === "out" ? "out" : "")}
           style={{height: `${Math.max(8, v * 100)}%`}} />
    ))}
  </div>
);

const IgDrawer = ({ ig, onClose }) => {
  if (!ig) return null;
  return (
    <>
      <div className="ig-drawer-backdrop" onClick={onClose} />
      <div className="ig-drawer">
        <div className="ig-drawer-head">
          <div className={"ig-logo " + ig.logo}>{ig.mark}</div>
          <div>
            <h3>{ig.name}</h3>
            <div className="sub">{ig.cat} · {ig.entitlement}</div>
          </div>
          <button className="close" onClick={onClose}><Icon name="close" size={14} /></button>
        </div>
        <div className="ig-drawer-body">

          <div className="ig-section">
            <h4>SLO · last 24h</h4>
            <IgSpark data={ig.spark} kind={ig.sparkKind} />
            <div style={{display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:0,
                         border:"1px solid var(--line)", borderRadius:"var(--r-md)", overflow:"hidden"}}>
              <div style={{padding:"10px 14px", borderRight:"1px solid var(--line)"}}>
                <div style={{fontSize:11, color:"var(--ink-3)"}}>Latency</div>
                <div style={{fontFamily:"var(--font-serif)", fontSize:18, color: ig.status === "degraded" ? "var(--caution)" : "var(--ink)"}}>{ig.lag}</div>
              </div>
              <div style={{padding:"10px 14px", borderRight:"1px solid var(--line)"}}>
                <div style={{fontSize:11, color:"var(--ink-3)"}}>Coverage</div>
                <div style={{fontFamily:"var(--font-serif)", fontSize:18, color: ig.status === "degraded" ? "var(--caution)" : "var(--ink)"}}>{ig.coverage}</div>
              </div>
              <div style={{padding:"10px 14px", borderRight:"1px solid var(--line)"}}>
                <div style={{fontSize:11, color:"var(--ink-3)"}}>SLO (7d)</div>
                <div style={{fontFamily:"var(--font-serif)", fontSize:18, color: ig.status === "degraded" ? "var(--caution)" : "var(--ink)"}}>{ig.slo}</div>
              </div>
              <div style={{padding:"10px 14px"}}>
                <div style={{fontSize:11, color:"var(--ink-3)"}}>Cost</div>
                <div style={{fontFamily:"var(--font-serif)", fontSize:18, color:"var(--ink)"}}>{ig.cost}</div>
              </div>
            </div>
            {ig.issue && (
              <div className="ig-danger" style={{background:"var(--caution-soft)", color:"var(--caution-soft-ink)", borderColor:"var(--caution)"}}>
                <b>Issue:</b> {ig.issue} <span style={{opacity:0.8}}>→ <u>Open incident</u></span>
              </div>
            )}
            {ig.pausedReason && (
              <div className="ig-danger" style={{background:"var(--surface-3)", color:"var(--ink-2)", borderColor:"var(--line-strong)"}}>
                <b>Paused.</b> {ig.pausedReason}
              </div>
            )}
          </div>

          <div className="ig-section">
            <h4>Where this source is used</h4>
            <div className="ig-usage">
              {ig.usedBy.map((u, i) => (
                <div key={i} className="ig-usage-row">
                  <span className="where">{u}<span className="p">· if disconnected, these surfaces degrade</span></span>
                  <span className="wt">weight {i === 0 ? "0.34" : i === 1 ? "0.22" : "0.14"}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="ig-section">
            <h4>Connection</h4>
            <dl className="ig-kv">
              <dt>Endpoint</dt><dd>{ig.creds.endpoint}</dd>
              <dt>Auth mode</dt><dd>{ig.creds.authMode}</dd>
              <dt>Account ID</dt><dd>{ig.creds.accountId}</dd>
              <dt>Connected</dt><dd>{ig.connected} · by {ig.connectedBy}</dd>
              <dt>Rotation</dt><dd>Keys auto-rotate every 90d · next: May 12, 2026</dd>
            </dl>
          </div>

          <div className="ig-section">
            <h4>Schema sample · {ig.schema.length} fields mapped</h4>
            <div className="ig-schema">
              <table>
                <thead>
                  <tr><th>Field</th><th>Type</th><th>Sample</th></tr>
                </thead>
                <tbody>
                  {ig.schema.map(f => (
                    <tr key={f.f}>
                      <td className="field">{f.f}</td>
                      <td className="type">{f.t}</td>
                      <td style={{color:"var(--ink-2)"}}>{f.sample}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="ig-section">
            <h4>Danger zone</h4>
            <div className="ig-danger">
              Disconnecting <b>{ig.name}</b> will immediately degrade <b>{ig.usedByCt} surfaces</b>.
              Recommendations that weight this source above 0.15 will be capped in confidence until you restore or substitute.
              This is a reversible operation — 30-day grace before data is purged.
            </div>
          </div>
        </div>
        <div className="ig-actions-row">
          <button className="btn ghost sm">Test connection</button>
          <button className="btn ghost sm">Rotate credentials</button>
          <div style={{flex:1}} />
          {ig.status === "paused"
            ? <button className="btn primary sm">Resume</button>
            : <button className="btn ghost sm" style={{color:"var(--breach)"}}>Pause feed</button>
          }
          <button className="btn ghost sm" style={{color:"var(--breach)"}}>Disconnect</button>
        </div>
      </div>
    </>
  );
};

const IgCatalogDrawer = ({ ig, onClose }) => {
  if (!ig) return null;
  return (
    <>
      <div className="ig-drawer-backdrop" onClick={onClose} />
      <div className="ig-drawer">
        <div className="ig-drawer-head">
          <div className={"ig-logo " + ig.logo}>{ig.mark}</div>
          <div>
            <h3>{ig.name}</h3>
            <div className="sub">{ig.cat} · Not connected</div>
          </div>
          <button className="close" onClick={onClose}><Icon name="close" size={14} /></button>
        </div>
        <div className="ig-drawer-body">
          <div className="ig-section">
            <h4>About</h4>
            <p style={{fontSize:13, color:"var(--ink-2)", lineHeight:1.55, margin:0}}>{ig.desc}</p>
            {ig.note && <p style={{fontSize:13, color:"var(--ink-3)", fontStyle:"italic", margin:"8px 0 0"}}>{ig.note}</p>}
          </div>
          <div className="ig-section">
            <h4>What connecting this unlocks</h4>
            <div className="ig-usage">
              <div className="ig-usage-row">
                <span className="where">New signals for recommendations<span className="p">· ~{ig.cat === "Alt data" ? 8 : 4} new feature rows</span></span>
                <span className="wt">estimated +3% conf.</span>
              </div>
              <div className="ig-usage-row">
                <span className="where">Cross-source arbitration<span className="p">· reduces single-source risk</span></span>
                <span className="wt">quality: ↑</span>
              </div>
            </div>
          </div>
          <div className="ig-section">
            <h4>Pricing & entitlement</h4>
            <dl className="ig-kv">
              <dt>Plan</dt><dd>{ig.tag}</dd>
              <dt>Trial</dt><dd>14 days · no credit card</dd>
              <dt>Data residency</dt><dd>Inherits workspace · eu-central-1</dd>
            </dl>
          </div>
        </div>
        <div className="ig-actions-row">
          <button className="btn ghost sm">Read docs ↗</button>
          <div style={{flex:1}} />
          <button className="btn ghost sm">Start 14-day trial</button>
          <button className="btn primary sm">Connect {ig.name}</button>
        </div>
      </div>
    </>
  );
};

/* Change log tab */
const IgChangeLog = () => {
  const items = [
    { t: "14m ago", who: "System", what: "CBOE Options Flow degraded", sev: "caution", d: "Latency >10s threshold crossed — auto down-weight applied to flow engine" },
    { t: "3d ago",  who: "Hadar Levi",   what: "Paused RavenPack News Analytics", sev: "neu",     d: "Contract renewal pending · 2 recommendations fell back to Reuters-only signal" },
    { t: "6d ago",  who: "Rivka Shoval", what: "Rotated Bloomberg credentials", sev: "ok",       d: "Scheduled 90-day rotation · no downtime" },
    { t: "2w ago",  who: "Noam Katz",    what: "Connected Snowflake", sev: "ok",                  d: "New warehouse for historical feature store · backtests now 4× faster" },
    { t: "5w ago",  who: "Hadar Levi",   what: "Added CBOE Options Flow", sev: "ok",              d: "New flow engine went live · 2 new recommendations in first week" },
    { t: "2mo ago", who: "Rivka Shoval", what: "Workspace provisioned",       sev: "ok",          d: "Default integrations connected: Bloomberg, Reuters, FactSet, Okta, Teams" },
  ];
  return (
    <div>
      <div className="ig-section-head">
        <div>
          <h2>Integration change log</h2>
          <div className="sub">Every connect, disconnect, rotation, and degradation — auditable forever.</div>
        </div>
        <button className="btn ghost sm"><Icon name="external" size={12}/> Export CSV</button>
      </div>
      <div className="ig-list">
        {items.map((it, i) => (
          <div key={i} className="ig-row" style={{gridTemplateColumns:"110px 1fr auto", cursor:"default"}}>
            <div className="ig-main" style={{gap:2}}>
              <div style={{fontFamily:"var(--font-mono)", fontSize:11, color:"var(--ink-3)"}}>{it.t}</div>
              <div style={{fontSize:11, color:"var(--ink-4)"}}>by {it.who}</div>
            </div>
            <div className="ig-main">
              <div className="nm">{it.what}</div>
              <div className="desc">{it.d}</div>
            </div>
            <span className={"ig-status-badge " + (it.sev === "caution" ? "degraded" : it.sev === "ok" ? "ok" : "paused")}>
              <span className="d"/>{it.sev === "caution" ? "Alert" : it.sev === "ok" ? "OK" : "Info"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

/* API keys tab */
const IgApiKeys = () => (
  <div>
    <div className="ig-section-head">
      <div>
        <h2>API keys & webhooks</h2>
        <div className="sub">For programmatic access — CI pipelines, notebooks, external dashboards.</div>
      </div>
      <button className="btn primary sm"><Icon name="plus" size={12}/> Generate key</button>
    </div>
    <div className="ig-list">
      {[
        { name: "CI · backtest runner",   scope: "read:backtests write:backtests", created: "12d ago", last: "34m ago", hash: "qp_live_a8•••••••••••bF2e" },
        { name: "Jupyter · R. Shoval",    scope: "read:recs read:universe",         created: "5w ago",  last: "yesterday", hash: "qp_live_b2•••••••••••8Y3x" },
        { name: "Compliance dashboard",   scope: "read:audit read:decisions",       created: "3mo ago", last: "1m ago", hash: "qp_live_c9•••••••••••1K4m" },
      ].map((k, i) => (
        <div key={i} className="ig-row" style={{gridTemplateColumns:"1fr auto auto auto", cursor:"default"}}>
          <div className="ig-main">
            <div className="nm">{k.name}</div>
            <div className="desc" style={{fontFamily:"var(--font-mono)", fontSize:11}}>{k.hash}</div>
            <div className="meta"><span>scopes: {k.scope}</span></div>
          </div>
          <div className="ig-metric">
            <div className="v">{k.last}</div>
            <div className="l">Last used</div>
          </div>
          <span className="ig-status-badge ok"><span className="d"/>Active</span>
          <div className="ig-row-actions">
            <button className="btn ghost sm">Rotate</button>
            <button className="btn ghost sm" style={{color:"var(--breach)"}}>Revoke</button>
          </div>
        </div>
      ))}
    </div>
  </div>
);

Object.assign(window, { IgHero, IgTabs, IgFilterBar, IgRow, IgCatalogCard, IgDrawer, IgCatalogDrawer, IgChangeLog, IgApiKeys });
