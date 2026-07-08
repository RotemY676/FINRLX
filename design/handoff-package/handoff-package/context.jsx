// Context pane
const { useState: useStateCtx } = React;

const ContextPane = () => {
  const [tab, setTab] = useStateCtx("risk");
  return (
    <aside className="contextpane">
      <div className="ctx-tabs">
        <div className={"ctx-tab" + (tab === "risk" ? " active" : "")} onClick={() => setTab("risk")}>
          Risk <span className="flag-dot" />
        </div>
        <div className={"ctx-tab" + (tab === "prov" ? " active" : "")} onClick={() => setTab("prov")}>Provenance</div>
        <div className={"ctx-tab" + (tab === "compare" ? " active" : "")} onClick={() => setTab("compare")}>Compare</div>
        <div className={"ctx-tab" + (tab === "notes" ? " active" : "")} onClick={() => setTab("notes")}>Notes</div>
      </div>

      {tab === "risk" && (
        <>
          <div className="ctx-group">
            <h4>Portfolio impact <span className="more">Open risk workspace ›</span></h4>
            <div className="ctx-kv">
              <span className="k">Book weight</span><span className="v">4.2%</span>
              <span className="k">Post-trim weight</span><span className="v hl-cau">3.6%</span>
              <span className="k">Sector (semis)</span><span className="v hl-cau">28.1% / 30% limit</span>
              <span className="k">Single-name DDn</span><span className="v">-8.4%</span>
              <span className="k">Portfolio β</span><span className="v">1.18</span>
              <span className="k">Realized vol 30d</span><span className="v">34.2%</span>
            </div>
          </div>
          <div className="ctx-group">
            <h4>Policy flags</h4>
            <div className="prov-item">
              <span className="prov-dot caution" />
              <div className="prov-body">
                <div className="t">Sector concentration approaching 30% limit</div>
                <div className="s">constraint.semis.weight · review at +150bps</div>
              </div>
            </div>
            <div className="prov-item">
              <span className="prov-dot" />
              <div className="prov-body">
                <div className="t">Liquidity coverage passes</div>
                <div className="s">ADV 48.2M shares · 14× position</div>
              </div>
            </div>
            <div className="prov-item">
              <span className="prov-dot" />
              <div className="prov-body">
                <div className="t">Leverage within limits</div>
                <div className="s">gross 112% · net 88%</div>
              </div>
            </div>
          </div>
        </>
      )}

      {tab === "prov" && (
        <>
          <div className="ctx-group">
            <h4>Snapshot</h4>
            <div className="ctx-kv">
              <span className="k">Snapshot ID</span><span className="v">snap_240419_0920</span>
              <span className="k">Model version</span><span className="v">v4.8.2-stable</span>
              <span className="k">Build hash</span><span className="v">a7c3f1…e204</span>
              <span className="k">Generated at</span><span className="v">09:20:14 ET</span>
              <span className="k">Pipeline</span><span className="v">decision/primary</span>
            </div>
          </div>
          <div className="ctx-group">
            <h4>Data sources</h4>
            <div className="prov-item">
              <span className="prov-dot" /><div className="prov-body">
                <div className="t">Market data · primary</div>
                <div className="s">refmm-us · freshness 0:12 · ok</div>
              </div></div>
            <div className="prov-item">
              <span className="prov-dot caution" /><div className="prov-body">
                <div className="t">Options chain</div>
                <div className="s">cboe-l2 · freshness 14:03 · stale</div>
              </div></div>
            <div className="prov-item">
              <span className="prov-dot" /><div className="prov-body">
                <div className="t">Fundamentals</div>
                <div className="s">factset-normalized · fresh</div>
              </div></div>
            <div className="prov-item">
              <span className="prov-dot neutral" /><div className="prov-body">
                <div className="t">News feed</div>
                <div className="s">composite · 238 items last 24h</div>
              </div></div>
          </div>
          <div className="ctx-group">
            <h4>Audit trail</h4>
            <div className="prov-item"><span className="prov-dot" />
              <div className="prov-body"><div className="t">v4 published</div>
              <div className="s">12m ago · automatic · gates passed</div></div></div>
            <div className="prov-item"><span className="prov-dot neutral" />
              <div className="prov-body"><div className="t">v3 held for review</div>
              <div className="s">38m ago · R.M. · options data stale</div></div></div>
            <div className="prov-item"><span className="prov-dot neutral" />
              <div className="prov-body"><div className="t">v2 published</div>
              <div className="s">3h ago · automatic</div></div></div>
          </div>
        </>
      )}

      {tab === "compare" && (
        <div className="ctx-group">
          <h4>Alternative theses</h4>
          <div className="mini-table">
            <div className="row"><span className="k">Synthesis (current)</span><span className="v hl-pos">Long 4.2%</span><span className="v">0.74</span></div>
            <div className="row"><span className="k">Momentum only</span><span className="v hl-pos">Long 5.1%</span><span className="v">0.82</span></div>
            <div className="row"><span className="k">Fundamentals only</span><span className="v hl-pos">Long 3.4%</span><span className="v">0.71</span></div>
            <div className="row"><span className="k">Narrative LLM</span><span className="v">Hold 0.0%</span><span className="v">0.58</span></div>
            <div className="row"><span className="k">Risk-parity</span><span className="v">Hold 1.2%</span><span className="v">0.54</span></div>
            <div className="row"><span className="k">Flow / options</span><span className="v hl-neg">Short 0.8%</span><span className="v">0.49</span></div>
          </div>
          <button className="btn ghost sm" style={{marginTop:10}}>Open comparison matrix <Icon name="chevron-right" size={12} /></button>
        </div>
      )}

      {tab === "notes" && (
        <div className="ctx-group">
          <h4>Analyst notes</h4>
          <div className="note-box">
            <textarea placeholder="Add a note. This attaches to REC-2026-0419-NVDA-L and appears in replay." defaultValue="Trim by 120 bps is consistent with sector cap. Re-review once options IV fresh." />
            <div className="nf">
              <span className="hint">Markdown supported · visible to ops</span>
              <button className="btn primary sm">Save</button>
            </div>
          </div>
          <div className="prov-item" style={{marginTop:12}}>
            <span className="prov-dot neutral" /><div className="prov-body">
              <div className="t">Hold vs cap exposure</div>
              <div className="s">R.M. · 2h ago</div>
            </div></div>
          <div className="prov-item"><span className="prov-dot neutral" />
            <div className="prov-body"><div className="t">Watch for Taiwan logistics</div>
            <div className="s">S.K. · yesterday</div></div></div>
        </div>
      )}
    </aside>
  );
};

Object.assign(window, { ContextPane });
