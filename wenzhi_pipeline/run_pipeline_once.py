"""CLI: run end-to-end pipeline (collector → scorer) for one or all platforms."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wenzhi_scorer.scorer import score_items
from wenzhi_pipeline.pipeline_summary import (
    count_levels, get_top_items, determine_pipeline_status, determine_all_status,
)

_TZ_CN = timezone(timedelta(hours=8))
_OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "output")

# re-use existing raw files from Window 1.1 for validation
_EXISTING_RAW = {
    "xhs": os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "data", "xhs", "json", "search_contents_2026-04-28.json"),
    "douyin": os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "data", "douyin", "json", "search_contents_2026-04-28.json"),
}


async def run_single_platform(platform: str, keyword: str, max_items: int,
                               use_existing: bool = True) -> dict:
    """Run collector + scorer for one platform. Returns platform result dict."""

    # ── Collector ─────────────────────────────────────────────────────────
    if platform == "xhs":
        from wenzhi_collectors.xhs_collector import XhsCollector
        collector = XhsCollector(keyword=keyword, max_items=max_items)
    else:
        from wenzhi_collectors.douyin_collector import DouyinCollector
        collector = DouyinCollector(keyword=keyword, max_items=max_items)

    if use_existing and platform in _EXISTING_RAW and os.path.isfile(_EXISTING_RAW[platform]):
        collector._existing_raw_path = _EXISTING_RAW[platform]

    collector_result = await collector.run()

    # ── Scorer ────────────────────────────────────────────────────────────
    scored_items: List[dict] = []
    scorer_status = "fail"
    scored_path = ""

    if collector_result.output_normalized_path and os.path.isfile(collector_result.output_normalized_path):
        with open(collector_result.output_normalized_path, "r", encoding="utf-8") as f:
            normalized = json.load(f)
        scored_items = score_items(normalized)

        # save scored
        scored_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "wenzhi_scorer", "output", "scored", collector_result.run_id,
        )
        os.makedirs(scored_dir, exist_ok=True)
        slug = keyword.replace(" ", "_")[:30]
        date = datetime.now(_TZ_CN).strftime("%Y-%m-%d")
        scored_path = os.path.join(scored_dir, f"{platform}_scored_{slug}_{date}.json")
        with open(scored_path, "w", encoding="utf-8") as f:
            json.dump(scored_items, f, ensure_ascii=False, indent=2)

        # determine scorer status
        has_partial = any(i.get("scoring_status") == "partial" for i in scored_items)
        scorer_status = "partial" if has_partial else "pass"

    pipeline_status = determine_pipeline_status(collector_result.status, scorer_status)
    levels = count_levels(scored_items)
    top = get_top_items(scored_items, 3)

    return {
        "collector_status": collector_result.status,
        "scorer_status": scorer_status,
        "normalized_path": collector_result.output_normalized_path,
        "scored_path": scored_path,
        "items_count": len(scored_items),
        "levels_count": levels,
        "top_items": top,
        "pipeline_status": pipeline_status,
        "scored_items": scored_items,  # internal, stripped from summary
    }


async def main():
    parser = argparse.ArgumentParser(description="Run end-to-end pipeline")
    parser.add_argument("--platform", required=True, choices=["xhs", "douyin", "all"])
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--max_items", type=int, default=5)
    parser.add_argument("--live", action="store_true",
                        help="Run live crawl instead of using existing raw files")
    args = parser.parse_args()

    use_existing = not args.live

    pipeline_run_id = f"pipeline_{datetime.now(_TZ_CN).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    started = datetime.now(_TZ_CN).isoformat()

    platforms = ["xhs", "douyin"] if args.platform == "all" else [args.platform]

    platform_results = {}
    all_scored: List[dict] = []
    platform_statuses: List[str] = []

    for p in platforms:
        p_key = p if p != "dy" else "douyin"
        result = await run_single_platform(p_key, args.keyword, args.max_items, use_existing)
        platform_results[p_key] = {
            "collector_status": result["collector_status"],
            "scorer_status": result["scorer_status"],
            "normalized_path": result["normalized_path"],
            "scored_path": result["scored_path"],
            "items_count": result["items_count"],
            "levels_count": result["levels_count"],
            "top_items": result["top_items"],
        }
        all_scored.extend(result["scored_items"])
        platform_statuses.append(result["pipeline_status"])

    # overall
    total_levels = {"S": 0, "A": 0, "B": 0, "C候选": 0, "淘汰": 0}
    for pr in platform_results.values():
        for k, v in pr["levels_count"].items():
            total_levels[k] = total_levels.get(k, 0) + v

    overall_top = get_top_items(all_scored, 5)
    overall_status = determine_all_status(platform_statuses)
    finished = datetime.now(_TZ_CN).isoformat()

    summary = {
        "pipeline_run_id": pipeline_run_id,
        "keyword": args.keyword,
        "platforms": platforms,
        "started_at": started,
        "finished_at": finished,
        "status": overall_status,
        "platform_results": platform_results,
        "total_items": len(all_scored),
        "total_levels_count": total_levels,
        "top_items_overall": overall_top,
        "blockers": [],
        "risks": [],
        "next_step": "",
    }

    # save summary
    summary_dir = os.path.join(_OUTPUT_BASE, pipeline_run_id)
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, "pipeline_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    asyncio.run(main())
