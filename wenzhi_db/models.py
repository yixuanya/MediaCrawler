"""Lightweight dataclass models for type hints (not ORM)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CrawlRun:
    run_id: str
    platform: str
    source_type: str = "keyword_search"
    source_keyword: str = ""
    started_at: str = ""
    finished_at: str = ""
    status: str = ""
    raw_path: str = ""
    normalized_path: str = ""
    scored_path: str = ""
    summary_path: str = ""
    raw_items_count: int = 0
    normalized_items_count: int = 0
    scored_items_count: int = 0
    blockers: list = field(default_factory=list)
    risks: list = field(default_factory=list)


@dataclass
class ContentItem:
    dedup_hash: str
    platform: str
    content_id: str
    content_url: str = ""
    title: str = ""
    desc: str = ""
    author_id: str = ""
    sec_author_id: str = ""
    author_name: str = ""
    author_profile_url: str = ""
    author_followers: Optional[int] = None
    author_followers_status: str = ""
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    weighted_engagement: float = 0.0
    viral_ratio: Optional[float] = None
    low_follower_high_viral_level: str = ""
    total_boom_score: int = 0
    scoring_status: str = ""
    recommended_action: str = ""
    publish_time: str = ""
    run_id: str = ""


@dataclass
class Author:
    platform: str
    author_id: str
    sec_author_id: str = ""
    author_name: str = ""
    author_profile_url: str = ""
    followers: Optional[int] = None
    followers_status: str = ""


@dataclass
class MetricsSnapshot:
    dedup_hash: str
    run_id: str
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    weighted_engagement: float = 0.0
    viral_ratio: Optional[float] = None
    total_boom_score: int = 0
