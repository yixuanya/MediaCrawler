"""Pipeline summary builder."""
from __future__ import annotations

import json
from typing import List


def build_top_item(item: dict) -> dict:
    return {
        "platform": item.get("platform", ""),
        "content_id": item.get("content_id", ""),
        "title": item.get("title", ""),
        "content_url": item.get("content_url", ""),
        "author_name": item.get("author_name", ""),
        "weighted_engagement": item.get("weighted_engagement", 0),
        "viral_ratio": item.get("viral_ratio"),
        "low_follower_high_viral_level": item.get("low_follower_high_viral_level", ""),
        "total_boom_score": item.get("total_boom_score", 0),
        "recommended_action": item.get("recommended_action", ""),
    }


def count_levels(scored_items: List[dict]) -> dict:
    levels = {"S": 0, "A": 0, "B": 0, "C候选": 0, "淘汰": 0}
    for item in scored_items:
        lvl = item.get("low_follower_high_viral_level", "淘汰")
        levels[lvl] = levels.get(lvl, 0) + 1
    return levels


def get_top_items(scored_items: List[dict], n: int = 3) -> List[dict]:
    sorted_items = sorted(scored_items, key=lambda x: x.get("total_boom_score", 0), reverse=True)
    return [build_top_item(i) for i in sorted_items[:n]]


def determine_pipeline_status(collector_status: str, scorer_status: str) -> str:
    if collector_status == "fail":
        return "fail"
    if collector_status == "pass" and scorer_status == "pass":
        return "pass"
    return "partial"


def determine_all_status(platform_statuses: List[str]) -> str:
    if all(s == "fail" for s in platform_statuses):
        return "fail"
    if all(s == "pass" for s in platform_statuses):
        return "pass"
    return "partial"
