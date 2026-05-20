"""Data provider adapters (Phase MVP-2).

Each provider exposes:
  fetch_bars(ticker, asset_id, start, end) -> tuple[list[dict], list[str]]
returning (bars_with_quality_passed, warnings).
"""
