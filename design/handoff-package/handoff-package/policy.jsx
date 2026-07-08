// Policy editor — UI components
const { useState: useStatePol } = React;

// ---- Rule chip summary -------------------------------------------
const RuleChip = ({ rule }) => {
  const r = rule[0];
  // Shorten field name for the chip
  const shortField = r.field.replace(/^(position|ticker|portfolio|time|regime|instrument)\./, "");
  return (
    <div className="pol-rule-chip" title={r.field + " " + r.op + " " + r.val}>
      <span className="seg">{shortField}</span>
      <span className="seg op">{r.op}</span>
      <span className="seg val">{r.val}</span>
      {rule.length > 1 && <span className="seg op">+{rule.length - 1}</span>}
    </div>
  );
};

// ---- Category icon mapping ---------------------------------------
const catIcon = (key) => ({
  position: "risk",
  exposure: "decision",
  sector:   "universe",
  approval: "ops",
  stoploss: "alert-triangle",
  regime:   "compare",
}[key] || "check");

// ---- Left tree ---------------------------------------------------
const PolicyTree = ({ active, onPick }) => (
  <aside className="pol-tree">
    <div className="pol-tree-head">
      <h2>Policies</h2>
      <span className="count">{POLICIES.length} rules</span>
    </div>
    <div className="pol-tree-search">
      <input type="text" placeholder="Search rules…" />
    </div>

    <div className="pol-category">
      <div className="pol-cat-label">All</div>
      <div className={"pol-cat-item" + (active === "all" ? " active" : "")} onClick={() => onPick("all")}>
        <span className="ic"><Icon name="command" size={14} /></span>
        <span>All rules</span>
        <span className="count">{POLICIES.length}</span>
      </div>
      <div className={"pol-cat-item" + (active === "active" ? " active" : "")} onClick={() => onPick("active")}>
        <span className="ic"><Icon name="check" size={14} /></span>
        <span>Active only</span>
        <span className="count">{POLICIES.filter(p => p.on).length}</span>
      </div>
      <div className={"pol-cat-item" + (active === "draft" ? " active" : "")} onClick={() => onPick("draft")}>
        <span className="ic"><Icon name="pin" size={14} /></span>
        <span>Drafts</span>
        <span className="count">{POLICIES.filter(p => p.draft).length}</span>
      </div>
    </div>

    <div className="pol-category">
      <div className="pol-cat-label">Categories</div>
      {POLICY_CATEGORIES.map(c => (
        <div
          key={c.key}
          className={"pol-cat-item" + (active === c.key ? " active" : "")}
          onClick={() => onPick(c.key)}
        >
          <span className="ic"><Icon name={catIcon(c.key)} size={14} /></span>
          <span>{c.label}</span>
          <span className="count">{c.count}</span>
        </div>
      ))}
    </div>
  </aside>
);

