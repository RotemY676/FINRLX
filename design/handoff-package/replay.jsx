// Replay workspace — UI components
// Consumes: REPLAY_EVENTS, REPLAY_ENGINE_STATES, interpPrice, eventIndexForT
const { useState, useEffect, useMemo, useRef } = React;

// ====== Header ======================================================
const ReplayHeader = ({ event, priceNow, priceEntry, pos }) => {
  const pnl = pos > 0 ? (priceNow - priceEntry) * 100 : 0;  // shown for original 100 shares
  const pnlPct = (priceNow - priceEntry) / priceEntry;
  return (
    <div className="rp-header">
      <div>
        <div className="rp-crumb">REPLAY · CASE #RP-2026-0113-NVDA</div>
        <h1 className="rp-title">
          <span className="tk">NVDA</span>
          long thesis · published Jan 13
        </h1>
        <p className="rp-subtitle">
          Scrubbing 14-day window. Viewing state at <b>{event.when}</b> — "{event.title}"
        </p>
      </div>
      <div className="rp-outcome-card">
        <div className="rp-outcome-stat">
          <div className="k">Entry</div>
          <div className="v">${priceEntry.toFixed(2)}</div>
        </div>
        <div className="rp-outcome-stat">
          <div className="k">At cursor</div>
          <div className="v">${priceNow.toFixed(2)}</div>
        </div>
        <div className="rp-outcome-stat">
          <div className="k">P&amp;L (per 100sh)</div>
          <div className={"v " + (pnl >= 0 ? "pos" : "breach")}>
            {pnl >= 0 ? "+" : ""}${pnl.toFixed(0)} · {formatPct(pnlPct)}
          </div>
        </div>
      </div>
    </div>
  );
};

