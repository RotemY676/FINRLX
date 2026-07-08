// Onboarding — step components
const { useState: useStateOb } = React;

const ObTopBar = ({ active, onClose }) => (
  <header className="ob-top">
    <div className="ob-brand">
      <div className="brand-mark" />
      <span>QuantPipeline<em> · setup</em></span>
    </div>
    <div className="ob-steps">
      {OB_STEPS.map((s, i) => {
        const ai = OB_STEPS.findIndex(x => x.id === active);
        const state = i < ai ? "done" : i === ai ? "active" : "";
        return (
          <React.Fragment key={s.id}>
            <div className={"ob-step " + state}>
              <span className="n">{i < ai ? "✓" : (i + 1)}</span>
              <span>{s.label}</span>
            </div>
            {i < OB_STEPS.length - 1 && <span className="ob-sep" />}
          </React.Fragment>
        );
      })}
    </div>
    <div className="ob-top-actions">
      <button className="btn ghost sm" onClick={onClose}>Save & exit</button>
    </div>
  </header>
);

const ObFooter = ({ onBack, onNext, nextLabel = "Continue", backLabel = "Back", disabled, hint }) => (
  <div className="ob-footer">
    <div className="left">{hint}</div>
    <div style={{display:"flex", gap:10}}>
      {onBack && <button className="btn ghost" onClick={onBack}>{backLabel}</button>}
      {onNext && <button className="btn primary" onClick={onNext} disabled={disabled}>{nextLabel} →</button>}
    </div>
  </div>
);

/* ---------- Step 1: sign-in ---------- */
const StepSignIn = ({ onNext }) => {
  const [email, setEmail] = useStateOb("rivka@rivkacap.com");
  const [password, setPassword] = useStateOb("");

  return (
    <div className="ob-card">
      <div className="ob-head">
        <span className="ob-eyebrow">Welcome</span>
        <h1 className="ob-title">Sign in to start your workspace</h1>
        <p className="ob-lede">
          QuantPipeline is tenant-isolated. Every workspace is a separate account — your data,
          your models, your policies. If your firm uses SSO, pick it below.
        </p>
      </div>

      <div className="ob-signin-side">
        <div className="ob-signin-panel">
          <h3>Single sign-on</h3>
          <p>Recommended — MFA and session revocation honored from your IdP.</p>
          <div className="ob-sso">
            <button className="ob-sso-btn" onClick={onNext}>
              <span className="logo google">G</span>
              Continue with Google Workspace
              <span className="tag">SAML 2.0</span>
            </button>
            <button className="ob-sso-btn" onClick={onNext}>
              <span className="logo ms">M</span>
              Continue with Microsoft Entra ID
              <span className="tag">OIDC</span>
            </button>
            <button className="ob-sso-btn" onClick={onNext}>
              <span className="logo okta">O</span>
              Continue with Okta
              <span className="tag">SCIM</span>
            </button>
          </div>
        </div>
        <div className="vrule" />
        <div className="ob-signin-panel">
          <h3>Email & password</h3>
          <p>For individual seats and trial workspaces. MFA required after first login.</p>
          <form className="ob-signin" onSubmit={e => { e.preventDefault(); onNext(); }}>
            <div className="ob-input">
              <label>Work email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@firm.com" />
            </div>
            <div className="ob-input">
              <label>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
            <button className="btn primary" type="submit" style={{marginTop:4}}>Continue →</button>
          </form>
        </div>
      </div>

      <div className="ob-footer" style={{borderTop:"none", paddingTop:0}}>
        <div className="left">
          By continuing you agree to the <u>Terms</u> and <u>DPA</u>. SOC 2 Type II · ISO 27001.
        </div>
      </div>
    </div>
  );
};

