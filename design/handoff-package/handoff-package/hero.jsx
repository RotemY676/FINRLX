// Hero + stance + confidence trio + action bar
const { useState: useStateHero } = React;

const ConfRing = ({ value, color = "var(--pos)" }) => (
  <div className="conf-ring" style={{ "--v": value, "--c": color }}>
    <span className="num">{value}</span>
  </div>
);

const HeroStrip = ({ tweaks }) => {
  const density = tweaks.density;
  return (
    <section className="hero">
      <div className="hero-top">
        <span className="rec-id">REC-2026-0419-NVDA-L</span>
        <span className="status-pill fresh">
          <span style={{width:6,height:6,borderRadius:"50%",background:"var(--pos)"}} />
          Fresh · updated 12 min ago
        </span>
        <span className="status-pill provisional">
          <Icon name="alert-triangle" size={11} />
          Provisional · data caveat on earnings window
        </span>
        <span className="status-pill neutral">
          <Icon name="history" size={11} />
          Published v4 · 2 revisions today
        </span>
      </div>

      <div className="hero-core">
        <div className="hero-title-wrap">
          <div className="hero-ticker">
            <span className="tk">NVDA</span>
            <span className="co">NVIDIA Corp · Semiconductors · US-LargeCap</span>
          </div>
          <p className="hero-thesis">
            Maintain <b>long</b> stance over a 3-month horizon. Momentum and earnings
            revisions continue to lead, but <b>engine disagreement has risen</b> and
            concentration is approaching the book limit — the platform recommends{" "}
            <span className="ul">trimming weight by 120 bps</span> rather than adding into strength.
          </p>
        </div>

        <div className="stance">
          <div>
            <div className="lbl">Stance</div>
            <div className="stance-direction">
              <span className="arrow"><Icon name="arrow-up-right" size={18} /></span>
              <span className="val pos">Long</span>
            </div>
          </div>
          <div>
            <div className="lbl">Weight</div>
            <div className="val">4.2<span className="unit">%</span></div>
          </div>
          <div>
            <div className="lbl">Horizon</div>
            <div className="val">3<span className="unit">M</span></div>
          </div>
          <div>
            <div className="lbl">Expected Δ</div>
            <div className="val pos">+6.4<span className="unit">%</span></div>
          </div>
        </div>
      </div>

      <div className="conf-trio">
        <div className="conf-card">
          <ConfRing value={74} color="var(--pos)" />
          <div className="conf-info">
            <div className="l">Model confidence</div>
            <div className="v">High <span className="tag">· 0.74 · 4 of 5 engines agree</span></div>
          </div>
        </div>
        <div className="conf-card">
          <ConfRing value={62} color="var(--caution)" />
          <div className="conf-info">
            <div className="l">Data quality</div>
            <div className="v">Mixed <span className="tag">· options IV stale by 14m</span></div>
          </div>
        </div>
        <div className="conf-card">
          <ConfRing value={92} color="var(--pos)" />
          <div className="conf-info">
            <div className="l">Operational readiness</div>
            <div className="v">Ready <span className="tag">· policy & freshness pass</span></div>
          </div>
        </div>
      </div>

      <div className="action-bar">
        <div className="group">
          <button className="btn primary">
            <Icon name="check" size={14} /> Save as current thesis
          </button>
          <button className="btn ghost">
            <Icon name="paper" size={14} /> Promote to paper
          </button>
          <button className="btn ghost">
            <Icon name="clock" size={14} /> Defer decision
          </button>
        </div>
        <div className="spacer" />
        <div className="group">
          <button className="btn ghost sm"><Icon name="compare" size={13} /> Compare engines</button>
          <button className="btn ghost sm"><Icon name="replay" size={13} /> Replay snapshot</button>
          <button className="btn ghost sm icon-only" title="Bookmark"><Icon name="bookmark" size={14} /></button>
          <button className="btn ghost sm icon-only" title="Share"><Icon name="share" size={14} /></button>
          <button className="btn ghost sm icon-only" title="More"><Icon name="dots" size={14} /></button>
        </div>
      </div>
    </section>
  );
};

Object.assign(window, { HeroStrip, ConfRing });
