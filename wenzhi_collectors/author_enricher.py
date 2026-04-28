"""Author enricher: supplement author_followers via secondary API calls."""
from __future__ import annotations

import asyncio
import logging
from typing import List

from .schemas import NormalizedItem, AuthorFollowersStatus

logger = logging.getLogger("wenzhi_collectors.author_enricher")


# ── XHS ──────────────────────────────────────────────────────────────────────

async def enrich_xhs_authors(
    items: List[NormalizedItem],
    client,  # XiaoHongShuClient
    sleep_between: float = 1.5,
) -> List[NormalizedItem]:
    seen: dict = {}  # user_id → (fans, status)

    for item in items:
        uid = item.author_id
        if uid in seen:
            item.author_followers, item.author_followers_status = seen[uid]
            if seen[uid][1] != AuthorFollowersStatus.AVAILABLE.value:
                item.risk_flags.append("xhs_author_enrichment_failed")
            continue

        try:
            creator_info = await client.get_creator_info(
                user_id=uid,
                xsec_token=item._raw_xsec_token,
                xsec_source="pc_search",
            )
            fans = _extract_xhs_fans(creator_info)
            item.author_followers = fans
            item.author_followers_status = AuthorFollowersStatus.AVAILABLE.value
            seen[uid] = (fans, AuthorFollowersStatus.AVAILABLE.value)
        except Exception as e:
            logger.warning(f"XHS author enrich failed for {uid}: {e}")
            item.author_followers = None
            item.author_followers_status = AuthorFollowersStatus.UNKNOWN.value
            item.risk_flags.append("xhs_author_enrichment_failed")
            seen[uid] = (None, AuthorFollowersStatus.UNKNOWN.value)

        await asyncio.sleep(sleep_between)

    return items


def _extract_xhs_fans(creator_info: dict) -> int | None:
    interactions = creator_info.get("interactions", [])
    for entry in interactions:
        if entry.get("type") == "fans":
            try:
                return int(entry["count"])
            except (KeyError, ValueError, TypeError):
                pass
    return None


# ── Douyin ───────────────────────────────────────────────────────────────────

async def enrich_douyin_authors(
    items: List[NormalizedItem],
    client,  # DouYinClient
    max_retries: int = 1,
    backoff_sec: float = 3.0,
    sleep_between: float = 2.0,
) -> List[NormalizedItem]:
    seen: dict = {}  # sec_uid → (fans, status)

    for item in items:
        sec_uid = item.sec_author_id
        if not sec_uid:
            item.author_followers_status = AuthorFollowersStatus.NOT_SUPPORTED.value
            continue
        if sec_uid in seen:
            item.author_followers = seen[sec_uid][0]
            item.author_followers_status = seen[sec_uid][1]
            if seen[sec_uid][1] == AuthorFollowersStatus.BLOCKED.value:
                item.risk_flags.append("douyin_author_followers_blocked")
            continue

        # Layer A: first attempt
        fans, status = await _try_get_douyin_fans(client, sec_uid)

        # Layer B: retry once with backoff
        if status != AuthorFollowersStatus.AVAILABLE.value and max_retries > 0:
            await asyncio.sleep(backoff_sec)
            fans, status = await _try_get_douyin_fans(client, sec_uid)

        # Layer C: record result
        item.author_followers = fans
        item.author_followers_status = status
        if status == AuthorFollowersStatus.BLOCKED.value:
            item.risk_flags.append("douyin_author_followers_blocked")

        seen[sec_uid] = (fans, status)
        await asyncio.sleep(sleep_between)

    return items


async def _try_get_douyin_fans(client, sec_uid: str) -> tuple:
    try:
        info = await client.get_user_info(sec_uid)
        user = info.get("user", {}) if isinstance(info, dict) else {}
        fans = user.get("max_follower_count")
        if fans is not None:
            return int(fans), AuthorFollowersStatus.AVAILABLE.value
        return None, AuthorFollowersStatus.UNKNOWN.value
    except Exception as e:
        err = str(e).lower()
        if "blocked" in err or "account" in err:
            return None, AuthorFollowersStatus.BLOCKED.value
        return None, AuthorFollowersStatus.UNKNOWN.value