/* ---------- Step 2: org setup ---------- */
const StepOrg = ({ data, setData, onNext, onBack }) => (
  <div className="ob-card wide">
    <div className="ob-head">
      <span className="ob-eyebrow">Step 2 of 5 · Your firm</span>
      <h1 className="ob-title">Tell us about your firm</h1>
      <p className="ob-lede">
        We'll tune defaults for universe, data feeds, and model presets based on what you trade.
        All of this is editable later.
      </p>
    </div>

    <div className="ob-form">
      <div className="ob-input full">
        <label>Firm name</label>
        <input value={data.firmName} onChange={e => setData({...data, firmName: e.target.value})} placeholder="Acme Capital" />
      </div>
      <div className="ob-input">
        <label>Primary domain</label>
        <input value={data.domain} onChange={e => setData({...data, domain: e.target.value})} placeholder="acmecap.com" />
      </div>
      <div className="ob-input">
        <label>Time zone</label>
        <input value={data.tz} onChange={e => setData({...data, tz: e.target.value})} placeholder="Asia/Jerusalem" />
      </div>
    </div>

    <div>
      <label style={{fontSize:12, fontWeight:500, color:"var(--ink-2)", display:"block", marginBottom:10}}>Firm size</label>
      <div className="ob-tile-group">
        {FIRM_SIZES.map(o => (
          <div key={o.id} className={"ob-tile" + (data.size === o.id ? " active" : "")}
               onClick={() => setData({...data, size: o.id})}>
            <div className="t">{o.t}</div>
            <div className="d">{o.d}</div>
          </div>
        ))}
      </div>
    </div>

    <div>
      <label style={{fontSize:12, fontWeight:500, color:"var(--ink-2)", display:"block", marginBottom:10}}>Decision style</label>
      <div className="ob-tile-group">
        {FIRM_STYLES.map(o => (
          <div key={o.id} className={"ob-tile" + (data.style === o.id ? " active" : "")}
               onClick={() => setData({...data, style: o.id})}>
            <div className="t">{o.t}</div>
            <div className="d">{o.d}</div>
          </div>
        ))}
      </div>
    </div>

    <div>
      <label style={{fontSize:12, fontWeight:500, color:"var(--ink-2)", display:"block", marginBottom:10}}>Asset classes <span style={{color:"var(--ink-3)", fontWeight:400}}>· multi-select</span></label>
      <div className="ob-tile-group">
        {ASSET_CLASSES.map(o => {
          const on = data.assets.includes(o.id);
          return (
            <div key={o.id} className={"ob-tile" + (on ? " active" : "")}
                 onClick={() => setData({
                   ...data,
                   assets: on ? data.assets.filter(x => x !== o.id) : [...data.assets, o.id]
                 })}>
              <div className="t">{o.t}</div>
              <div className="d">{o.d}</div>
            </div>
          );
        })}
      </div>
    </div>

    <ObFooter onBack={onBack} onNext={onNext}
              disabled={!data.firmName || !data.size || !data.style || !data.assets.length}
              hint="All defaults are editable from Settings later." />
  </div>
);

