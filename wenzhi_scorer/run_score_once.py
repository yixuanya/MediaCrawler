"""CLI entry: score a normalized JSON file."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wenzhi_scorer.scorer import score_items

_TZ_CN = timezone(timedelta(hours=8))
_OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "output", "scored")


def main():
    parser = argparse.ArgumentParser(description="Score normalized items")
    parser.add_argument("--input", required=True, help="Path to normalized JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        items = json.load(f)

    scored = score_items(items)

    # determine output path
    platform = scored[0].get("platform", "unknown") if scored else "unknown"
    run_id = scored[0].get("run_id", uuid.uuid4().hex[:8]) if scored else "unknown"
    keyword_slug = (scored[0].get("source_keyword", "").replace(" ", "_")[:30]) if scored else "unknown"
    date = datetime.now(_TZ_CN).strftime("%Y-%m-%d")

    out_dir = os.path.join(_OUTPUT_BASE, run_id)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{platform}_scored_{keyword_slug}_{date}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=2)

    # summary
    levels = {}
    for item in scored:
        lvl = item.get("low_follower_high_viral_level", "淘汰")
        levels[lvl] = levels.get(lvl, 0) + 1

    summary = {
        "input": args.input,
        "output": out_path,
        "items_count": len(scored),
        "levels": levels,
        "top_items": sorted(scored, key=lambda x: x.get("total_boom_score", 0), reverse=True)[:3],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
