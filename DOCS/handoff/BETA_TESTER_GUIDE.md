# FINRLX Beta Tester Guide

Welcome. This is the closed beta of FINRLX, a decision-support tool for medium-term equity investing. You are one of a small group invited to try it before public release.

## What FINRLX is

A research environment that takes a universe of US equities, runs a quantitative pipeline over daily market data, and produces a single weight-centric **recommendation** with confidence scores and a full audit trail. You can replay the decision step-by-step, paper-trade against it, and review historical scans.

## What FINRLX is NOT

- **Not investment advice.** Nothing you see here is a recommendation to buy or sell any security tailored to your personal situation. Outputs are quantitative model results, not the opinion of a licensed advisor.
- **Not a broker.** We do not connect to your brokerage account. Paper trading only.
- **Not real-time.** Daily bars only, US equities only.

You will see this disclaimer in a modal on first visit and a footer banner on every page. Both are real legal guardrails, please read them.

## How to get in

1. Your email is added to the allowlist by the operator (Rotem).
2. You go to `https://<frontend-url>/signup`, enter the email you provided + a password (min 12 chars).
3. You accept the disclaimer.
4. The 4-step onboarding shows you the lay of the land: welcome → disclaimer → pick a universe → first recommendation.
5. From here, you have access to: Decision Workspace, Paper Portfolio, Replay, and the Decision Overview.

## The 6 surfaces you'll use

| Surface | What's there | What you can do |
|---|---|---|
| Overview | Today's snapshot of every published recommendation. | Click into the active recommendation to see Decision detail. |
| Decision Workspace | The current recommendation, broken down by stage (selection, allocation, timing, risk overlay). | Save as your current thesis, defer, or promote to paper. |
| Paper Portfolio | A synthetic portfolio that tracks recommendation weights against real market prices. | View drift vs. target, see PnL since promotion. |
| Replay | Historical recommendations replayed stage-by-stage. | Pick a past decision and see exactly what data + signals produced it. |
| Onboarding | First-visit walkthrough. | One-time. |
| Disclaimer / Terms / Privacy | Legal pages. | Read once; permanently linked from the footer. |

## What to look for and report back

You're our quality bar. Specifically:

- **Anything that reads like "advice".** If a label, button, or sentence makes it sound like FINRLX is telling YOU to buy something, that's a bug. Screenshot it.
- **Numbers that don't add up.** Weights that don't sum to ~1. Confidence scores that contradict the narrative. Drift values that move in the wrong direction.
- **Slow pages.** Anything that takes more than a couple of seconds to load is a bug, not a feature.
- **Confusing flows.** If you got lost, screenshot where + tell me which button you wanted to click.
- **Broken accessibility.** If your screen reader, dark-mode preference, or keyboard navigation is unhappy, flag it. (Known: some color contrast on the dark theme is being fixed.)

## How to report

Email the operator (your invite came from this address) with:

1. A one-line summary.
2. A screenshot if it's visual.
3. The URL and approximate time.
4. What you expected vs. what you saw.

There is no Linear or Jira during the beta. Email is the bug tracker.

## Privacy

We store your email + a hashed password + your in-app actions (paper trades, recommendation views). We do NOT store payment info, broker credentials, or government ID. Full details in `/privacy`.

If you want your account deleted, email the operator. We action requests within 30 days.

## What's coming

The beta is intentionally narrow. Coming after public launch — not part of the beta:
- Real broker integration (Alpaca / IBKR).
- Multi-asset class (today: US equities only).
- Real-time data.
- Mobile native app.

If any of those would change how useful this is to you, please tell us. The roadmap is set by what testers actually want.

## Thank you

You're using something that's two months old. Things will be rough. The trade-off you accepted is: you get to shape it.