/* ---------- Step 3: role + permissions matrix ---------- */
const StepRoles = ({ data, setData, onNext, onBack }) => {
  const [showMatrix, setShowMatrix] = useStateOb(false);
  return (
    <div className="ob-card wide">
      <div className="ob-head">
        <span className="ob-eyebrow">Step 3 of 5 · Your role</span>
        <h1 className="ob-title">What's your role?</h1>
        <p className="ob-lede">
          This is <em>your</em> role in this workspace. Separation of duties is enforced by default
          — admins cannot publish trades, and PMs cannot edit the policies that govern them.
          Change it later from Admin · Members.
        </p>
      </div>

      <div className="ob-roles">
        {ROLES.map(r => (
          <div key={r.id} className={"ob-role" + (data.role === r.id ? " active" : "")}
               onClick={() => setData({...data, role: r.id})}>
            <div className="ob-role-icon"><Icon name={r.icon} size={18} /></div>
            <div className="ob-role-body">
              <h4>{r.t}</h4>
              <p>{r.d}</p>
              <div className="ob-role-perms">
                {r.perms.map(p => (
                  <span key={p.t} className={"ob-perm" + (p.ok ? "" : " deny")}>
                    {p.ok ? "✓" : "×"} {p.t}
                  </span>
                ))}
              </div>
            </div>
            <span className="ob-role-radio" />
          </div>
        ))}
      </div>

      <div>
        <button className="btn ghost sm" onClick={() => setShowMatrix(v => !v)}>
          {showMatrix ? "Hide" : "Show"} full permissions matrix <Icon name={showMatrix ? "chevron-up" : "chevron-down"} size={11} />
        </button>
        {showMatrix && (
          <div className="ob-matrix" style={{marginTop:14}}>
            <table>
              <thead>
                <tr>
                  <th>Capability</th>
                  <th>Admin</th>
                  <th>PM</th>
                  <th>Analyst</th>
                  <th>Viewer</th>
                </tr>
              </thead>
              <tbody>
                {PERM_ROWS.map((r, i) => (
                  <tr key={i}>
                    <td className="action">
                      {r.action}
                      <span className="sub">{r.cat} · {r.sub}</span>
                    </td>
                    <td className={"cell " + r.admin}>{r.admin === "y" ? "✓" : r.admin === "lim" ? "limited" : "—"}</td>
                    <td className={"cell " + r.pm}>{r.pm === "y" ? "✓" : r.pm === "lim" ? "limited" : "—"}</td>
                    <td className={"cell " + r.ana}>{r.ana === "y" ? "✓" : r.ana === "lim" ? "limited" : "—"}</td>
                    <td className={"cell " + r.viewer}>{r.viewer === "y" ? "✓" : r.viewer === "lim" ? "limited" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ObFooter onBack={onBack} onNext={onNext} disabled={!data.role}
                hint="Roles are declarative — we map them to your IdP groups if you add SSO later." />
    </div>
  );
};

/* ---------- Step 4: invites ---------- */
const StepInvites = ({ data, setData, onNext, onBack }) => {
  const updateRow = (i, patch) => {
    const n = [...data.invites];
    n[i] = { ...n[i], ...patch };
    setData({...data, invites: n});
  };
  const remove = (i) => setData({...data, invites: data.invites.filter((_, j) => j !== i)});
  const add = () => setData({...data, invites: [...data.invites, { email: "", role: "pm" }]});

  const valid = data.invites.filter(r => r.email && r.email.includes("@")).length;

  return (
    <div className="ob-card">
      <div className="ob-head">
        <span className="ob-eyebrow">Step 4 of 5 · Invite team</span>
        <h1 className="ob-title">Who else is in this workspace?</h1>
        <p className="ob-lede">
          We'll send each person a magic link valid for 48 hours. You can skip and invite later
          from Admin · Members. Invitees won't see anything until they accept and set MFA.
        </p>
      </div>

      <div className="ob-invite">
        {data.invites.map((row, i) => (
          <div key={i} className="ob-invite-row">
            <input type="email" placeholder="colleague@firm.com" value={row.email}
                   onChange={e => updateRow(i, {email: e.target.value})} />
            <select value={row.role} onChange={e => updateRow(i, {role: e.target.value})}>
              <option value="admin">Admin</option>
              <option value="pm">Portfolio manager</option>
              <option value="analyst">Analyst / Quant</option>
              <option value="viewer">Viewer</option>
            </select>
            <button className="ob-invite-remove" onClick={() => remove(i)} title="Remove">
              <Icon name="x" size={13} />
            </button>
          </div>
        ))}
        <button className="ob-invite-add" onClick={add}>
          <Icon name="plus" size={12} /> Add another
        </button>
      </div>

      <ObFooter onBack={onBack} onNext={onNext}
                nextLabel={valid ? `Send ${valid} invite${valid > 1 ? "s" : ""} & continue` : "Skip for now"}
                hint="Pro tip: invite your compliance observer as Viewer — they see decisions without weights." />
    </div>
  );
};

/* ---------- Step 5: review ---------- */
const StepReview = ({ data, onNext, onBack, goToStep }) => {
  const firmSize = FIRM_SIZES.find(s => s.id === data.size);
  const firmStyle = FIRM_STYLES.find(s => s.id === data.style);
  const assets = ASSET_CLASSES.filter(a => data.assets.includes(a.id)).map(a => a.t).join(", ");
  const roleObj = ROLES.find(r => r.id === data.role);
  const validInvites = data.invites.filter(r => r.email && r.email.includes("@"));

  return (
    <div className="ob-card">
      <div className="ob-head">
        <span className="ob-eyebrow">Step 5 of 5 · Review</span>
        <h1 className="ob-title">Does this look right?</h1>
        <p className="ob-lede">
          Creating your workspace takes about 20 seconds. We'll provision a default universe
          ({data.assets.includes("eq") ? "US-LargeCap-500" : "Macro-Cross-Asset"}), seed sample data,
          and route you to your first decision.
        </p>
      </div>

      <div className="ob-review">
        <div className="ob-review-row">
          <span className="k">Workspace</span>
          <div className="v">{data.firmName}
            <span className="sub">{data.domain} · {data.tz}</span>
          </div>
          <span className="edit" onClick={() => goToStep("org")}>Edit</span>
        </div>
        <div className="ob-review-row">
          <span className="k">Firm profile</span>
          <div className="v">{firmSize?.t} · {firmStyle?.t}
            <span className="sub">Asset classes: {assets}</span>
          </div>
          <span className="edit" onClick={() => goToStep("org")}>Edit</span>
        </div>
        <div className="ob-review-row">
          <span className="k">Your role</span>
          <div className="v">{roleObj?.t}
            <span className="sub">{roleObj?.d.split(".")[0]}.</span>
          </div>
          <span className="edit" onClick={() => goToStep("roles")}>Edit</span>
        </div>
        <div className="ob-review-row">
          <span className="k">Team invites</span>
          <div className="v">
            {validInvites.length ? `${validInvites.length} pending invite${validInvites.length > 1 ? "s" : ""}` : "None — you'll work solo for now"}
            {validInvites.length > 0 && (
              <span className="sub">
                {validInvites.slice(0, 3).map(r => `${r.email} (${ROLE_LABEL[r.role]})`).join(" · ")}
                {validInvites.length > 3 && ` · +${validInvites.length - 3} more`}
              </span>
            )}
          </div>
          <span className="edit" onClick={() => goToStep("team")}>Edit</span>
        </div>
        <div className="ob-review-row">
          <span className="k">Security defaults</span>
          <div className="v">MFA required · SOC 2 Type II tenant
            <span className="sub">Audit log enabled · Data residency: eu-central-1</span>
          </div>
          <span className="edit">Advanced</span>
        </div>
      </div>

      <ObFooter onBack={onBack} onNext={onNext} nextLabel="Create workspace"
                hint="You can change any of this from Admin later." />
    </div>
  );
};

/* ---------- Step 6: done ---------- */
const StepDone = ({ firmName, onDone }) => (
  <div className="ob-card">
    <div className="ob-done">
      <div className="ob-done-mark">✓</div>
      <h2>Welcome to {firmName || "your workspace"}</h2>
      <p>
        Your tenant is provisioned. We seeded sample recommendations on NVDA, MSFT, and AMZN
        so you can see the engine without risk — nothing is routed to a live OMS until you
        connect one from Admin · Integrations.
      </p>
      <div className="ob-next">
        <div className="ob-next-card" onClick={onDone}>
          <div className="t">→ Open Overview</div>
          <div className="d">Portfolio health, triage queue, activity</div>
        </div>
        <div className="ob-next-card">
          <div className="t">Connect data sources</div>
          <div className="d">Bloomberg, Refinitiv, alt data, your OMS</div>
        </div>
        <div className="ob-next-card">
          <div className="t">Configure policies</div>
          <div className="d">Position limits, concentration, VaR caps</div>
        </div>
      </div>
    </div>
  </div>
);

/* ---------- Team management (post-onboarding admin view) ---------- */
const TeamManagement = () => {
  const [tab, setTab] = useStateOb("members");
  const byStatus = {
    active:   TEAM_MEMBERS.filter(m => m.status === "active").length,
    pending:  TEAM_MEMBERS.filter(m => m.status === "pending").length,
    inactive: TEAM_MEMBERS.filter(m => m.status === "inactive").length,
  };

  return (
    <div className="ob-card ob-team-card">
      <div className="ob-team-head">
        <div className="ob-head">
          <span className="ob-eyebrow">Admin · members</span>
          <h1 className="ob-title" style={{fontSize:28}}>Team management</h1>
          <p className="ob-lede" style={{fontSize:13}}>
            6 seats used of 15 on Growth plan · <u>upgrade</u>
          </p>
        </div>
        <div style={{display:"flex", gap:8}}>
          <button className="btn ghost sm"><Icon name="external" size={12}/> Export</button>
          <button className="btn ghost sm"><Icon name="shield" size={12}/> SCIM provisioning</button>
          <button className="btn primary sm"><Icon name="plus" size={12}/> Invite members</button>
        </div>
      </div>

      <div className="ob-team-tabs">
        {[
          { id: "members", label: "Members", ct: TEAM_MEMBERS.length },
          { id: "pending", label: "Pending", ct: byStatus.pending },
          { id: "roles",   label: "Roles & permissions" },
          { id: "sso",     label: "SSO & security" },
          { id: "audit",   label: "Audit log" },
        ].map(t => (
          <div key={t.id} className={"ob-team-tab" + (tab === t.id ? " active" : "")}
               onClick={() => setTab(t.id)}>
            {t.label}
            {t.ct !== undefined && <span className="ct">{t.ct}</span>}
          </div>
        ))}
      </div>

      {tab === "members" && (
        <div className="ob-member-table">
          <table>
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Status</th>
                <th>MFA</th>
                <th>Last active</th>
                <th style={{width:50}}></th>
              </tr>
            </thead>
            <tbody>
              {TEAM_MEMBERS.map(m => (
                <tr key={m.email}>
                  <td>
                    <span className={"ob-avatar " + m.av}>{m.init}</span>
                    <span className="ob-member-name">
                      {m.name}
                      <span className="em">{m.email}</span>
                    </span>
                  </td>
                  <td><span className={"ob-role-chip " + m.role}>{ROLE_LABEL[m.role]}</span></td>
                  <td>
                    <span className={"ob-status-dot " + m.status} />
                    <span style={{fontSize:12, color:"var(--ink-2)", textTransform:"capitalize"}}>{m.status}</span>
                  </td>
                  <td style={{fontSize:12, color: m.mfa ? "var(--pos-soft-ink)" : "var(--breach-soft-ink)", fontFamily:"var(--font-mono)"}}>
                    {m.mfa ? "✓ enabled" : "⚠ required"}
                  </td>
                  <td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>{m.last}</td>
                  <td>
                    <button className="ob-overflow">⋯</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "pending" && (
        <div className="ob-member-table">
          <table>
            <thead>
              <tr><th>Invited</th><th>Role</th><th>Sent</th><th>Expires</th><th></th></tr>
            </thead>
            <tbody>
              <tr>
                <td><span className="ob-member-name">shira@rivkacap.com<span className="em">Invited by Rivka Shoval</span></span></td>
                <td><span className="ob-role-chip ana">Analyst</span></td>
                <td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>3d ago</td>
                <td style={{fontSize:12, color:"var(--caution-soft-ink)", fontFamily:"var(--font-mono)"}}>in 45h</td>
                <td><button className="btn ghost sm">Resend</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {tab === "roles" && (
        <div className="ob-matrix">
          <table>
            <thead>
              <tr><th>Capability</th><th>Admin</th><th>PM</th><th>Analyst</th><th>Viewer</th></tr>
            </thead>
            <tbody>
              {PERM_ROWS.map((r, i) => (
                <tr key={i}>
                  <td className="action">{r.action}<span className="sub">{r.cat} · {r.sub}</span></td>
                  <td className={"cell " + r.admin}>{r.admin === "y" ? "✓" : r.admin === "lim" ? "limited" : "—"}</td>
                  <td className={"cell " + r.pm}>{r.pm === "y" ? "✓" : r.pm === "lim" ? "limited" : "—"}</td>
                  <td className={"cell " + r.ana}>{r.ana === "y" ? "✓" : r.ana === "lim" ? "limited" : "—"}</td>
                  <td className={"cell " + r.viewer}>{r.viewer === "y" ? "✓" : r.viewer === "lim" ? "limited" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "sso" && (
        <div style={{display:"grid", gap:14}}>
          <div className="ob-review-row">
            <span className="k">Identity provider</span>
            <div className="v">Okta
              <span className="sub">SAML 2.0 · auto-provision via SCIM · last sync 14m ago</span>
            </div>
            <span className="edit">Configure</span>
          </div>
          <div className="ob-review-row">
            <span className="k">MFA policy</span>
            <div className="v">Required for all roles
              <span className="sub">TOTP or WebAuthn · session max 12h · 6 members compliant</span>
            </div>
            <span className="edit">Edit</span>
          </div>
          <div className="ob-review-row">
            <span className="k">IP allow-list</span>
            <div className="v">Off
              <span className="sub">Recommended for production workspaces</span>
            </div>
            <span className="edit">Enable</span>
          </div>
          <div className="ob-review-row">
            <span className="k">Data residency</span>
            <div className="v">eu-central-1 (Frankfurt)
              <span className="sub">Locked · change requires support ticket</span>
            </div>
            <span className="edit">—</span>
          </div>
        </div>
      )}

      {tab === "audit" && (
        <div className="ob-member-table">
          <table>
            <thead><tr><th>Event</th><th>Actor</th><th>Target</th><th>When</th></tr></thead>
            <tbody>
              <tr><td style={{fontFamily:"var(--font-mono)", fontSize:12}}>member.invited</td><td>Rivka Shoval</td><td>shira@rivkacap.com</td><td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>3d ago · 09:14</td></tr>
              <tr><td style={{fontFamily:"var(--font-mono)", fontSize:12}}>role.changed</td><td>Rivka Shoval</td><td>Tali Yaron → Viewer</td><td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>5d ago · 16:22</td></tr>
              <tr><td style={{fontFamily:"var(--font-mono)", fontSize:12}}>policy.edited</td><td>Rivka Shoval</td><td>Sector concentration cap 25→22%</td><td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>1w ago</td></tr>
              <tr><td style={{fontFamily:"var(--font-mono)", fontSize:12}}>sso.configured</td><td>Rivka Shoval</td><td>Okta · SAML 2.0</td><td style={{fontSize:12, color:"var(--ink-3)", fontFamily:"var(--font-mono)"}}>2w ago</td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

Object.assign(window, {
  ObTopBar, StepSignIn, StepOrg, StepRoles, StepInvites, StepReview, StepDone, TeamManagement,
});
