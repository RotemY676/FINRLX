// iOS shared — tokens, icons, chrome helpers for QuantPipeline mobile.
// Tailored to iOS 17 HIG — SF Pro, 17pt body, grouped lists, blur bars.

const IOS = {
  // Apple-system colors (light/dark)
  light: {
    bg: "#F2F2F7", surface: "#FFFFFF", surface2: "#F9F9FB", surface3: "#EDEDF2",
    ink: "#000000", ink2: "rgba(60,60,67,0.85)", ink3: "rgba(60,60,67,0.60)",
    ink4: "rgba(60,60,67,0.30)", sep: "rgba(60,60,67,0.12)",
    blue: "#0A84FF", green: "#30D158", red: "#FF453A", orange: "#FF9F0A",
    indigo: "#5E5CE6", teal: "#64D2FF", mint: "#63E6E2",
    tint: "#0A84FF",
  },
  dark: {
    bg: "#000000", surface: "#1C1C1E", surface2: "#2C2C2E", surface3: "#3A3A3C",
    ink: "#FFFFFF", ink2: "rgba(235,235,245,0.85)", ink3: "rgba(235,235,245,0.60)",
    ink4: "rgba(235,235,245,0.30)", sep: "rgba(84,84,88,0.50)",
    blue: "#0A84FF", green: "#32D74B", red: "#FF453A", orange: "#FF9F0A",
    indigo: "#7D7AFF", teal: "#40CBE0", mint: "#63E6E2",
    tint: "#0A84FF",
  },
  font: '-apple-system, "SF Pro Text", system-ui, sans-serif',
  fontDisplay: '-apple-system, "SF Pro Display", system-ui, sans-serif',
  fontMono: '"SF Mono", ui-monospace, monospace',
};

function useIOS(dark) {
  return dark ? IOS.dark : IOS.light;
}

// Tabbar — bottom nav
function IOSTabBar({ tabs, active, dark }) {
  const t = useIOS(dark);
  return (
    <div style={{
      position: "absolute", bottom: 0, left: 0, right: 0,
      paddingBottom: 22, paddingTop: 6,
      background: dark ? "rgba(20,20,22,0.82)" : "rgba(249,249,251,0.82)",
      backdropFilter: "saturate(180%) blur(20px)",
      WebkitBackdropFilter: "saturate(180%) blur(20px)",
      borderTop: `0.5px solid ${t.sep}`,
      display: "flex", zIndex: 40,
    }}>
      {tabs.map((tab, i) => (
        <div key={i} style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", gap: 3, padding: "6px 0",
          color: active === i ? t.blue : t.ink3,
        }}>
          {tab.icon}
          <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: 0.1 }}>
            {tab.label}
          </span>
          {tab.badge && (
            <span style={{
              position: "absolute", top: 4, marginLeft: 18,
              background: t.red, color: "#fff", fontSize: 10,
              fontWeight: 700, padding: "1px 5px", borderRadius: 9,
              minWidth: 16, textAlign: "center",
            }}>{tab.badge}</span>
          )}
        </div>
      ))}
    </div>
  );
}

