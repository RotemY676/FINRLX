// Scenario controls + delta preview
const { useState: useStateSc } = React;

const ScenarioCard = () => {
  const [vals, setVals] = useStateSc({
    hold: 42,   // horizon days
    infl: 50,   // inflation shock
    corr: 55,   // correlation
    rev: 60,    // earnings revision weight
    momDis: true,
    opt: false,
    policy: true,
  });
  const on = (k, v) => setVals(s => ({ ...s, [k]: v }));
  const modified = vals.hold !== 42 || vals.infl !== 50 || vals.corr !== 55 || vals.rev !== 60 || !vals.momDis || vals.opt;
  return (
    <div className="card">
      <div className="card-head">
        <Icon name="universe" size={14} />
        <h3>Scenario controls</h3>
        <div className="meta">
          <span>{modified ? "Modified · preview below" : "Baseline"}</span>
          <button className="btn ghost sm">Reset</button>
        </div>
      </div>
      <div className="card-body">
        <div className="scenario-grid">
          <div className="sc-row">
            <div className="rtop">
              <span className="lbl">Horizon</span>
              <span className={"val " + (vals.hold !== 42 ? "mod" : "")}>{vals.hold} days</span>
            </div>
            <input type="range" min="7" max="180" value={vals.hold} onChange={e => on("hold", +e.target.value)} />
            <div className="track-ctx"><span>1W</span><span>6M</span></div>
          </div>

          <div className="sc-row">
            <div className="rtop">
              <span className="lbl">Rate shock (±bps)</span>
              <span className={"val " + (vals.infl !== 50 ? "mod" : "")}>{vals.infl - 50 > 0 ? "+" : ""}{(vals.infl - 50) * 4} bps</span>
            </div>
            <input type="range" min="0" max="100" value={vals.infl} onChange={e => on("infl", +e.target.value)} />
            <div className="track-ctx"><span>-200</span><span>0</span><span>+200</span></div>
          </div>

          <div className="sc-row">
            <div className="rtop">
              <span className="lbl">Cross-asset correlation</span>
              <span className={"val " + (vals.corr !== 55 ? "mod" : "")}>{(vals.corr / 100).toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="100" value={vals.corr} onChange={e => on("corr", +e.target.value)} />
            <div className="track-ctx"><span>0.00</span><span>1.00</span></div>
          </div>

          <div className="sc-row">
            <div className="rtop">
              <span className="lbl">Earnings revision weight</span>
              <span className={"val " + (vals.rev !== 60 ? "mod" : "")}>{vals.rev}%</span>
            </div>
            <input type="range" min="0" max="100" value={vals.rev} onChange={e => on("rev", +e.target.value)} />
            <div className="track-ctx"><span>off</span><span>dominant</span></div>
          </div>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginTop:16}}>
          <div className="toggle-row">
            <div className="t-text"><b>Momentum</b> engine</div>
            <div className="spacer" />
            <div className={"switch" + (vals.momDis ? " on" : "")} onClick={() => on("momDis", !vals.momDis)} />
          </div>
          <div className="toggle-row">
            <div className="t-text"><b>Options/flow</b> engine</div>
            <div className="spacer" />
            <div className={"switch" + (vals.opt ? " on" : "")} onClick={() => on("opt", !vals.opt)} />
          </div>
          <div className="toggle-row">
            <div className="t-text"><b>Policy constraints</b></div>
            <div className="spacer" />
            <div className={"switch" + (vals.policy ? " on" : "")} onClick={() => on("policy", !vals.policy)} />
          </div>
        </div>

        {modified && (
          <div className="delta-strip">
            <Icon name="sparkle" size={14} />
            <span>Preview delta on recommendation:</span>
            <span className="d-item">Weight <b>4.2% → 3.6%</b></span>
            <span className="d-item">Confidence <b>0.74 → 0.69</b></span>
            <span className="d-item">Expected Δ <b>+6.4% → +4.9%</b></span>
            <span className="spacer" />
            <button className="btn primary sm">Apply to thesis</button>
            <button className="btn ghost sm">Discard</button>
          </div>
        )}
      </div>
    </div>
  );
};

Object.assign(window, { ScenarioCard });
