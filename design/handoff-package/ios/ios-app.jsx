// iOS canvas — present all screens side-by-side in DesignCanvas sections

const { useState: useStateIOSApp } = React;

function IOSApp() {
  const [dark, setDark] = useStateIOSApp(true);

  return (
    <>
      <DesignCanvas>
        <DCSection id="nav" title="Mobile navigation" subtitle="Tab bar, today hub, and key entry points.">
          <DCArtboard id="today-a" label="Today · A · card list" width={390} height={844}>
            <S_TodayA dark={dark}/>
          </DCArtboard>
          <DCArtboard id="today-b" label="Today · B · stack ranked" width={390} height={844}>
            <S_TodayB dark={dark}/>
          </DCArtboard>
          <DCArtboard id="alerts" label="Alerts inbox" width={390} height={844}>
            <S_Alerts dark={dark}/>
          </DCArtboard>
          <DCArtboard id="watchlist" label="Watchlist & views" width={390} height={844}>
            <S_Watchlist dark={dark}/>
          </DCArtboard>
          <DCArtboard id="settings" label="Settings · Me" width={390} height={844}>
            <S_Settings dark={dark}/>
          </DCArtboard>
        </DCSection>

        <DCSection id="decision" title="Decision workspace" subtitle="Two directions for reading and acting on a recommendation.">
          <DCArtboard id="dec-a" label="Decision · A · reading-first" width={390} height={844}>
            <S_DecisionA dark={dark}/>
          </DCArtboard>
          <DCArtboard id="dec-b" label="Decision · B · tabbed + bottom sheet" width={390} height={844}>
            <S_DecisionB dark={dark}/>
          </DCArtboard>
          <DCArtboard id="scenario" label="Scenario controls" width={390} height={844}>
            <S_Scenario dark={dark}/>
          </DCArtboard>
          <DCArtboard id="publish" label="Promote · Face ID sheet" width={390} height={844}>
            <S_Publish dark={dark}/>
          </DCArtboard>
        </DCSection>

        <DCSection id="analysis" title="Analysis & forensics" subtitle="Compare engines, replay history, annotate thesis.">
          <DCArtboard id="compare" label="Engine comparison" width={390} height={844}>
            <S_Compare dark={dark}/>
          </DCArtboard>
          <DCArtboard id="replay" label="Replay · time travel" width={390} height={844}>
            <S_Replay dark={dark}/>
          </DCArtboard>
          <DCArtboard id="notes" label="Notes & annotations" width={390} height={844}>
            <S_Notes dark={dark}/>
          </DCArtboard>
        </DCSection>

        <DCSection id="ipad" title="iPad · master-detail" subtitle="Decisions split view for deep review without the desktop.">
          <DCArtboard id="ipad-decision" label="iPad · Decisions split" width={1180} height={820}>
            <S_iPad dark={dark}/>
          </DCArtboard>
        </DCSection>
      </DesignCanvas>

      {/* Small theme toggle in corner */}
      <div style={{
        position:"fixed", top:14, right:14, zIndex:1000,
        background: dark? "#1c1c1e" : "#fff",
        color: dark? "#fff" : "#000",
        border: "0.5px solid rgba(0,0,0,0.1)",
        borderRadius: 999, padding: "6px 12px",
        fontSize: 12, fontWeight:500, cursor:"pointer",
        fontFamily:"-apple-system, system-ui",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
      }} onClick={()=>setDark(d=>!d)}>
        {dark? "☀ Light" : "☾ Dark"}
      </div>
    </>
  );
}

const iosRoot = ReactDOM.createRoot(document.getElementById("root"));
iosRoot.render(<IOSApp />);
