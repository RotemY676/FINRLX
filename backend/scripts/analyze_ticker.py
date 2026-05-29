"""End-to-end single-ticker analysis runner (CLI wrapper).

This script is a thin shell around `app.services.single_ticker_analysis`:
the analytical pipeline + HTML report builder live there so the same code
backs both this CLI and the GET /api/v1/analysis/single-ticker endpoint.

Usage:
  cd backend
  python scripts/analyze_ticker.py UMC
  python scripts/analyze_ticker.py UMC --out reports/umc.json
  python scripts/analyze_ticker.py UMC --history-days 730 --backtest-days 730
  python scripts/analyze_ticker.py UMC --no-open
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

# Force UTF-8 stdout — Windows consoles default to cp1252 which mangles
# smart quotes and other glyphs in news titles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# Make the script runnable as `python scripts/analyze_ticker.py UMC` from
# the backend/ dir.
_THIS = Path(__file__).resolve()
_BACKEND = _THIS.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.single_ticker_analysis import (  # noqa: E402
    MAX_POSITION_WEIGHT,
    AnalysisResult,
    run_full_analysis,
)


# ── Terminal report ──────────────────────────────────────────────────────────

def _fmt_pct(v: float | None, digits: int = 2) -> str:
    return f"{v * 100:+.{digits}f}%" if v is not None else "n/a"


def _fmt_num(v: float | None, digits: int = 2) -> str:
    return f"{v:.{digits}f}" if v is not None else "n/a"


def print_report(result: AnalysisResult) -> None:
    bar = "=" * 78
    sub = "-" * 78
    r = result

    print(bar)
    print(f"  FINRLX SINGLE-TICKER ANALYSIS  --  {r.ticker}")
    print(f"  As-of: {r.bars.latest_date}  |  Last close: ${_fmt_num(r.bars.latest_close)}  |  "
          f"Bars: {len(r.bars.dates)}  |  Generated: {datetime.now(UTC).isoformat(timespec='seconds')}")
    print(bar)

    print("\n[1] FEATURES (FINRLX feature layer)")
    print(sub)
    feat_rows = [
        ("5d return",          r.features["return_5d"],            "pct"),
        ("20d return",         r.features["return_20d"],           "pct"),
        ("60d return",         r.features["return_60d"],           "pct"),
        ("20d volatility ann", r.features["volatility_20d"],       "pct"),
        ("20d max drawdown",   r.features["drawdown_20d"],         "pct"),
        ("20d rel volume",     r.features["relative_volume_20d"],  "ratio"),
        ("7d news sentiment",  r.features["news_sentiment_7d"],    "score"),
        ("7d news count",      r.features["news_count_7d"],        "int"),
    ]
    for label, (val, qual), kind in feat_rows:
        if val is None:
            text = f"n/a ({qual})"
        elif kind == "pct":
            text = _fmt_pct(val)
        elif kind == "int":
            text = f"{int(val)}"
        else:
            text = _fmt_num(val, 3)
        print(f"  {label:<22} {text}")

    print("\n[2] FINRLX ENGINE ENSEMBLE (production scoring layer)")
    print(sub)
    for key, out in r.engine_outputs.items():
        print(f"  {key:<22} score={_fmt_num(out['score'])}  conf={_fmt_num(out['confidence'])}  "
              f"stance={out['stance']:<5}  risk={out['risk_level']}")
        for d in out.get("drivers", [])[:3]:
            print(f"    + {d}")
        for c in out.get("caveats", [])[:3]:
            print(f"    ! {c}")

    print("\n[3] WEIGHT-CENTRIC RECOMMENDATION (composite)")
    print(sub)
    c = r.composite
    print(f"  Composite score:     {_fmt_num(c['composite_score'])}  (range -1.00 .. +1.00)")
    print(f"  Avg engine conf:     {_fmt_num(c['avg_confidence'])}")
    print(f"  Stance:              {c['stance'].upper()}")
    print(f"  Suggested weight:    {_fmt_pct(c['target_weight'], digits=2)} of portfolio "
          f"(cap {int(MAX_POSITION_WEIGHT * 100)}% per asset)")
    if c["drivers"]:
        print("  Drivers:")
        for d in c["drivers"]:
            print(f"    + {d}")
    if c["caveats"]:
        print("  Caveats:")
        for cv in c["caveats"]:
            print(f"    ! {cv}")

    print("\n[4] NEWS & SENTIMENT (ticker-specific, last 7d highlighted)")
    print(sub)
    if not r.news_items:
        print("  (no ticker news returned by yfinance)")
    else:
        sent_avg = (sum(n.sentiment_compound for n in r.news_7d) / len(r.news_7d)) if r.news_7d else None
        print(f"  Items total / last 7d: {len(r.news_items)} / {len(r.news_7d)}     "
              f"Avg compound (7d): {_fmt_num(sent_avg, 3) if sent_avg is not None else 'n/a'}")
        print()
        for n in r.news_items[:8]:
            print(f"  [{n.sentiment_label:<8} {n.sentiment_compound:+.2f}] {n.title[:90]}")
            print(f"      {n.publisher} | {n.published or 'undated'}")

    print("\n[5] STRATEGY COMPARISON (walk-forward weekly, cost 10 bps)")
    print(sub)
    print(f"  Window:              {r.backtest_start.isoformat()} .. {r.bars.latest_date}")
    print(f"  Strategies tested:   {len(r.strategy_results)} main + {len(r.sweep_results)} threshold sweep")
    print()
    print(f"  {'strategy':<26}{'total':>10}{'ann':>10}{'maxDD':>10}{'Sharpe':>8}{'long%':>8}{'trades':>8}")
    print(f"  {sub[:78]}")
    sortable = [s for s in r.strategy_results if s["key"] != "buy_hold"]
    sortable.sort(key=lambda s: s["metrics"].get("sharpe_ratio") or -999, reverse=True)
    bh = next((s for s in r.strategy_results if s["key"] == "buy_hold"), None)
    for s in sortable + ([bh] if bh else []):
        m = s["metrics"]
        print(
            f"  {s['name']:<26}"
            f"{_fmt_pct(m.get('total_return'), 1):>10}"
            f"{_fmt_pct(m.get('annualized_return'), 1):>10}"
            f"{_fmt_pct(m.get('max_drawdown'), 1):>10}"
            f"{_fmt_num(m.get('sharpe_ratio')):>8}"
            f"{_fmt_pct(m.get('long_share'), 0):>8}"
            f"{m.get('trades', 0):>8}"
        )

    print()
    print("  Composite threshold sweep (gate sensitivity):")
    print(f"  {'threshold':<26}{'total':>10}{'ann':>10}{'maxDD':>10}{'Sharpe':>8}{'long%':>8}{'trades':>8}")
    print(f"  {sub[:78]}")
    for s in r.sweep_results:
        m = s["metrics"]
        print(
            f"  {s['name']:<26}"
            f"{_fmt_pct(m.get('total_return'), 1):>10}"
            f"{_fmt_pct(m.get('annualized_return'), 1):>10}"
            f"{_fmt_pct(m.get('max_drawdown'), 1):>10}"
            f"{_fmt_num(m.get('sharpe_ratio')):>8}"
            f"{_fmt_pct(m.get('long_share'), 0):>8}"
            f"{m.get('trades', 0):>8}"
        )

    print("\n[6] SUMMARY")
    print(sub)
    main_strat = next((s for s in r.strategy_results if s["key"] == "composite_010"), None)
    bh_ret = bh["metrics"].get("total_return") if bh else None
    main_ret = main_strat["metrics"].get("total_return") if main_strat else None
    alpha = (main_ret - bh_ret) if main_ret is not None and bh_ret is not None else None
    best = max(r.strategy_results, key=lambda s: s["metrics"].get("sharpe_ratio") or -999)
    print(f"  Current stance:      {c['stance'].upper()}  (composite {_fmt_num(c['composite_score'])}, "
          f"target weight {_fmt_pct(c['target_weight'])})")
    print(f"  Best Sharpe:         {best['name']} -> Sharpe {_fmt_num(best['metrics'].get('sharpe_ratio'))}, "
          f"total {_fmt_pct(best['metrics'].get('total_return'))}")
    print(f"  Composite vs B&H:    {_fmt_pct(alpha) if alpha is not None else 'n/a'} alpha over window")
    print(f"  Note: All strategies are deterministic baselines run on the same data. The")
    print(f"        FinRL-X RL trainer (rl_adapter.py) is research/offline-only - no")
    print(f"        trained policies exist in this repo, so none are included in this")
    print(f"        comparison. The recommendation above comes from the live engine ensemble.")
    print(bar)


# ── Server detection + browser opening ───────────────────────────────────────

def _url_alive(url: str, timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def _open_in_browser(url_or_path: str) -> bool:
    try:
        webbrowser.open(url_or_path, new=2)
        return True
    except Exception:
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="FINRLX single-ticker analysis runner.")
    ap.add_argument("ticker", help="Ticker symbol, e.g. UMC")
    ap.add_argument("--history-days", type=int, default=400,
                    help="Days of OHLCV history to fetch (default: 400)")
    ap.add_argument("--backtest-days", type=int, default=365,
                    help="Days the walk-forward backtest covers (default: 365)")
    ap.add_argument("--out", type=str, default=None,
                    help="Optional path to write a JSON dump of the full result")
    ap.add_argument("--no-open", action="store_true",
                    help="Skip writing/opening the HTML report and the FINRLX research page")
    ap.add_argument("--frontend-url", default="http://localhost:3000",
                    help="FINRLX frontend base URL (default: http://localhost:3000)")
    ap.add_argument("--backend-url", default="http://localhost:8000",
                    help="FINRLX backend base URL (default: http://localhost:8000)")
    args = ap.parse_args()

    ticker = args.ticker.upper().strip()
    if not ticker:
        sys.exit("ERROR: ticker required")

    print(f"[fetch] {ticker} history + news ...")
    try:
        result = run_full_analysis(
            ticker,
            history_days=args.history_days,
            backtest_days=args.backtest_days,
        )
    except RuntimeError as e:
        sys.exit(f"ERROR: {e}")
    print(f"[fetch] {len(result.bars.dates)} bars, "
          f"{len(result.news_items)} news items, "
          f"{len(result.strategy_results)} strategies done")
    print()

    print_report(result)

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ticker": result.ticker,
            "as_of": result.bars.latest_date.isoformat() if result.bars.latest_date else None,
            "latest_close": result.bars.latest_close,
            "features": {k: {"value": v[0], "quality": v[1]} for k, v in result.features.items()},
            "engines": result.engine_outputs,
            "composite": result.composite,
            "news_recent_7d": [asdict(n) for n in result.news_7d],
            "news_total": len(result.news_items),
            "strategy_results": result.strategy_results,
            "sweep_results": result.sweep_results,
            "feature_evolution": result.feature_evolution,
            "decision_trace": result.decision_trace,
            "backtest_start": result.backtest_start.isoformat(),
            "generated_at": datetime.now(UTC).isoformat(),
        }
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"\n[out  ] wrote {out_path}")

    if not args.no_open:
        reports_dir = (_BACKEND / "reports").resolve()
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        html_path = reports_dir / f"analysis_{ticker}_{stamp}.html"
        html_path.write_text(result.html, encoding="utf-8")
        print(f"\n[html ] wrote {html_path}")
        if _open_in_browser(html_path.as_uri()):
            print(f"[html ] opened in browser")

        # Best-effort: also open /research/<ticker> if the FINRLX frontend is up.
        research_url = f"{args.frontend_url.rstrip('/')}/research/{ticker}"
        if _url_alive(args.frontend_url, timeout=1.5):
            backend_ok = _url_alive(f"{args.backend_url.rstrip('/')}/health", timeout=1.5)
            if not backend_ok:
                print(f"[app  ] frontend up, but backend at {args.backend_url} is not")
            if _open_in_browser(research_url):
                print(f"[app  ] opened {research_url}")
        else:
            print(f"[app  ] FINRLX frontend not running at {args.frontend_url}")
            print(f"[app  ]   to start it:")
            print(f"[app  ]     terminal 1:  cd backend && python -m uvicorn app.main:app --reload")
            print(f"[app  ]     terminal 2:  cd frontend && npm run dev")
            print(f"[app  ]   then open: {research_url}")
            print(f"[app  ]   or use the /analyze wizard at: {args.frontend_url}/analyze")


if __name__ == "__main__":
    main()