// ====== Scrubber timeline ==========================================
const Scrubber = ({ t, onT, playing, onPlay, speed, onSpeed, event }) => {
  const trackRef = useRef(null);

  const onTrackDown = (e) => {
    const onMove = (ev) => {
      const rect = trackRef.current.getBoundingClientRect();
      const clientX = ev.touches ? ev.touches[0].clientX : ev.clientX;
      const nt = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      onT(nt);
    };
    onMove(e);
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  return (
    <section className="rp-scrubber">
      <div className="rp-scrub-meta">
        <div className="rp-scrub-title">
          TIMELINE
          <span className="now">{event.when}</span>
        </div>
        <div className="rp-scrub-controls">
          <button className="rp-scrub-btn" title="Jump to genesis" onClick={() => onT(0)}>
            <Icon name="chevron-right" size={12} style={{ transform: "rotate(180deg) scaleX(2)" }} />
          </button>
          <button className="rp-scrub-btn" title="Previous event" onClick={() => {
            const idx = eventIndexForT(t - 0.001);
            onT(REPLAY_EVENTS[Math.max(0, idx)].t);
          }}>
            <Icon name="chevron-right" size={12} style={{ transform: "rotate(180deg)" }} />
          </button>
          <button className="rp-scrub-btn primary" title={playing ? "Pause" : "Play"} onClick={onPlay}>
            {playing
              ? <span style={{ fontSize: 12, lineHeight: 1 }}>❚❚</span>
              : <span style={{ fontSize: 12, lineHeight: 1, marginLeft: 2 }}>▶</span>}
          </button>
          <button className="rp-scrub-btn" title="Next event" onClick={() => {
            const idx = eventIndexForT(t);
            onT(REPLAY_EVENTS[Math.min(REPLAY_EVENTS.length - 1, idx + 1)].t);
          }}>
            <Icon name="chevron-right" size={12} />
          </button>
          <button className="rp-scrub-btn" title="Jump to now" onClick={() => onT(1)}>
            <Icon name="chevron-right" size={12} style={{ transform: "scaleX(2)" }} />
          </button>
          <div className="rp-scrub-speed">
            {[0.5, 1, 2, 4].map(s => (
              <button key={s} className={s === speed ? "active" : ""} onClick={() => onSpeed(s)}>
                {s}×
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="rp-timeline" ref={trackRef} onMouseDown={onTrackDown}>
        <div className="rp-timeline-track">
          <div className="rp-timeline-progress" style={{ width: (t * 100) + "%" }} />
        </div>
        {REPLAY_EVENTS.map((ev, i) => (
          <div
            key={i}
            className="rp-event"
            style={{ left: (ev.t * 100) + "%" }}
            onMouseDown={(e) => { e.stopPropagation(); onT(ev.t); }}
            title={ev.title}
          >
            <div className="rp-event-label">{ev.label}</div>
            <div className={"rp-event-dot " + ev.kind} />
          </div>
        ))}
        <div
          className="rp-timeline-cursor"
          style={{ left: (t * 100) + "%" }}
        />
        <div className="rp-timeline-axis">
          <span>JAN 12</span>
          <span>JAN 15</span>
          <span>JAN 18</span>
          <span>JAN 21</span>
          <span>JAN 24</span>
          <span>JAN 26</span>
        </div>
      </div>
    </section>
  );
};

// ====== Engine state snapshot (left column) ========================
const EnginePanel = ({ stateNow, statePrev }) => {
  const engines = [
    { key: "momentum",  label: "Momentum"  },
    { key: "value",     label: "Value"     },
    { key: "quality",   label: "Quality"   },
    { key: "sentiment", label: "Sentiment" },
    { key: "macro",     label: "Macro"     },
  ];
  const maxConf = Math.max(...engines.map(e => stateNow[e.key]?.c || 0));
  return (
    <div className="rp-card">
      <div className="rp-card-head">
        <div className="rp-card-title">ENGINE STATE · AT CURSOR</div>
        <div className="rp-card-meta">5 engines</div>
      </div>
      <div className="rp-card-body">
        <div className="rp-engines">
          {engines.map(e => {
            const s = stateNow[e.key];
            const prev = statePrev?.[e.key];
            const dominant = s && s.c === maxConf;
            if (!s) {
              return (
                <div key={e.key} className="rp-engine-row">
                  <div className="rp-engine-head">
                    <div className="rp-engine-name">{e.label}</div>
                    <div className="rp-engine-stance none">feed stale</div>
                  </div>
                  <div className="rp-engine-notavail">no reading at this timestamp</div>
                </div>
              );
            }
            const delta = prev?.c != null ? s.c - prev.c : null;
            const barCls = s.c >= 0.75 ? "pos" : s.c >= 0.55 ? "" : s.c >= 0.4 ? "caution" : "breach";
            return (
              <div key={e.key} className={"rp-engine-row" + (dominant ? " dominant" : "")}>
                <div className="rp-engine-head">
                  <div className="rp-engine-name">{e.label}</div>
                  <div className={"rp-engine-stance " + s.s}>{s.s.toUpperCase()}</div>
                </div>
                <div className="rp-engine-conf">
                  <div className="bar"><span className={barCls} style={{ width: (s.c * 100) + "%" }} /></div>
                  <span className="v">{s.c.toFixed(2)}</span>
                  <span className={"delta " + (delta > 0.01 ? "up" : delta < -0.01 ? "down" : "")}>
                    {delta != null ? (delta > 0 ? "+" : "") + delta.toFixed(2) : "—"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ====== Chart (center) =============================================
const PriceChart = ({ t }) => {
  const W = 720, H = 280, pad = { l: 40, r: 14, t: 18, b: 26 };
  const series = REPLAY_PRICE;
  const prices = series.map(s => s.p);
  const pMin = Math.min(...prices) - 5;
  const pMax = Math.max(...prices) + 5;

  const x = (tt) => pad.l + tt * (W - pad.l - pad.r);
  const y = (p)  => pad.t + (1 - (p - pMin) / (pMax - pMin)) * (H - pad.t - pad.b);

  // Trajectory path: what HAS happened up to t
  const walked = series.filter(s => s.t <= t);
  if (walked.length === 0 || walked[walked.length - 1].t < t) {
    const interp = interpPrice(t);
    walked.push(interp);
  }
  const future = series.filter(s => s.t > t);

  const lineD = (pts) => pts.map((s, i) =>
    (i === 0 ? "M " : "L ") + x(s.t) + " " + y(s.p)
  ).join(" ");

  // gridlines
  const gridPrices = [];
  for (let p = Math.ceil(pMin / 20) * 20; p <= pMax; p += 20) gridPrices.push(p);

  const now = interpPrice(t);

  // Event annotations (only for events <= t)
  const visible = REPLAY_EVENTS.filter(e => e.t <= t);

  return (
    <div className="rp-chart">
      <svg viewBox={`0 0 ${W} ${H}`} className="rp-chart-svg" preserveAspectRatio="none">
        {/* gridlines */}
        {gridPrices.map(p => (
          <g key={p}>
            <line x1={pad.l} x2={W - pad.r} y1={y(p)} y2={y(p)} stroke="var(--line)" strokeDasharray="2 3" />
            <text x={pad.l - 6} y={y(p) + 3} fontSize="9.5" fill="var(--ink-4)" textAnchor="end" fontFamily="var(--font-mono)">
              {p}
            </text>
          </g>
        ))}
        {/* x-axis marks */}
        {[0, 0.25, 0.5, 0.75, 1].map(tt => (
          <text key={tt} x={x(tt)} y={H - 8} fontSize="9" fill="var(--ink-4)" textAnchor="middle" fontFamily="var(--font-mono)">
            {["D0","D3","D7","D10","D14"][[0,0.25,0.5,0.75,1].indexOf(tt)]}
          </text>
        ))}

        {/* entry line */}
        <line x1={pad.l} x2={W - pad.r} y1={y(612.40)} y2={y(612.40)} stroke="var(--accent)" strokeDasharray="4 4" strokeWidth="1" opacity="0.5" />
        <text x={W - pad.r - 4} y={y(612.40) - 4} fontSize="9.5" fill="var(--accent)" textAnchor="end" fontFamily="var(--font-mono)">entry $612.40</text>

        {/* future (ghosted) */}
        {future.length > 0 && (
          <path
            d={lineD([walked[walked.length - 1], ...future])}
            stroke="var(--ink-4)"
            strokeWidth="1.5"
            strokeDasharray="3 4"
            fill="none"
            opacity="0.45"
          />
        )}

        {/* walked area fill */}
        <path
          d={lineD(walked) + ` L ${x(walked[walked.length - 1].t)} ${y(pMin)} L ${x(walked[0].t)} ${y(pMin)} Z`}
          fill="var(--primary-soft)"
          opacity="0.5"
        />
        {/* walked line */}
        <path
          d={lineD(walked)}
          stroke="var(--primary)"
          strokeWidth="2"
          fill="none"
        />

        {/* event markers on walked path */}
        {visible.map((ev, i) => {
          const interp = interpPrice(ev.t);
          return (
            <g key={i}>
              <line
                x1={x(ev.t)} x2={x(ev.t)}
                y1={y(interp.p) - 6} y2={y(interp.p) + 6}
                stroke="var(--ink-3)"
                strokeWidth="1"
                opacity="0.4"
              />
              <circle cx={x(ev.t)} cy={y(interp.p)} r="3"
                fill={{
                  rescore: "var(--primary)",
                  publish: "var(--pos)",
                  news: "var(--accent)",
                  caution: "var(--caution)",
                  action: "var(--ink)",
                  breach: "var(--breach)",
                }[ev.kind]}
                stroke="var(--surface)"
                strokeWidth="1.5"
              />
            </g>
          );
        })}

        {/* now cursor */}
        <line x1={x(t)} x2={x(t)} y1={pad.t} y2={H - pad.b} stroke="var(--primary)" strokeWidth="1" opacity="0.5" />
        <circle cx={x(t)} cy={y(now.p)} r="5" fill="var(--primary)" stroke="var(--surface)" strokeWidth="2" />
      </svg>
    </div>
  );
};

const ChartPanel = ({ t }) => {
  const now = interpPrice(t);
  return (
    <div className="rp-card">
      <div className="rp-card-head">
        <div className="rp-card-title">PRICE &amp; POSITION · REPLAY</div>
        <div className="rp-card-meta">
          ${now.p.toFixed(2)} · {now.pos}sh
        </div>
      </div>
      <div className="rp-chart-wrap">
        <PriceChart t={t} />
        <div className="rp-chart-legend">
          <span className="rp-legend-item">
            <span className="rp-legend-dot" style={{ background: "var(--primary)", height: 2 }} />
            <b>Price</b> (walked)
          </span>
          <span className="rp-legend-item">
            <span className="rp-legend-dot" style={{ background: "var(--ink-4)", height: 2 }} />
            Future (ghosted)
          </span>
          <span className="rp-legend-item">
            <span className="rp-legend-dot" style={{ background: "var(--accent)", height: 2 }} />
            Entry line
          </span>
          <span className="rp-legend-item" style={{ marginLeft: "auto" }}>
            Events · <b>{REPLAY_EVENTS.filter(e => e.t <= t).length}</b> of {REPLAY_EVENTS.length} revealed
          </span>
        </div>
      </div>
    </div>
  );
};

// ====== Narrative log (right column) ===============================
const LogPanel = ({ t, onJump }) => {
  return (
    <div className="rp-card">
      <div className="rp-card-head">
        <div className="rp-card-title">NARRATIVE LOG</div>
        <div className="rp-card-meta">{REPLAY_EVENTS.length} events</div>
      </div>
      <div className="rp-card-body">
        <div className="rp-log">
          {REPLAY_EVENTS.map((ev, i) => {
            const isCurrent = Math.abs(ev.t - t) < 0.02;
            const isFuture = ev.t > t + 0.02;
            return (
              <div
                key={i}
                className={"rp-log-entry" + (isCurrent ? " current" : isFuture ? " future" : "")}
                onClick={() => onJump(ev.t)}
                style={{ cursor: "pointer" }}
              >
                <div className="rp-log-time">{ev.when.split(", ")[1] || ev.when}</div>
                <div className="rp-log-content">
                  <div className={"rp-log-kind " + ev.kind}>{ev.label}</div>
                  <div className="rp-log-text">{ev.title}</div>
                  <div className="rp-log-actor">
                    {ev.actor === "system"
                      ? <><span className="chip" style={{ background: "var(--primary)" }}>S</span> system rescore</>
                      : ev.actor === "news"
                      ? <><span className="chip" style={{ background: "var(--accent)" }}>N</span> news feed</>
                      : ev.actor === "ops"
                      ? <><span className="chip" style={{ background: "var(--caution)" }}>O</span> ops</>
                      : <><span className="chip">{ev.actor}</span> {ev.actor === "RM" ? "Rachel Moy" : "Tanvi Nair"}</>
                    }
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ====== Counterfactual footer ======================================
const CounterfactualFooter = ({ eventIdx }) => {
  // A few canned counterfactuals tied to specific events
  const CF = {
    6: "Had you held position through the IV spike, drawdown would have reached −3.8% before recovery.",
    7: "The 30% trim locked ~$3,015 profit — fully exiting here would have captured another +$420 on the remainder.",
    8: "Without the sentiment engine's read on the export headline, position would still show the stale +0.84 confidence.",
    9: "Quality feed stale for 47m — decisions made in this window used last-known fundamentals (as of Jan 23, 19:40).",
  };
  const note = CF[eventIdx] || "At this point no counterfactual of note — state evolved as the thesis expected.";
  return (
    <footer className="rp-footer">
      <div className="rp-cf-label">
        <span className="dot" />
        COUNTERFACTUAL
      </div>
      <div className="rp-cf-claim">
        <b>What if?</b> {note}
      </div>
      <div className="rp-cf-actions">
        <button className="btn ghost">Fork thesis</button>
        <button className="btn primary">Add to post-mortem</button>
      </div>
    </footer>
  );
};

Object.assign(window, {
  ReplayHeader,
  Scrubber,
  EnginePanel,
  ChartPanel,
  LogPanel,
  CounterfactualFooter,
});