// ---- Policy card -------------------------------------------------
const PolicyCard = ({ pol, expanded, onToggleExpand, on, onToggleOn }) => {
  const blocked = pol.impact.blocked;
  const warned  = pol.impact.warned;
  return (
    <div className={"pol-card" + (expanded ? " expanded" : "") + (pol.draft ? " draft" : "")}>
      <div className="pol-card-top" onClick={onToggleExpand}>
        <div
          className={"pol-toggle" + (on ? " on" : "")}
          onClick={(e) => { e.stopPropagation(); onToggleOn(); }}
        />
        <div className="pol-card-title">
          <div className="pol-card-name">
            {pol.name}
            {pol.draft && <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--caution-soft-ink)", background: "var(--caution-soft)", padding: "1px 6px", borderRadius: 3, fontWeight: 500 }}>DRAFT</span>}
          </div>
          <div className="pol-card-desc">{pol.desc}</div>
        </div>
        <RuleChip rule={pol.rule} />
        <div className="pol-card-impact">
          {blocked > 0
            ? <><b className="breach">{blocked}</b> blocked<br/><span style={{ opacity: 0.7 }}>{warned} warned</span></>
            : warned > 0
            ? <><b className="caution">{warned}</b> warned</>
            : <><b style={{ color: "var(--ink-3)" }}>0</b> no current hits</>}
        </div>
        <span className="pol-card-chev"><Icon name="chevron-right" size={14} /></span>
      </div>

      {expanded && (
        <>
          <div className="pol-card-body">
            <div className="pol-rule-builder">
              <div className="pol-form-row">
                <label>When</label>
                <div className="pol-conds">
                  {pol.rule.map((r, i) => (
                    <div className="pol-cond" key={i}>
                      <span className={"pol-cond-op " + (i === 0 ? "if" : "and")}>
                        {i === 0 ? "IF" : "AND"}
                      </span>
                      <span className="pol-cond-text">
                        <span className="lit">{r.field}</span>
                        {" "}
                        <span>{r.op}</span>
                        {" "}
                        <span className="num">{r.val}</span>
                      </span>
                      <div className="pol-cond-actions">
                        <button className="pol-cond-del" title="Remove">
                          <Icon name="close" size={11} />
                        </button>
                      </div>
                    </div>
                  ))}
                  <button className="pol-add-cond">
                    <Icon name="plus" size={12} />
                    Add condition
                  </button>
                </div>
              </div>

              <div className="pol-form-row">
                <label>Then</label>
                <div className={"pol-action-block " + pol.action.kind}>
                  <div className="pol-action-head">
                    {pol.action.kind === "block" && <><Icon name="close" size={11} /> BLOCK</>}
                    {pol.action.kind === "warn"  && <><Icon name="alert-triangle" size={11} /> WARN</>}
                    {pol.action.kind === "allow" && <><Icon name="check" size={11} /> ALLOW WITH CONDITION</>}
                  </div>
                  <div className="pol-action-text">{pol.action.text}</div>
                </div>
              </div>

              <div className="pol-form-row">
                <label>Applies to</label>
                <select className="pol-select" defaultValue="all">
                  <option value="all">All recommendations</option>
                  <option value="new">New publications only</option>
                  <option value="held">Open positions only</option>
                </select>
              </div>
            </div>

            <div className="pol-divider" />

            <div className="pol-impact">
              <div className="pol-impact-title">LIVE IMPACT · RIGHT NOW</div>
              <div className="pol-impact-stat">
                <div className={"n " + (blocked > 0 ? "breach" : warned > 0 ? "caution" : "")}>
                  {blocked + warned}
                </div>
                <div className="l">
                  recommendations caught<br/>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-4)" }}>
                    {blocked} blocked · {warned} warned
                  </span>
                </div>
              </div>
              {pol.impact.hits.length > 0 && (
                <div>
                  {pol.impact.hits.map((h, i) => (
                    <div className="pol-impact-item" key={i}>
                      <span className="tk">{h.tk}</span>
                      <span className="reason">{h.desc}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="pol-card-footer">
            <div className="pol-card-footer-meta">
              <span className="auth">{pol.author}</span> · updated {pol.updated}
            </div>
            <div className="pol-card-footer-actions">
              <button className="btn ghost">View history</button>
              <button className="btn ghost">Duplicate</button>
              <button className="btn primary">Save changes</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ---- Right side: global impact ------------------------------------
const PolicySidePanel = ({ policies }) => {
  const totalBlocked = policies.filter(p => p.on).reduce((a, p) => a + p.impact.blocked, 0);
  const totalWarned  = policies.filter(p => p.on).reduce((a, p) => a + p.impact.warned, 0);
  const hits = [];
  policies.filter(p => p.on).forEach(p => {
    p.impact.hits.forEach(h => hits.push({ ...h, polName: p.name }));
  });
  const blockHits = hits.filter(h => h.kind === "block");
  const warnHits = hits.filter(h => h.kind === "warn");

  return (
    <aside className="pol-side">
      <h3 className="pol-side-head">Live impact</h3>
      <p className="pol-side-sub">
        Simulated against all 24 recommendations currently queued or held. Re-evaluates on every rule change.
      </p>

      <div className="pol-side-section">
        <div className="pol-side-label">Totals</div>
        <div className="pol-outcome">
          <div className={"big " + (totalBlocked > 0 ? "breach" : "")}>{totalBlocked}</div>
          <div className="lbl"><b>blocked</b> — would not publish under current rules</div>
        </div>
        <div style={{ height: 8 }} />
        <div className="pol-outcome">
          <div className={"big " + (totalWarned > 0 ? "caution" : "")}>{totalWarned}</div>
          <div className="lbl"><b>warned</b> — would surface caution, require review</div>
        </div>
      </div>

      {blockHits.length > 0 && (
        <div className="pol-side-section">
          <div className="pol-side-label">Blocked right now</div>
          {blockHits.map((h, i) => (
            <div className="pol-rec-row" key={i}>
              <span className="pol-rec-dot block" />
              <div>
                <div className="pol-rec-tk">{h.tk}</div>
                <div className="pol-rec-desc">{h.desc}</div>
              </div>
              <span className="pol-rec-pol">{h.polName.split(" · ")[0].slice(0, 14)}</span>
            </div>
          ))}
        </div>
      )}

      {warnHits.length > 0 && (
        <div className="pol-side-section">
          <div className="pol-side-label">Warned right now</div>
          {warnHits.slice(0, 5).map((h, i) => (
            <div className="pol-rec-row" key={i}>
              <span className="pol-rec-dot warn" />
              <div>
                <div className="pol-rec-tk">{h.tk}</div>
                <div className="pol-rec-desc">{h.desc}</div>
              </div>
              <span className="pol-rec-pol">{h.polName.split(" · ")[0].slice(0, 14)}</span>
            </div>
          ))}
        </div>
      )}

      <div className="pol-side-section">
        <div className="pol-side-label">Last 30 days</div>
        <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.55 }}>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed var(--line)" }}>
            <span>Recommendations caught</span>
            <span style={{ fontFamily: "var(--font-mono)", color: "var(--ink)" }}>47</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed var(--line)" }}>
            <span>Overrides approved</span>
            <span style={{ fontFamily: "var(--font-mono)", color: "var(--ink)" }}>3</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
            <span>Most-active rule</span>
            <span style={{ fontFamily: "var(--font-mono)", color: "var(--ink)" }}>Sector cap · Tech</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

Object.assign(window, { RuleChip, PolicyTree, PolicyCard, PolicySidePanel });
