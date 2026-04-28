"""Unified schemas for wenzhi_collectors."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List


class Platform(str, Enum):
    XHS = "xhs"
    DOUYIN = "douyin"


class SourceType(str, Enum):
    KEYWORD_SEARCH = "keyword_search"
    ACCOUNT_HOMEPAGE = "account_homepage"
    MANUAL_URL = "manual_url"


class AuthorFollowersStatus(str, Enum):
    AVAILABLE = "available"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"
    NOT_REQUESTED = "not_requested"
    NOT_SUPPORTED = "not_supported"


REQUIRED_FIELDS = [
    "platform", "source_type", "source_keyword", "content_id",
    "content_url", "title", "desc", "author_id", "author_name",
    "liked_count", "publish_time", "crawl_time", "run_id", "dedup_hash",
]

OPTIONAL_FIELDS = [
    "sec_author_id", "author_profile_url", "author_followers",
    "collected_count", "comment_count", "share_count",
    "video_url", "image_list", "tag_list", "ip_location",
]

ENRICHER_FIELDS = ["author_followers", "author_followers_status"]


@dataclass
class NormalizedItem:
    # required
    platform: str = ""
    source_type: str = ""
    source_keyword: str = ""
    content_id: str = ""
    content_url: str = ""
    title: str = ""
    desc: str = ""
    author_id: str = ""
    author_name: str = ""
    liked_count: int = 0
    publish_time: str = ""
    crawl_time: str = ""
    run_id: str = ""
    dedup_hash: str = ""
    # optional
    sec_author_id: Optional[str] = None
    author_profile_url: Optional[str] = None
    author_followers: Optional[int] = None
    author_followers_status: str = AuthorFollowersStatus.NOT_REQUESTED.value
    collected_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    video_url: Optional[str] = None
    image_list: Optional[str] = None
    tag_list: Optional[str] = None
    ip_location: Optional[str] = None
    raw_path: str = ""
    normalized_path: str = ""
    risk_flags: List[str] = field(default_factory=list)
    # internal – not in output
    _raw_xsec_token: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_raw_xsec_token", None)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class CollectorRunResult:
    run_id: str = ""
    platform: str = ""
    source_type: str = ""
    source_keyword: str = ""
    started_at: str = ""
    finished_at: str = ""
    raw_items_count: int = 0
    normalized_items_count: int = 0
    dedup_removed_count: int = 0
    author_enriched_count: int = 0
    author_blocked_count: int = 0
    output_raw_path: str = ""
    output_normalized_path: str = ""
    status: str = "fail"
    blockers: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
