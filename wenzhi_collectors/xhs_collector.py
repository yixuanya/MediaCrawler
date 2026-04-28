"""XHS Collector: wraps MediaCrawler for keyword search + author enrichment."""
from __future__ import annotations

import asyncio
import glob
import json
import os
import shutil
from typing import List

from playwright.async_api import async_playwright

from .base import BaseCollector
from .schemas import NormalizedItem, Platform
from .normalizer import normalize_xhs_item
from .author_enricher import enrich_xhs_authors

_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
_BROWSER_DATA = os.path.join(_PROJECT_ROOT, "browser_data", "xhs_user_data_dir")


class XhsCollector(BaseCollector):
    def __init__(self, keyword: str, max_items: int = 5):
        super().__init__(Platform.XHS.value, keyword, max_items)
        self._existing_raw_path = ""  # set externally to skip CLI

    async def collect_raw(self) -> List[dict]:
        if self._existing_raw_path and os.path.isfile(self._existing_raw_path):
            with open(self._existing_raw_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            shutil.copy2(self._existing_raw_path, os.path.join(self.raw_dir, os.path.basename(self._existing_raw_path)))
            return raw_items

        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "main.py",
            "--platform", "xhs",
            "--lt", "qrcode",
            "--type", "search",
            "--keywords", self.keyword,
            "--save_data_option", "json",
            "--get_comment", "false",
            "--headless", "true",
            cwd=_PROJECT_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        pattern = os.path.join(_PROJECT_ROOT, "data", "xhs", "json", "search_contents_*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if not files:
            raise RuntimeError(f"XHS search produced no output. stderr={stderr.decode()[-500:]}")

        with open(files[0], "r", encoding="utf-8") as f:
            raw_items = json.load(f)
        shutil.copy2(files[0], os.path.join(self.raw_dir, os.path.basename(files[0])))
        return raw_items

    def normalize(self, raw_items: List[dict], raw_path: str) -> List[NormalizedItem]:
        return [
            normalize_xhs_item(r, self.run_id, raw_path, "", self.keyword)
            for r in raw_items
        ]

    async def enrich_authors(self, items: List[NormalizedItem]) -> List[NormalizedItem]:
        from media_platform.xhs.client import XiaoHongShuClient
        from tools import utils

        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=_BROWSER_DATA,
                headless=True,
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            )
            page = await ctx.new_page()
            await page.goto("https://www.xiaohongshu.com")
            cookie_str, cookie_dict = await utils.convert_browser_context_cookies(
                ctx, urls=["https://www.xiaohongshu.com"]
            )
            client = XiaoHongShuClient(
                headers={
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "content-type": "application/json;charset=UTF-8",
                    "origin": "https://www.xiaohongshu.com",
                    "referer": "https://www.xiaohongshu.com/",
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                    "Cookie": cookie_str,
                },
                playwright_page=page,
                cookie_dict=cookie_dict,
            )
            items = await enrich_xhs_authors(items, client, sleep_between=1.5)
            await ctx.close()
        return items
