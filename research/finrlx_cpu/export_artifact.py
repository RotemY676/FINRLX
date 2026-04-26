"""Export research artifacts to JSON files.

LOCAL RESEARCH ONLY — not used by production.
"""

import json
from pathlib import Path


def save_artifact(artifact: dict, output_dir: str = "outputs") -> str:
    """Save a research artifact to a JSON file in the outputs directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    algo = artifact.get("algorithm", "unknown").lower()
    ts = artifact.get("artifact_created_at", "unknown").replace(":", "-").replace(".", "-")
    filename = f"artifact_{algo}_{ts}.json"
    filepath = Path(output_dir) / filename

    with open(filepath, "w") as f:
        json.dump(artifact, f, indent=2, default=str)

    return str(filepath)
