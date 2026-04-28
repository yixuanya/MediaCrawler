"""Douyin Collector: wraps MediaCrawler for keyword search + author enrichment."""
from __future__ import annotations

import asyncio
import glob
import json
import os
import shutil
from typing import List

from .base import BaseCollector
from .schemas import NormalizedItem, Platform, AuthorFollowersStatus
from .normalizer import normalize_douyin_item
from .author_enricher import enrich_douyin_authors

_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
_BROWSER_DATA = os.path.join(_PROJECT_ROOT, "browser_data", "cdp_dy_user_data_dir")


class DouyinCollector(BaseCollector):
    def __init__(self, keyword: str, max_items: int = 5):
        super().__init__(Platform.DOUYIN.value, keyword, max_items)
        self._existing_raw_path = ""  # set externally to skip CLI

    async def collect_raw(self) -> List[dict]:
        if self._existing_raw_path and os.path.isfile(self._existing_raw_path):
            with open(self._existing_raw_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            shutil.copy2(self._existing_raw_path, os.path.join(self.raw_dir, os.path.basename(self._existing_raw_path)))
            return raw_items

        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "main.py",
            "--platform", "dy",
            "--lt", "qrcode",
            "--type", "search",
            "--keywords", self.keyword,
            "--save_data_option", "json",
            "--get_comment", "false",
            "--headless", "false",
            cwd=_PROJECT_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        pattern = os.path.join(_PROJECT_ROOT, "data", "douyin", "json", "search_contents_*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if not files:
            raise RuntimeError(f"Douyin search produced no output. stderr={stderr.decode()[-500:]}")

        with open(files[0], "r", encoding="utf-8") as f:
            raw_items = json.load(f)
        shutil.copy2(files[0], os.path.join(self.raw_dir, os.path.basename(files[0])))
        return raw_items

    def normalize(self, raw_items: List[dict], raw_path: str) -> List[NormalizedItem]:
        return [
            normalize_douyin_item(r, self.run_id, raw_path, "", self.keyword)
            for r in raw_items
        ]

    async def enrich_authors(self, items: List[NormalizedItem]) -> List[NormalizedItem]:
        """Douyin author enrichment with degradation.
        Since douyin get_user_info requires active CDP browser context which is
        not easily reusable offline, we mark all as blocked for now.
        """
        for item in items:
            if item.sec_author_id:
                item.author_followers = None
                item.author_followers_status = AuthorFollowersStatus.BLOCKED.value
                item.risk_flags.append("douyin_author_followers_blocked")
            else:
                item.author_followers_status = AuthorFollowersStatus.NOT_SUPPORTED.value
        return items
