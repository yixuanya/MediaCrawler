"""CLI entry point: run a single collection pass."""
from __future__ import annotations

import argparse
import asyncio
import sys
import os

# ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def main():
    parser = argparse.ArgumentParser(description="Run one collection pass")
    parser.add_argument("--platform", required=True, choices=["xhs", "dy"])
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--max_items", type=int, default=5)
    parser.add_argument("--use_existing_raw", type=str, default="",
                        help="Path to existing raw JSON (skip CLI crawl)")
    args = parser.parse_args()

    if args.platform == "xhs":
        from wenzhi_collectors.xhs_collector import XhsCollector
        collector = XhsCollector(keyword=args.keyword, max_items=args.max_items)
    else:
        from wenzhi_collectors.douyin_collector import DouyinCollector
        collector = DouyinCollector(keyword=args.keyword, max_items=args.max_items)

    if args.use_existing_raw:
        collector._existing_raw_path = args.use_existing_raw

    result = await collector.run()
    print(result.to_json())
    return result


if __name__ == "__main__":
    asyncio.run(main())
