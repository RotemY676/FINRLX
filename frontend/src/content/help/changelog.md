---
title: Changelog
summary: What changed and when, newest first.
diataxis: reference
area: changelog
updated: 2026-05-22
---

What changed and when, newest first. Entries follow the [Keep a Changelog](https://keepachangelog.com/) convention with the tags **Added**, **Changed**, **Fixed**, **Deprecated**, and **Removed**.

## 2026.05 — Help center launch

**Added**

- A complete in-app Help center at [`/help`](/help). Authored in MDX, served by Next.js, ~50 pages across Getting started, Concepts, Guides, Reference, Glossary, FAQ, Troubleshooting, Changelog, and Disclaimers.
- The global Help (`?`) button in the top bar of every page links to the Help center.
- Contextual `?` glyphs deep-link from in-app screens — Policies, Decision, Home, Universe, Backtests, Risk, Replay, Comparison — into the matching help page.
- Numbered-callout screenshots on six high-traffic reference pages (Home, Decision, Policies, Universe, Backtests, Replay), captured against the live deploy with a 25-second post-networkidle wait so charts and animations are fully settled.
- A search bar on the Help landing page covering every help page's title, summary, and body text.
- A Playwright-based screenshot pipeline (`npm run help:shots`) that re-captures the screenshot set against the live deploy, for ongoing maintenance.

## 2026.05 — Onboarding wizard (WIZ-1/2/3)

**Added**

- An eight-step welcome wizard at `/onboarding` that collects knowledge, financial, risk, objectives, universe, and operational preferences. Defaults flow from the wizard into the workspace.
- A "Re-run the wizard" button on the [Profile page](/help/reference/pages/profile) so you can update your defaults at any time. See [Re-run the welcome wizard](/help/guides/re-run-the-wizard).
- WIZ-2: Users without a complete profile are routed to `/onboarding` after sign-in.
- WIZ-1: The profile questions catalog seeds automatically on first server boot.

## 2026.05 — Home command center (HOME-1)

**Changed**

- The home page is now the **Decision Command Center**, replacing the previous greeting + next-actions overview. The new screen answers "what changed, what needs review, what evidence supports it, what is stale, shadow-only, or blocked" at a glance. See [Reading the dashboard](/help/getting-started/reading-the-dashboard).

## See also

- [Help center landing](/help) — start here if you are new.
- [FAQ](/help/faq) — common questions answered.
