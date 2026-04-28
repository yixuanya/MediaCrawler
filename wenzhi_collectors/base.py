"""Base collector abstract class."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List

from .schemas import NormalizedItem, CollectorRunResult, Platform, SourceType

_TZ_CN = timezone(timedelta(hours=8))
_OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "output")


def _make_run_id(platform: str, source_type: str) -> str:
    now = datetime.now(_TZ_CN)
    rand = uuid.uuid4().hex[:4]
    return f"{platform}_{source_type}_{now.strftime('%Y%m%d_%H%M%S')}_{rand}"


class BaseCollector(ABC):
    def __init__(self, platform: str, keyword: str, max_items: int = 5,
                 source_type: str = SourceType.KEYWORD_SEARCH.value):
        self.platform = platform
        self.keyword = keyword
        self.max_items = max_items
        self.source_type = source_type
        self.run_id = _make_run_id(platform, source_type)
        self.raw_dir = os.path.join(_OUTPUT_BASE, "raw", self.run_id)
        self.norm_dir = os.path.join(_OUTPUT_BASE, "normalized", self.run_id)
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.norm_dir, exist_ok=True)

    async def run(self) -> CollectorRunResult:
        started = datetime.now(_TZ_CN).isoformat()
        result = CollectorRunResult(
            run_id=self.run_id,
            platform=self.platform,
            source_type=self.source_type,
            source_keyword=self.keyword,
            started_at=started,
        )
        try:
            raw_items = await self.collect_raw()
            result.raw_items_count = len(raw_items)

            # save raw
            raw_path = self._save_raw(raw_items)
            result.output_raw_path = raw_path

            # normalize + trim
            normalized = self.normalize(raw_items, raw_path)
            normalized = normalized[: self.max_items]

            # dedup
            from .dedup import dedup_items
            normalized, removed = dedup_items(normalized)
            result.dedup_removed_count = removed

            # enrich
            normalized = await self.enrich_authors(normalized)
            enriched = sum(1 for i in normalized if i.author_followers is not None)
            blocked = sum(1 for i in normalized if "blocked" in i.author_followers_status)
            result.author_enriched_count = enriched
            result.author_blocked_count = blocked

            # save normalized
            norm_path = self._save_normalized(normalized)
            result.output_normalized_path = norm_path
            result.normalized_items_count = len(normalized)

            # set normalized_path on items
            for item in normalized:
                item.normalized_path = norm_path

            result.status = "pass" if enriched > 0 else "partial"
        except Exception as e:
            result.status = "fail"
            result.blockers.append(str(e))

        result.finished_at = datetime.now(_TZ_CN).isoformat()
        return result

    @abstractmethod
    async def collect_raw(self) -> List[dict]:
        """Return list of raw dicts from MediaCrawler."""
        ...

    @abstractmethod
    def normalize(self, raw_items: List[dict], raw_path: str) -> List[NormalizedItem]:
        ...

    @abstractmethod
    async def enrich_authors(self, items: List[NormalizedItem]) -> List[NormalizedItem]:
        ...

    def _save_raw(self, raw_items: List[dict]) -> str:
        slug = self.keyword.replace(" ", "_")[:30]
        date = datetime.now(_TZ_CN).strftime("%Y-%m-%d")
        fname = f"{self.platform}_raw_{slug}_{date}.json"
        path = os.path.join(self.raw_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(raw_items, f, ensure_ascii=False, indent=2)
        return path

    def _save_normalized(self, items: List[NormalizedItem]) -> str:
        slug = self.keyword.replace(" ", "_")[:30]
        date = datetime.now(_TZ_CN).strftime("%Y-%m-%d")
        fname = f"{self.platform}_normalized_{slug}_{date}.json"
        path = os.path.join(self.norm_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)
        return path
