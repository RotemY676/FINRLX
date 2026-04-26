"""Dataset loader for local CPU RL research.

Supports two modes:
1. Real dataset: load from a JSON file exported by the backend's
   POST /api/v1/rl/training/export-dataset endpoint.
2. Synthetic fallback: generate deterministic synthetic data when
   no real dataset file is available.

LOCAL RESEARCH ONLY — no production database access.
"""

import json
import os
from pathlib import Path


def load_dataset(path: str | None = None, seed: int = 42) -> tuple[list[dict], bool]:
    """Load dataset rows for the research environment.

    Returns:
        (rows, synthetic_data) — rows is a list of dicts with at least
        engine_score and realized_return; synthetic_data is True if
        generated rather than loaded from file.
    """
    if path and os.path.isfile(path):
        return _load_from_file(path)
    return _generate_synthetic(seed=seed), True


def _load_from_file(path: str) -> tuple[list[dict], bool]:
    """Load real dataset from JSON export."""
    with open(path, "r") as f:
        data = json.load(f)

    # Handle both flat list and wrapped {"rows": [...]} formats
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and "rows" in data:
        rows = data["rows"]
    else:
        raise ValueError(f"Unrecognized dataset format in {path}")

    # Flatten asset-level data into per-step rows
    flat_rows = []
    for row in rows:
        assets = row.get("assets", [])
        if not assets:
            continue
        # Average across assets for a portfolio-level observation
        avg_score = sum(a.get("engine_score", 0) or 0 for a in assets) / max(len(assets), 1)
        avg_return = sum(a.get("realized_return", 0) or 0 for a in assets) / max(len(assets), 1)
        flat_rows.append({
            "as_of_date": row.get("as_of_date"),
            "engine_score": round(avg_score, 6),
            "realized_return": round(avg_return, 6),
            "asset_count": len(assets),
        })

    if not flat_rows:
        raise ValueError(f"No usable rows in {path}")

    return flat_rows, False


def _generate_synthetic(n_steps: int = 60, seed: int = 42) -> list[dict]:
    """Generate deterministic synthetic dataset for research fallback."""
    try:
        import numpy as np
        rng = np.random.default_rng(seed)
    except ImportError:
        # Fallback without numpy
        import random
        random.seed(seed)
        rng = None

    rows = []
    for i in range(n_steps):
        if rng is not None:
            score = float(rng.uniform(-0.3, 0.7))
            ret = float(rng.normal(0.001, 0.015))
        else:
            score = random.uniform(-0.3, 0.7)
            ret = random.gauss(0.001, 0.015)
        rows.append({
            "as_of_date": f"2026-01-{(i % 28) + 1:02d}",
            "engine_score": round(score, 6),
            "realized_return": round(ret, 6),
            "asset_count": 2,
            "synthetic": True,
        })
    return rows


def export_sample_dataset(output_path: str, seed: int = 42) -> str:
    """Export a sample synthetic dataset for testing."""
    rows = _generate_synthetic(seed=seed)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"rows": rows, "synthetic": True, "seed": seed}, f, indent=2)
    return output_path
