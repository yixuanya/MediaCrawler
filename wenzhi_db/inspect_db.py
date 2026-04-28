"""Inspect the SQLite database: summary stats + top items."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wenzhi_db.db import get_conn


def inspect(top_n: int = 10):
    conn = get_conn()
    result = {}

    # total content items
    row = conn.execute("SELECT COUNT(*) AS cnt FROM content_items").fetchone()
    result["total_content_items"] = row["cnt"]

    # platform distribution
    rows = conn.execute("SELECT platform, COUNT(*) AS cnt FROM content_items GROUP BY platform").fetchall()
    result["platform_counts"] = {r["platform"]: r["cnt"] for r in rows}

    # level distribution
    rows = conn.execute("""
        SELECT low_follower_high_viral_level AS level, COUNT(*) AS cnt
        FROM content_items GROUP BY low_follower_high_viral_level
    """).fetchall()
    result["levels_count"] = {r["level"]: r["cnt"] for r in rows}

    # followers_status distribution
    rows = conn.execute("""
        SELECT author_followers_status AS status, COUNT(*) AS cnt
        FROM content_items GROUP BY author_followers_status
    """).fetchall()
    result["followers_status_count"] = {r["status"]: r["cnt"] for r in rows}

    # top N by total_boom_score
    rows = conn.execute("""
        SELECT platform, content_id, title, content_url, author_name,
               weighted_engagement, viral_ratio,
               low_follower_high_viral_level, total_boom_score, scoring_status
        FROM content_items
        ORDER BY total_boom_score DESC
        LIMIT ?
    """, (top_n,)).fetchall()
    result["top_items"] = [dict(r) for r in rows]

    # feishu queue
    row = conn.execute("SELECT COUNT(*) AS cnt FROM feishu_write_queue WHERE status='pending'").fetchone()
    result["feishu_queue_pending"] = row["cnt"]

    # pipeline summaries count
    row = conn.execute("SELECT COUNT(*) AS cnt FROM pipeline_summaries").fetchone()
    result["pipeline_summaries_count"] = row["cnt"]

    # metrics history count
    row = conn.execute("SELECT COUNT(*) AS cnt FROM content_metrics_history").fetchone()
    result["metrics_history_count"] = row["cnt"]

    # authors count
    row = conn.execute("SELECT COUNT(*) AS cnt FROM authors").fetchone()
    result["authors_count"] = row["cnt"]

    conn.close()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    inspect(args.top)


if __name__ == "__main__":
    main()
