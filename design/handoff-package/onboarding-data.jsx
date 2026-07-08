// Onboarding — data

const OB_STEPS = [
  { id: "signin",  label: "Sign in" },
  { id: "org",     label: "Your firm" },
  { id: "roles",   label: "Your role" },
  { id: "team",    label: "Invite team" },
  { id: "review",  label: "Review" },
];

const FIRM_SIZES = [
  { id: "sm",  t: "Small shop",   d: "1–9 seats · single book" },
  { id: "md",  t: "Boutique",     d: "10–49 seats · multiple PMs" },
  { id: "lg",  t: "Institutional", d: "50+ seats · multi-strategy" },
];

const FIRM_STYLES = [
  { id: "disc",    t: "Discretionary",        d: "Humans decide, quants assist" },
  { id: "systsys", t: "Systematic",            d: "Models decide, humans oversee" },
  { id: "hybrid",  t: "Hybrid",                d: "Both — depends on mandate" },
];

const ASSET_CLASSES = [
  { id: "eq",  t: "Equities",        d: "Long-only, L/S, market neutral" },
  { id: "fi",  t: "Fixed income",    d: "Rates, credit, macro" },
  { id: "fx",  t: "FX & commodities", d: "Spot, futures, cross-asset" },
  { id: "mac", t: "Macro",           d: "Multi-asset top-down" },
  { id: "cry", t: "Crypto",          d: "Digital assets, DeFi" },
  { id: "alt", t: "Alternatives",    d: "PE, real assets, structured" },
];

const ROLES = [
  {
    id: "admin",
    icon: "shield",
    t: "Admin",
    d: "Full control. Manage members, policies, data sources, billing. Cannot publish decisions without a PM approval (separation of duties).",
    perms: [
      { t: "manage team", ok: true },
      { t: "edit policies", ok: true },
      { t: "view all books", ok: true },
      { t: "audit log", ok: true },
      { t: "publish decisions", ok: false },
    ],
  },
  {
    id: "pm",
    icon: "target",
    t: "Portfolio manager",
    d: "Decides and publishes. Sees recommendations routed to your book, runs scenarios, approves trades within your policy limits.",
    perms: [
      { t: "publish decisions", ok: true },
      { t: "run scenarios", ok: true },
      { t: "view own book", ok: true },
      { t: "view other books", ok: false },
      { t: "edit policies", ok: false },
    ],
  },
  {
    id: "analyst",
    icon: "search",
    t: "Analyst / Quant",
    d: "Builds and validates. Designs models, runs backtests, proposes recommendations for PM review. Read-only on live book.",
    perms: [
      { t: "build models", ok: true },
      { t: "run backtests", ok: true },
      { t: "propose recs", ok: true },
      { t: "publish decisions", ok: false },
      { t: "edit policies", ok: false },
    ],
  },
  {
    id: "viewer",
    icon: "eye",
    t: "Viewer",
    d: "Read-only access. Sees recommendations, comparison, and portfolio health. No weights or expected-Δ exposed. Suitable for IR, compliance observers, junior staff.",
    perms: [
      { t: "view recs (masked)", ok: true },
      { t: "view portfolio health", ok: true },
      { t: "see weights / Δ", ok: false },
      { t: "run scenarios", ok: false },
      { t: "publish", ok: false },
    ],
  },
];

const PERM_ROWS = [
  { cat: "Decisions", action: "View recommendations", sub: "Active and historical", admin: "y", pm: "y", ana: "y", viewer: "lim" },
  { cat: "Decisions", action: "Propose new recommendation", sub: "For PM review", admin: "n", pm: "y", ana: "y", viewer: "n" },
  { cat: "Decisions", action: "Publish to live book", sub: "Sends to OMS", admin: "n", pm: "y", ana: "n", viewer: "n" },
  { cat: "Decisions", action: "Override policy", sub: "With justification log", admin: "n", pm: "y", ana: "n", viewer: "n" },
  { cat: "Analysis",  action: "Run scenarios", sub: "Counterfactuals", admin: "y", pm: "y", ana: "y", viewer: "n" },
  { cat: "Analysis",  action: "Run backtests", sub: "On proposed models", admin: "y", pm: "y", ana: "y", viewer: "n" },
  { cat: "Analysis",  action: "Edit model configs", sub: "Factors, weights", admin: "n", pm: "n", ana: "y", viewer: "n" },
  { cat: "Admin",     action: "Manage members & roles", sub: "Invite, revoke", admin: "y", pm: "n", ana: "n", viewer: "n" },
  { cat: "Admin",     action: "Edit global policies", sub: "Position limits, concentration", admin: "y", pm: "n", ana: "n", viewer: "n" },
  { cat: "Admin",     action: "Manage data sources", sub: "Add, pause, diagnose", admin: "y", pm: "n", ana: "n", viewer: "n" },
  { cat: "Admin",     action: "View audit log", sub: "Full tenant log", admin: "y", pm: "lim", ana: "lim", viewer: "n" },
];

const DEFAULT_INVITES = [
  { email: "hadar@rivkacap.com",    role: "pm" },
  { email: "noam@rivkacap.com",     role: "analyst" },
  { email: "shira@rivkacap.com",    role: "analyst" },
  { email: "",                       role: "pm" },
];

const TEAM_MEMBERS = [
  { name: "Rivka Shoval",   email: "rivka@rivkacap.com",   role: "admin",   av: "a1", init: "RS", status: "active",   last: "just now",    mfa: true },
  { name: "Hadar Levi",      email: "hadar@rivkacap.com",   role: "pm",      av: "a2", init: "HL", status: "active",   last: "2m ago",      mfa: true },
  { name: "Noam Katz",       email: "noam@rivkacap.com",    role: "ana",     av: "a3", init: "NK", status: "active",   last: "14m ago",     mfa: true },
  { name: "Shira Benari",    email: "shira@rivkacap.com",   role: "ana",     av: "a4", init: "SB", status: "pending",  last: "—",           mfa: false },
  { name: "Ido Rotem",       email: "ido@rivkacap.com",     role: "viewer",  av: "a5", init: "IR", status: "active",   last: "yesterday",   mfa: true },
  { name: "Tali Yaron",      email: "tali@rivkacap.com",    role: "pm",      av: "a6", init: "TY", status: "inactive", last: "12d ago",     mfa: true },
];

const ROLE_LABEL = { admin: "Admin", pm: "PM", ana: "Analyst", viewer: "Viewer" };

Object.assign(window, {
  OB_STEPS, FIRM_SIZES, FIRM_STYLES, ASSET_CLASSES, ROLES, PERM_ROWS,
  DEFAULT_INVITES, TEAM_MEMBERS, ROLE_LABEL,
});