// SF-style icons (minimal set we need)
const SF = {
  house: (c="#000", w=26) => (
    <svg width={w} height={w} viewBox="0 0 26 26" fill="none">
      <path d="M4 11L13 3l9 8v11a1 1 0 01-1 1h-5v-7h-6v7H5a1 1 0 01-1-1V11z"
        stroke={c} strokeWidth="1.8" strokeLinejoin="round"/>
    </svg>
  ),
  decisions: (c="#000", w=26) => (
    <svg width={w} height={w} viewBox="0 0 26 26" fill="none">
      <rect x="3" y="5" width="20" height="16" rx="3" stroke={c} strokeWidth="1.8"/>
      <path d="M7 10h8M7 14h12M7 18h6" stroke={c} strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  bell: (c="#000", w=26) => (
    <svg width={w} height={w} viewBox="0 0 26 26" fill="none">
      <path d="M13 3a7 7 0 00-7 7v5l-2 3h18l-2-3v-5a7 7 0 00-7-7zM10 20a3 3 0 006 0"
        stroke={c} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round"/>
    </svg>
  ),
  person: (c="#000", w=26) => (
    <svg width={w} height={w} viewBox="0 0 26 26" fill="none">
      <circle cx="13" cy="9" r="4.5" stroke={c} strokeWidth="1.8"/>
      <path d="M4 22c1.5-4.5 5-6.5 9-6.5s7.5 2 9 6.5" stroke={c} strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  compare: (c="#000", w=26) => (
    <svg width={w} height={w} viewBox="0 0 26 26" fill="none">
      <path d="M9 4v18M17 4v18" stroke={c} strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M4 8l5-4 5 4M21 18l-5 4-5-4" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  chev: (c="rgba(60,60,67,0.3)", dir="right") => (
    <svg width="8" height="14" viewBox="0 0 8 14">
      <path d={dir==="right"?"M1 1l6 6-6 6":"M7 1L1 7l6 6"} stroke={c} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  xmark: (c="#000") => (
    <svg width="18" height="18" viewBox="0 0 18 18">
      <path d="M3 3l12 12M15 3L3 15" stroke={c} strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  check: (c="#fff") => (
    <svg width="16" height="16" viewBox="0 0 16 16">
      <path d="M3 8.5L6.5 12 13 4.5" stroke={c} strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  arrowUp: (c="#30D158") => (
    <svg width="14" height="14" viewBox="0 0 14 14">
      <path d="M7 12V2M3 6l4-4 4 4" stroke={c} strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  arrowDown: (c="#FF453A") => (
    <svg width="14" height="14" viewBox="0 0 14 14">
      <path d="M7 2v10M3 8l4 4 4-4" stroke={c} strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  dash: (c="#8e8e93") => (
    <svg width="14" height="14" viewBox="0 0 14 14">
      <path d="M2 7h10" stroke={c} strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  plus: (c="#0A84FF") => (
    <svg width="20" height="20" viewBox="0 0 20 20">
      <path d="M10 4v12M4 10h12" stroke={c} strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  filter: (c="#0A84FF") => (
    <svg width="20" height="20" viewBox="0 0 20 20">
      <path d="M3 5h14M5 10h10M8 15h4" stroke={c} strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  ellipsis: (c="rgba(60,60,67,0.6)") => (
    <svg width="22" height="6" viewBox="0 0 22 6">
      <circle cx="3" cy="3" r="2.5" fill={c}/>
      <circle cx="11" cy="3" r="2.5" fill={c}/>
      <circle cx="19" cy="3" r="2.5" fill={c}/>
    </svg>
  ),
  warning: (c="#FF9F0A", w=18) => (
    <svg width={w} height={w} viewBox="0 0 18 18" fill="none">
      <path d="M9 2l8 14H1L9 2z" fill={c}/>
      <path d="M9 7v4M9 13v.5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  breach: (c="#FF453A", w=18) => (
    <svg width={w} height={w} viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="8" fill={c}/>
      <path d="M9 4.5v5M9 12.5v.5" stroke="#fff" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  fresh: (c="#30D158", w=18) => (
    <svg width={w} height={w} viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="8" fill={c}/>
      <path d="M5 9.5L8 12l5-6" stroke="#fff" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
};

// Status bar (copied mini version)
function IOSStatus({ dark }) {
  const c = dark ? "#fff" : "#000";
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "16px 26px 6px", position: "relative", zIndex: 20,
      fontFamily: IOS.font, fontWeight: 600, fontSize: 15, color: c,
    }}>
      <span>9:41</span>
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <svg width="16" height="10" viewBox="0 0 16 10">
          <rect x="0" y="6" width="2.5" height="4" rx="0.5" fill={c}/>
          <rect x="4" y="4" width="2.5" height="6" rx="0.5" fill={c}/>
          <rect x="8" y="2" width="2.5" height="8" rx="0.5" fill={c}/>
          <rect x="12" y="0" width="2.5" height="10" rx="0.5" fill={c}/>
        </svg>
        <svg width="22" height="11" viewBox="0 0 22 11">
          <rect x="0.5" y="0.5" width="19" height="10" rx="2.5" stroke={c} strokeOpacity="0.4" fill="none"/>
          <rect x="2" y="2" width="16" height="7" rx="1.5" fill={c}/>
        </svg>
      </div>
    </div>
  );
}

// Phone frame (bezel)
function IOSPhone({ children, dark, w = 390, h = 844, label }) {
  const t = useIOS(dark);
  return (
    <div data-screen-label={label} style={{
      width: w, height: h, borderRadius: 52, position: "relative",
      background: t.bg, overflow: "hidden",
      fontFamily: IOS.font, color: t.ink,
      boxShadow: "0 1px 0 rgba(255,255,255,0.08) inset, 0 0 0 2px rgba(0,0,0,0.08), 0 40px 80px rgba(0,0,0,0.22)",
    }}>
      {/* dynamic island */}
      <div style={{
        position: "absolute", top: 11, left: "50%", transform: "translateX(-50%)",
        width: 120, height: 34, borderRadius: 20, background: "#000", zIndex: 50,
      }} />
      <IOSStatus dark={dark}/>
      {children}
      {/* home indicator */}
      <div style={{
        position: "absolute", bottom: 8, left: 0, right: 0, zIndex: 60,
        display: "flex", justifyContent: "center", pointerEvents: "none",
      }}>
        <div style={{
          width: 135, height: 5, borderRadius: 100,
          background: dark ? "rgba(255,255,255,0.7)" : "rgba(0,0,0,0.28)",
        }}/>
      </div>
    </div>
  );
}

// Nav bar (compact + large title)
function IOSNav({ title, back, trailing, dark, large = true, subtitle }) {
  const t = useIOS(dark);
  return (
    <div style={{ paddingTop: 4, position: "relative", zIndex: 5 }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "2px 16px 8px", minHeight: 32,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 4, color: t.blue, fontSize: 17, fontWeight: 400 }}>
          {back && <>{SF.chev(t.blue, "left")}<span>{back}</span></>}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {trailing}
        </div>
      </div>
      {large && (
        <div style={{ padding: "4px 16px 8px" }}>
          <div style={{
            fontFamily: IOS.fontDisplay, fontSize: 34, fontWeight: 700,
            letterSpacing: 0.37, color: t.ink, lineHeight: 1.1,
          }}>{title}</div>
          {subtitle && (
            <div style={{ fontSize: 13, color: t.ink3, marginTop: 4 }}>{subtitle}</div>
          )}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { IOS, useIOS, IOSTabBar, SF, IOSStatus, IOSPhone, IOSNav });
