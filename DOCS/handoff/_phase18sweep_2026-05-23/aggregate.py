"""Aggregate the per-(route,viewport) findings into a per-route summary."""
import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent
findings_dir = OUT / "findings"
findings = [json.loads(p.read_text()) for p in sorted(findings_dir.glob("*.json"))]
# Persist the consolidated array for downstream consumers.
(OUT / "sweep-report.json").write_text(json.dumps(findings, indent=2))

by_route = defaultdict(
    lambda: {
        "viewports": [],
        "console_errors": set(),
        "page_errors": set(),
        "axe_rules": {},
        "axe_totals": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
        "fail_count": 0,
        "http_statuses": set(),
    }
)

for f in findings:
    r = by_route[f["route"]]
    r["viewports"].append(f["viewport"])
    r["http_statuses"].add(f.get("httpStatus"))
    for e in f["consoleErrors"]:
        r["console_errors"].add(e[:200])
    for e in f["pageErrors"]:
        r["page_errors"].add(e[:200])
    for k in ("critical", "serious", "moderate", "minor"):
        r["axe_totals"][k] += f["axe"][k]
    for rule in f["axe"]["rules"]:
        cur = r["axe_rules"].setdefault(rule["id"], {"impact": rule["impact"], "nodes": 0})
        cur["nodes"] = max(cur["nodes"], rule["nodes"])
    if f["status"] == "fail":
        r["fail_count"] += 1

print(f"Total routes tested: {len(by_route)}")
print(f"Total findings entries: {len(findings)}")
print()
print("=" * 100)
print("AXE VIOLATIONS PER ROUTE (sum across all viewports)")
print("=" * 100)
header = "{:<25} {:>5} {:>5} {:>5} {:>5}  Top rules".format(
    "Route", "Crit", "Ser", "Mod", "Min"
)
print(header)
print("-" * 100)
for route in sorted(by_route.keys()):
    r = by_route[route]
    top_rules = sorted(r["axe_rules"].items(), key=lambda x: (-x[1]["nodes"], x[0]))[:4]
    top_str = ", ".join(
        "{}({}/{})".format(rid, info["impact"][:3], info["nodes"])
        for rid, info in top_rules
    )
    print(
        "{:<25} {:>5} {:>5} {:>5} {:>5}  {}".format(
            route,
            r["axe_totals"]["critical"],
            r["axe_totals"]["serious"],
            r["axe_totals"]["moderate"],
            r["axe_totals"]["minor"],
            top_str,
        )
    )

print()
print("=" * 100)
print("UNIQUE AXE RULES OBSERVED (across the whole sweep)")
print("=" * 100)
rule_summary = defaultdict(lambda: {"impact": "", "routes": 0, "max_nodes": 0})
for route, r in by_route.items():
    for rid, info in r["axe_rules"].items():
        rule_summary[rid]["impact"] = info["impact"]
        rule_summary[rid]["routes"] += 1
        rule_summary[rid]["max_nodes"] = max(
            rule_summary[rid]["max_nodes"], info["nodes"]
        )
for rid, info in sorted(
    rule_summary.items(), key=lambda x: ({"critical": 0, "serious": 1, "moderate": 2, "minor": 3}.get(x[1]["impact"], 4), -x[1]["routes"])
):
    print(
        "  {:<35} impact={:<8} on_routes={:>2}  max_nodes={}".format(
            rid, info["impact"], info["routes"], info["max_nodes"]
        )
    )

print()
print("=" * 100)
print("CONSOLE ERRORS PER ROUTE (deduped across viewports)")
print("=" * 100)
for route in sorted(by_route.keys()):
    r = by_route[route]
    if r["console_errors"]:
        print(
            "\n[{}] http={} fails={}".format(
                route, r["http_statuses"], r["fail_count"]
            )
        )
        for e in sorted(r["console_errors"])[:5]:
            print("  - {}".format(e[:180]))

print()
print("=" * 100)
print("PAGE ERRORS PER ROUTE")
print("=" * 100)
for route in sorted(by_route.keys()):
    r = by_route[route]
    if r["page_errors"]:
        print("\n[{}]".format(route))
        for e in sorted(r["page_errors"])[:5]:
            print("  - {}".format(e[:180]))
