# QuantPipeline — Handoff Package

> חבילת המסירה ל‑Claude Code. כוללת את כל המסכים, ה‑tokens, וה‑components שנבנו עד כה.

---

## מה יש בחבילה

### 📄 מסמכי handoff
| קובץ | מטרה |
|---|---|
| `INDEX.md` | המסמך הזה — מפת הקבצים והיכן להתחיל |
| `HANDOFF.md` | מסמך ההעברה המלא — UX principles, IA, stack, type definitions, mapping ל‑SwiftUI/React |

### 🌐 Web (4 workspaces)
| מסך | HTML entry | קובצי JSX | קובצי CSS |
|---|---|---|---|
| **Overview** — morning triage | `Overview.html` | `overview-app.jsx`, `overview.jsx` | `styles.css`, `overview.css` |
| **Decision Workspace** — recommendation hero, evidence, scenario, disagreement | `Decision Workspace.html` | `app.jsx`, `shell.jsx`, `hero.jsx`, `modules.jsx`, `chart.jsx`, `scenario.jsx`, `context.jsx` | `styles.css` |
| **Engine Comparison** — matrix, alignment, methodology | `Engine Comparison.html` | `compare-app.jsx`, `comparison.jsx` | `styles.css` |
| **Ops Command Center** — queue, feeds, engines, breaches, incidents, audit | `Ops.html` | `ops-app.jsx`, `ops.jsx` | `styles.css`, `ops.css` |

**משותף לכל מסכי ה‑web:**
- `styles.css` — design tokens (light + dark), typography, components, layout primitives
- `icons.jsx` — inline SVG icon set (~40 icons)
- `tweaks-panel.jsx` — runtime tweak controls (**prototype‑only**, אל תעבירו לפרודקשן)

### 📱 iOS (12 מסכים + iPad)
| Entry | תיקייה |
|---|---|
| `iOS App.html` | design canvas wrapper |
| `ios/` | `ios-shared.jsx` (tokens, IOSPhone, IOSNav, IOSTabBar) + `screens-*.jsx` per group + `screen-ipad.jsx` |

**Groups בקנבס:**
- Mobile navigation: Today A · Today B · Alerts · Watchlist · Settings
- Decision workspace: Decision A (reading‑first) · Decision B (tabbed + bottom sheet) · Scenario · Publish (Face ID)
- Analysis & forensics: Engine comparison · Replay · Notes
- iPad: split view (sidebar + list + detail)

---

## איך להתחיל (Claude Code)

1. **קרא קודם את `HANDOFF.md`** — הוא מסביר את ה‑UX principles, ה‑IA, ה‑stack, וטבלאות mapping ל‑Tailwind ול‑SwiftUI.
2. **פתח את 4 קבצי ה‑HTML** ב‑browser כדי לראות את הדיזיין החי. כולם self‑contained — צריך רק את הקבצים בתיקייה הזו.
3. **`styles.css` הוא המקור היחיד לאמת על tokens.** העתק את ה‑CSS variables מתוך `:root` ו‑`[data-theme="dark"]` ל‑`theme.extend.colors` של Tailwind.
4. **רכיבים קריטיים לפורט (Tier 1):** RecommendationCard, ConfidenceBlock (trio: model · data · ops), AlertSystem, QueueItem, ComparisonTable, AppShell.
5. **iOS:** `ios/ios-shared.jsx` הוא ה‑equivalent של design system — כל המסכים בונים מ‑IOSPhone + IOSNav + IOSTabBar.

---

## מה **לא** בחבילה (ידוע)

יש 4 פריטים שעוד לא נבנו, לפי סדר חשיבות:

1. **Design System project נפרד** — tokens, type sheet, icon gallery, motion demo, כל ה‑states לכל component
2. **Empty / loading / error / degraded states pass** — יש כמה skeletons בקיים, אבל לא מקיף
3. **Replay (web), Backtests, Paper portfolio, Universe browser, Policy editor** — workspaces נוספים מה‑IA
4. **Onboarding, sign‑in, permissions, team management** — flows של חיבור ראשוני

---

## גרסה
חבילה זו תואמת את מצב הפרויקט נכון ל‑handoff הראשון.
