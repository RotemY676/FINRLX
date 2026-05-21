# Phase W-6 — Wizard A11y & Mobile Sweep

**Date:** 2026-05-21
**Base commit:** `005c512` (W-5)
**Track:** Phase W — sub-phase 6 of 8.

## What this sub-phase ships

Cross-viewport accessibility verification for the W-3 wizard.

| Artifact | Path |
|---|---|
| Mobile Playwright spec (3 viewports) | `frontend/tests/e2e/onboarding-mobile.spec.ts` |

The wizard chrome was already mobile-tuned in W-3 (44px touch targets,
fluid card width, accent-color focus rings). This sub-phase verifies it
empirically at three viewports.

## Verification matrix

| Viewport | Device class | Axe result |
|---|---|---|
| 375 × 667 | iPhone SE | 0 serious / 0 critical |
| 768 × 1024 | iPad portrait | 0 serious / 0 critical |
| 1280 × 720 | desktop | 0 serious / 0 critical |

Axe runs against `wcag2a + wcag2aa + wcag21a + wcag21aa` tag bundle, the
same configuration used by the rest of the UX track.

Wizard `progressbar` ARIA role is asserted visible on the
non-redirect path, so the role contract from W-3 stays in force.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest | 839 (unchanged from W-5) |
| Frontend vitest | 27 (unchanged from W-3) |
| Frontend tsc | clean |
| Playwright chromium | **31 passed** (was 28; +3 new) |
| Touch-target lint | green |

## Follow-ups

* **W-7** edit page will reuse the same components and inherit the W-6
  axe baseline. Re-running the same Playwright spec against `/profile`
  in W-7 gives free regression coverage.
* If the wizard ever grows screen-reader-only hints (sr-only span), add
  a tailwind class or inline visually-hidden style — current text is
  visible by design, so we don't need it yet.

## Honest limitations

* The spec stubs all `**/api/v1/**` to 503, so the wizard either renders
  its loading fallback or bounces to /login. We never traverse the
  populated step-1..step-8 flow under Playwright until W-8 wires real
  signup + question fetch. That means axe is verifying the chrome
  (progressbar, card, footer nav, welcome content) but **not** the
  per-question fieldset/legend pairs at runtime.
* Adding a fixture that pre-seeds the test DB with profile_questions
  and runs the wizard end-to-end is exactly the W-8 work.

## Sources

* WCAG 2.2 — radio-group + fieldset/legend pattern.
* Axe-core 4.x rule index (used by Playwright integration).
