"""Ingest a pipeline_summary.json into SQLite."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wenzhi_db.db import get_conn
from wenzhi_db import repository as repo


def ingest(summary_path: str):
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    conn = get_conn()
    stats = {
        "content_items": 0,
        "authors": 0,
        "metrics_history": 0,
        "feishu_queue": 0,
        "crawl_runs": 0,
    }

    # insert pipeline summary
    repo.insert_pipeline_summary(conn, summary, summary_path)
    repo.insert_log(conn, summary["pipeline_run_id"], "INFO",
                    f"Pipeline summary ingested: {summary['pipeline_run_id']}")

    # process each platform result
    for platform, result in summary.get("platform_results", {}).items():
        scored_path = result.get("scored_path", "")
        if not scored_path or not os.path.isfile(scored_path):
            repo.insert_log(conn, summary["pipeline_run_id"], "WARN",
                            f"Scored path missing for {platform}: {scored_path}")
            continue

        with open(scored_path, "r", encoding="utf-8") as f:
            scored_items = json.load(f)

        # crawl_run
        run_id = scored_items[0].get("run_id", "") if scored_items else ""
        repo.upsert_crawl_run(conn, {
            "run_id": run_id,
            "platform": platform,
            "source_type": "keyword_search",
            "source_keyword": summary.get("keyword", ""),
            "started_at": summary.get("started_at", ""),
            "finished_at": summary.get("finished_at", ""),
            "status": result.get("collector_status", ""),
            "raw_path": "",
            "normalized_path": result.get("normalized_path", ""),
            "scored_path": scored_path,
            "summary_path": summary_path,
            "raw_items_count": 0,
            "normalized_items_count": result.get("items_count", 0),
            "scored_items_count": result.get("items_count", 0),
        })
        stats["crawl_runs"] += 1

        # content items + authors + metrics + dedup + feishu queue
        seen_authors = set()
        for item in scored_items:
            repo.upsert_content_item(conn, item)
            stats["content_items"] += 1

            repo.insert_metrics_history(conn, item)
            stats["metrics_history"] += 1

            repo.upsert_dedup_hash(conn, item)

            # author (deduplicate within this batch)
            author_key = (item.get("platform", ""), item.get("author_id", ""))
            if author_key not in seen_authors and author_key[1]:
                repo.upsert_author(conn, item)
                stats["authors"] += 1
                seen_authors.add(author_key)

            # feishu write queue: enqueue scored items with boom_score > 0
            if item.get("total_boom_score", 0) > 0:
                payload = {
                    "platform": item.get("platform"),
                    "content_id": item.get("content_id"),
                    "title": item.get("title", "")[:100],
                    "content_url": item.get("content_url", ""),
                    "author_name": item.get("author_name", ""),
                    "weighted_engagement": item.get("weighted_engagement", 0),
                    "viral_ratio": item.get("viral_ratio"),
                    "low_follower_high_viral_level": item.get("low_follower_high_viral_level", ""),
                    "total_boom_score": item.get("total_boom_score", 0),
                    "scoring_status": item.get("scoring_status", ""),
                }
                repo.enqueue_feishu_write(conn, "scored_item", item.get("dedup_hash"), payload)
                stats["feishu_queue"] += 1

    conn.commit()
    conn.close()

    print(json.dumps({
        "status": "pass",
        "summary_path": summary_path,
        "pipeline_run_id": summary["pipeline_run_id"],
        "stats": stats,
    }, ensure_ascii=False, indent=2))
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    ingest(args.summary)


if __name__ == "__main__":
    main()
