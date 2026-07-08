// Onboarding — app composer
const { useState: useStateObApp, useEffect: useEffectObApp } = React;

const TWEAK_DEFAULTS_OB = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "startStep": "signin",
  "showTeamManagement": false
}/*EDITMODE-END*/;

function OnboardingApp() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS_OB);
  const [step, setStep] = useStateObApp(tweaks.startStep);
  const [data, setData] = useStateObApp({
    firmName: "Rivka Capital",
    domain: "rivkacap.com",
    tz: "Asia/Jerusalem",
    size: "md",
    style: "hybrid",
    assets: ["eq", "mac"],
    role: "admin",
    invites: DEFAULT_INVITES,
  });

  useEffectObApp(() => {
    document.documentElement.setAttribute("data-theme", tweaks.theme);
  }, [tweaks.theme]);

  const goTo = (id) => { setStep(id); setTweak("startStep", id); };

  if (tweaks.showTeamManagement) {
    return (
      <div className="ob-shell" data-screen-label="08 Team management">
        <ObTopBar active="done" />
        <div className="ob-body">
          <TeamManagement />
        </div>
        <TweaksPanel title="Tweaks">
          <TweakSection label="Flow" />
          <TweakRadio label="View" value={"team"}
            options={["onboarding","team"]}
            onChange={v => setTweak("showTeamManagement", v === "team")} />
          <TweakSection label="Appearance" />
          <TweakRadio label="Theme" value={tweaks.theme}
            options={["light","dark"]}
            onChange={v => setTweak("theme", v)} />
        </TweaksPanel>
      </div>
    );
  }

  const goNext = () => {
    const order = ["signin","org","roles","team","review","done"];
    const i = order.indexOf(step);
    if (i < order.length - 1) goTo(order[i + 1]);
  };
  const goBack = () => {
    const order = ["signin","org","roles","team","review","done"];
    const i = order.indexOf(step);
    if (i > 0) goTo(order[i - 1]);
  };

  return (
    <div className="ob-shell" data-screen-label={"08 Onboarding · " + step}>
      <ObTopBar active={step === "done" ? OB_STEPS[OB_STEPS.length - 1].id : step} />
      <div className="ob-body">
        {step === "signin" && <StepSignIn onNext={goNext} />}
        {step === "org"    && <StepOrg data={data} setData={setData} onBack={goBack} onNext={goNext} />}
        {step === "roles"  && <StepRoles data={data} setData={setData} onBack={goBack} onNext={goNext} />}
        {step === "team"   && <StepInvites data={data} setData={setData} onBack={goBack} onNext={goNext} />}
        {step === "review" && <StepReview data={data} goToStep={goTo} onBack={goBack} onNext={goNext} />}
        {step === "done"   && <StepDone firmName={data.firmName} onDone={() => setTweak("showTeamManagement", true)} />}
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Flow" />
        <TweakSelect label="Jump to step" value={step}
          options={[
            {value:"signin", label:"1 · Sign in"},
            {value:"org", label:"2 · Firm"},
            {value:"roles", label:"3 · Role"},
            {value:"team", label:"4 · Invite"},
            {value:"review", label:"5 · Review"},
            {value:"done", label:"6 · Done"},
          ]}
          onChange={v => goTo(v)} />
        <TweakButton label="View team management" onClick={() => setTweak("showTeamManagement", true)} />
        <TweakSection label="Appearance" />
        <TweakRadio label="Theme" value={tweaks.theme}
          options={["light","dark"]}
          onChange={v => setTweak("theme", v)} />
      </TweaksPanel>
    </div>
  );
}

const obRoot = ReactDOM.createRoot(document.getElementById("root"));
obRoot.render(<OnboardingApp />);
