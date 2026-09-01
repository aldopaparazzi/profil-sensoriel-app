# reporting/bilan_strategies.py
import json

from storage.paths import paths


def load_strategies() -> dict:
    with paths.strategies_path.open(encoding="utf-8") as f:
        return json.load(f)


def select_strategy_candidates(scores: dict, threshold: float) -> dict:
    strategies = load_strategies()
    quadrants = scores.get("quadrants", {})
    domains = scores.get("domains", {})
    candidates = {}

    for quadrant, values in quadrants.items():
        z = values.get("z")

        if z is None or abs(z) < threshold:
            continue

        direction = "plus" if z > 0 else "moins"
        block = strategies.get(quadrant, {}).get(direction)

        if not block:
            continue

        filtered_items = {}

        for domaine, items in block.get("items", {}).items():
            if domaine == "general":
                filtered_items[domaine] = items
                continue

            domain_z = domains.get(domaine, {}).get("z")

            if domain_z is not None and abs(domain_z) >= threshold:
                filtered_items[domaine] = items

        if filtered_items:
            candidates[quadrant] = {
                "z": z,
                "direction": direction,
                "objectif": block.get("objectif"),
                "items": filtered_items,
            }

    return candidates
