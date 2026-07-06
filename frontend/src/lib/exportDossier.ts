/**
 * LEAP S5 polish — dossier export (SIMPLE_MODE_SPEC §5b, binding).
 * Generates a self-contained offline HTML document from the dossier payload
 * (same philosophy as the /analyze reports: opens anywhere, no runtime).
 * MUST embed: full disclaimer strip, freshness stamp, and the tournament
 * scoreboard's penalty columns. Stance passes through the mapping boundary.
 */
import { toSimpleStance } from "@/lib/simpleStance";
import type { DossierPayload } from "@/components/simple/DossierView";

function esc(s: unknown): string {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string,
  );
}

export function dossierToHtml(d: DossierPayload): string {
  const t = d.sections.model_insight;
  const rows = t.candidates
    .map(
      (c) => `<tr><td>${esc(c.name)}</td><td>${c.kind === "ml" ? "machine-learning" : "rule-based"}</td>` +
        `<td>${c.train_sharpe.toFixed(2)}</td><td>${c.val_sharpe.toFixed(2)}</td>` +
        `<td>${c.divergence.toFixed(2)}</td><td>${c.penalty.toFixed(2)}</td><td>${c.score.toFixed(2)}</td></tr>`,
    )
    .join("");
  const news = d.sections.news_sentiment.items_7d
    .slice(0, 6)
    .map(
      (n) => `<li>${esc(n.title)} <em>(${esc(n.sentiment)})</em>` +
        (n.why_this_matters ? `<br><small>Why it matters: ${esc(n.why_this_matters)}</small>` : "") +
        `</li>`,
    )
    .join("");
  const features = Object.entries(d.sections.technical.features)
    .map(([k, v]) => `<tr><td>${esc(k)}</td><td>${typeof v === "number" ? v.toFixed(4) : "—"}</td></tr>`)
    .join("");
  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>${esc(d.ticker)} research dossier — FINRLX</title>
<style>body{font:14px/1.5 system-ui;margin:24px;color:#20242c;max-width:760px}
table{border-collapse:collapse;width:100%;margin:8px 0}td,th{border:1px solid #d9dde3;padding:4px 8px;text-align:left}
h1{font-size:20px}h2{font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#5a616c}
footer{border-top:1px solid #d9dde3;margin-top:16px;padding-top:8px;color:#5a616c;font-size:12px}</style></head><body>
<h1>${esc(d.ticker)} — research dossier</h1>
<p>Research stance: <strong>${esc(toSimpleStance(d.summary.stance))}</strong> ·
Regime: ${esc(d.summary.regime)} (rule-based research overlay, not a prediction) ·
Data through <strong>${esc(d.freshness.latest_bar)}</strong> · Generated ${esc(d.generated_at)}</p>
<h2>Model insight</h2>
<p>${t.winner ? `${esc(t.winner.name)} — validation score ${t.winner.score}, chosen over ${t.candidates.length} candidates after walk-forward validation with overfitting penalties.` : esc(t.rationale ?? "The tournament needs more history to validate candidates honestly.")}</p>
<table><tr><th>Candidate</th><th>Kind</th><th>Train Sharpe</th><th>Validation Sharpe</th><th>Divergence</th><th>Penalty</th><th>Score</th></tr>${rows}</table>
<p><small>Reinforcement-learning candidates: ${esc(t.rl?.note ?? t.rl?.status ?? "")}</small></p>
<h2>Technical signals</h2><table>${features}</table>
<h2>News (7 days)</h2><ul>${news || "<li>No items in the window.</li>"}</ul>
<footer>${d.disclaimers.map((x) => `<p>${esc(x)}</p>`).join("")}
<p>Data through ${esc(d.freshness.latest_bar)} · Model chosen by walk-forward tournament — penalties included in the scoreboard above.</p></footer>
</body></html>`;
}

export function downloadDossierHtml(d: DossierPayload): void {
  const blob = new Blob([dossierToHtml(d)], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${d.ticker}-dossier-${d.freshness.latest_bar}.html`;
  a.click();
  URL.revokeObjectURL(url);
}
