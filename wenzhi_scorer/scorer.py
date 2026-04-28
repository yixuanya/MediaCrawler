"""Core scorer: takes normalized items, outputs scored items."""
from __future__ import annotations

from typing import Optional
from . import scoring_rules as R


def _safe_int(v) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def calc_weighted_engagement(item: dict) -> float:
    platform = item.get("platform", "")
    w = R.XHS_WEIGHTS if platform == "xhs" else R.DY_WEIGHTS
    liked = _safe_int(item.get("liked_count"))
    collected = _safe_int(item.get("collected_count"))
    comment = _safe_int(item.get("comment_count"))
    share = _safe_int(item.get("share_count"))
    return (liked * w["liked"]
            + collected * w["collected"]
            + comment * w["comment"]
            + share * w["share"])


def calc_viral_ratio(weighted_engagement: float, followers: Optional[int]) -> Optional[float]:
    if followers is None or followers <= 0:
        return None
    return round(weighted_engagement / followers, 4)


def determine_level(
    followers: Optional[int],
    followers_available: bool,
    weighted_engagement: float,
    viral_ratio: Optional[float],
    spike_ratio: Optional[float],
    platform: str,
) -> str:
    """Return one of: S, A, B, C候选, 淘汰"""
    # check spike shortcut first
    if spike_ratio is not None:
        if spike_ratio >= R.LEVEL_S["spike_ratio"]:
            return "S"
        if spike_ratio >= R.LEVEL_A["spike_ratio"]:
            return "A"
        if spike_ratio >= R.LEVEL_B["spike_ratio"]:
            return "B"

    if followers_available and followers is not None and followers > 0 and viral_ratio is not None:
        if (followers < R.LEVEL_S["max_followers"]
                and weighted_engagement > R.LEVEL_S["min_engagement"]
                and viral_ratio > R.LEVEL_S["min_viral_ratio"]):
            return "S"
        if (followers < R.LEVEL_A["max_followers"]
                and weighted_engagement > R.LEVEL_A["min_engagement"]
                and viral_ratio > R.LEVEL_A["min_viral_ratio"]):
            return "A"
        if (followers < R.LEVEL_B["max_followers"]
                and weighted_engagement > R.LEVEL_B["min_engagement"]
                and viral_ratio > R.LEVEL_B["min_viral_ratio"]):
            return "B"

    # C候选: followers missing but decent engagement, or engagement >= 1000
    if not followers_available and weighted_engagement >= R.LEVEL_C_MIN_ENGAGEMENT:
        return "C候选"
    if followers_available and weighted_engagement >= R.LEVEL_C_MIN_ENGAGEMENT:
        return "C候选"

    return "淘汰"


def calc_target_user_score(text: str) -> int:
    score = 0
    for kw in R.TARGET_USER_KEYWORDS:
        if kw in text:
            score += 5
    return min(score, 25)


def calc_topic_reusable_score(text: str) -> int:
    score = 0
    for kw in R.TOPIC_KEYWORDS:
        if kw in text:
            score += 4
    return min(score, 20)


def calc_comment_need_score(comment_count: int) -> int:
    for threshold, points in R.COMMENT_THRESHOLDS:
        if comment_count >= threshold:
            return points
    return 0


def calc_conversion_score(text: str) -> int:
    score = 0
    for kw in R.CONVERSION_KEYWORDS:
        if kw in text:
            score += 2
    return min(score, 10)


def score_item(item: dict) -> dict:
    """Score a single normalized item. Returns a new dict with all original + score fields."""
    result = dict(item)  # shallow copy

    # weighted engagement
    we = calc_weighted_engagement(item)
    result["weighted_engagement"] = we

    # followers
    followers = item.get("author_followers")
    status = item.get("author_followers_status", "not_requested")
    followers_available = (status == "available" and followers is not None and followers > 0)
    result["followers_available"] = followers_available

    # viral ratio
    vr = calc_viral_ratio(we, followers) if followers_available else None
    result["viral_ratio"] = vr

    # spike (not available yet)
    result["account_avg_engagement_10"] = None
    result["single_item_spike_ratio"] = None
    result["spike_level"] = None

    # level
    level = determine_level(
        followers, followers_available, we, vr,
        result["single_item_spike_ratio"],
        item.get("platform", ""),
    )
    result["low_follower_high_viral_level"] = level

    # sub-scores
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    result["viral_score"] = R.VIRAL_SCORE_MAP.get(level, 0)
    result["target_user_score"] = calc_target_user_score(text)
    result["topic_reusable_score"] = calc_topic_reusable_score(text)
    result["comment_need_score"] = calc_comment_need_score(_safe_int(item.get("comment_count")))
    result["conversion_score"] = calc_conversion_score(text)
    result["total_boom_score"] = (
        result["viral_score"]
        + result["target_user_score"]
        + result["topic_reusable_score"]
        + result["comment_need_score"]
        + result["conversion_score"]
    )

    # scoring status
    if followers_available:
        result["scoring_status"] = "pass"
        result["recommended_action"] = ""
    else:
        result["scoring_status"] = "partial"
        result["recommended_action"] = "需要后续补作者粉丝数或用账号主页近10条平均互动判断"
        if "followers_missing_degraded_scoring" not in result.get("risk_flags", []):
            result.setdefault("risk_flags", []).append("followers_missing_degraded_scoring")

    return result


def score_items(items: list[dict]) -> list[dict]:
    return [score_item(item) for item in items]
