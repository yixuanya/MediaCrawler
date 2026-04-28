"""Normalizer: raw MediaCrawler items → NormalizedItem."""
from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from .schemas import NormalizedItem, Platform, SourceType, AuthorFollowersStatus
from .dedup import make_dedup_hash

_TZ_CN = timezone(timedelta(hours=8))


def _parse_count(val) -> Optional[int]:
    """Parse count strings like '10万+', '1.2万', '598', '' → int or None."""
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip().replace(",", "").replace("+", "")
    if not s:
        return None
    m = re.match(r"^([\d.]+)\s*万$", s)
    if m:
        return int(float(m.group(1)) * 10000)
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _ts_to_iso(ts, unit="ms") -> str:
    """Convert timestamp to ISO8601 string (Asia/Shanghai)."""
    if ts is None or ts == "" or ts == 0:
        return ""
    ts_val = int(ts)
    if unit == "ms":
        ts_val = ts_val // 1000 if ts_val > 1e12 else ts_val
    dt = datetime.fromtimestamp(ts_val, tz=_TZ_CN)
    return dt.isoformat()


def normalize_xhs_item(
    raw: dict,
    run_id: str,
    raw_path: str,
    normalized_path: str,
    source_keyword: str,
    source_type: str = SourceType.KEYWORD_SEARCH.value,
) -> NormalizedItem:
    user_id = raw.get("user_id", "")
    content_id = raw.get("note_id", "")
    item = NormalizedItem(
        platform=Platform.XHS.value,
        source_type=source_type,
        source_keyword=source_keyword,
        content_id=content_id,
        content_url=raw.get("note_url", ""),
        title=raw.get("title", ""),
        desc=raw.get("desc", ""),
        author_id=user_id,
        author_name=raw.get("nickname", ""),
        liked_count=_parse_count(raw.get("liked_count")) or 0,
        publish_time=_ts_to_iso(raw.get("time"), "ms"),
        crawl_time=_ts_to_iso(raw.get("last_modify_ts"), "ms"),
        run_id=run_id,
        dedup_hash=make_dedup_hash(Platform.XHS.value, content_id),
        sec_author_id=None,
        author_profile_url=f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else None,
        author_followers=None,
        author_followers_status=AuthorFollowersStatus.NOT_REQUESTED.value,
        collected_count=_parse_count(raw.get("collected_count")),
        comment_count=_parse_count(raw.get("comment_count")),
        share_count=_parse_count(raw.get("share_count")),
        video_url=raw.get("video_url") or None,
        image_list=raw.get("image_list") or None,
        tag_list=raw.get("tag_list") or None,
        ip_location=raw.get("ip_location") or None,
        raw_path=raw_path,
        normalized_path=normalized_path,
        risk_flags=[],
        _raw_xsec_token=raw.get("xsec_token", ""),
    )
    return item


def normalize_douyin_item(
    raw: dict,
    run_id: str,
    raw_path: str,
    normalized_path: str,
    source_keyword: str,
    source_type: str = SourceType.KEYWORD_SEARCH.value,
) -> NormalizedItem:
    user_id = raw.get("user_id", "")
    sec_uid = raw.get("sec_uid", "") or ""
    content_id = raw.get("aweme_id", "")
    item = NormalizedItem(
        platform=Platform.DOUYIN.value,
        source_type=source_type,
        source_keyword=source_keyword,
        content_id=content_id,
        content_url=raw.get("aweme_url", ""),
        title=raw.get("title", ""),
        desc=raw.get("desc", ""),
        author_id=user_id,
        author_name=raw.get("nickname", ""),
        liked_count=_parse_count(raw.get("liked_count")) or 0,
        publish_time=_ts_to_iso(raw.get("create_time"), "s"),
        crawl_time=_ts_to_iso(raw.get("last_modify_ts"), "ms"),
        run_id=run_id,
        dedup_hash=make_dedup_hash(Platform.DOUYIN.value, content_id),
        sec_author_id=sec_uid or None,
        author_profile_url=f"https://www.douyin.com/user/{sec_uid}" if sec_uid else None,
        author_followers=None,
        author_followers_status=AuthorFollowersStatus.NOT_REQUESTED.value,
        collected_count=_parse_count(raw.get("collected_count")),
        comment_count=_parse_count(raw.get("comment_count")),
        share_count=_parse_count(raw.get("share_count")),
        video_url=raw.get("video_download_url") or None,
        image_list=raw.get("note_download_url") or None,
        tag_list=_extract_douyin_tags(raw.get("title", "") + " " + raw.get("desc", "")),
        ip_location=raw.get("ip_location") or None,
        raw_path=raw_path,
        normalized_path=normalized_path,
        risk_flags=[],
    )
    return item


def _extract_douyin_tags(text: str) -> Optional[str]:
    tags = re.findall(r"#(\S+?)(?:\s|$|#)", text)
    return ",".join(tags) if tags else None
