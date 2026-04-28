"""Repository: all DB read/write operations."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

_TZ = timezone(timedelta(hours=8))


def _now() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


# ── crawl_runs ────────────────────────────────────────────────────────────────

def upsert_crawl_run(conn: sqlite3.Connection, run: dict):
    conn.execute("""
        INSERT INTO crawl_runs (
            run_id, platform, source_type, source_keyword,
            started_at, finished_at, status,
            raw_path, normalized_path, scored_path, summary_path,
            raw_items_count, normalized_items_count, scored_items_count,
            blockers_json, risks_json, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(run_id) DO UPDATE SET
            status=excluded.status,
            scored_path=excluded.scored_path,
            scored_items_count=excluded.scored_items_count,
            finished_at=excluded.finished_at
    """, (
        run["run_id"], run["platform"], run.get("source_type", "keyword_search"),
        run.get("source_keyword", ""), run.get("started_at", ""), run.get("finished_at", ""),
        run.get("status", ""), run.get("raw_path", ""), run.get("normalized_path", ""),
        run.get("scored_path", ""), run.get("summary_path", ""),
        run.get("raw_items_count", 0), run.get("normalized_items_count", 0),
        run.get("scored_items_count", 0),
        json.dumps(run.get("blockers", []), ensure_ascii=False),
        json.dumps(run.get("risks", []), ensure_ascii=False),
        _now(),
    ))


# ── content_items ─────────────────────────────────────────────────────────────

def upsert_content_item(conn: sqlite3.Connection, item: dict):
    now = _now()
    conn.execute("""
        INSERT INTO content_items (
            dedup_hash, platform, content_id, content_url, title, desc,
            author_id, sec_author_id, author_name, author_profile_url,
            author_followers, author_followers_status,
            liked_count, collected_count, comment_count, share_count,
            weighted_engagement, viral_ratio,
            low_follower_high_viral_level, total_boom_score,
            scoring_status, recommended_action, publish_time,
            first_seen_at, last_seen_at, latest_run_id, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(dedup_hash) DO UPDATE SET
            liked_count=excluded.liked_count,
            collected_count=excluded.collected_count,
            comment_count=excluded.comment_count,
            share_count=excluded.share_count,
            weighted_engagement=excluded.weighted_engagement,
            viral_ratio=excluded.viral_ratio,
            low_follower_high_viral_level=excluded.low_follower_high_viral_level,
            total_boom_score=excluded.total_boom_score,
            scoring_status=excluded.scoring_status,
            recommended_action=excluded.recommended_action,
            last_seen_at=excluded.last_seen_at,
            latest_run_id=excluded.latest_run_id,
            raw_json=excluded.raw_json,
            author_followers=COALESCE(excluded.author_followers, content_items.author_followers),
            author_followers_status=excluded.author_followers_status
    """, (
        item["dedup_hash"], item["platform"], item["content_id"],
        item.get("content_url", ""), item.get("title", ""), item.get("desc", ""),
        item.get("author_id", ""), item.get("sec_author_id", ""),
        item.get("author_name", ""), item.get("author_profile_url", ""),
        item.get("author_followers"), item.get("author_followers_status", ""),
        _safe_int(item.get("liked_count")), _safe_int(item.get("collected_count")),
        _safe_int(item.get("comment_count")), _safe_int(item.get("share_count")),
        item.get("weighted_engagement", 0), item.get("viral_ratio"),
        item.get("low_follower_high_viral_level", ""), item.get("total_boom_score", 0),
        item.get("scoring_status", ""), item.get("recommended_action", ""),
        item.get("publish_time", ""),
        now, now, item.get("run_id", ""),
        json.dumps(item, ensure_ascii=False),
    ))


# ── authors ───────────────────────────────────────────────────────────────────

def upsert_author(conn: sqlite3.Connection, item: dict):
    now = _now()
    conn.execute("""
        INSERT INTO authors (
            platform, author_id, sec_author_id, author_name,
            author_profile_url, followers, followers_status,
            last_enriched_at, latest_seen_at, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(platform, author_id) DO UPDATE SET
            author_name=excluded.author_name,
            sec_author_id=COALESCE(excluded.sec_author_id, authors.sec_author_id),
            author_profile_url=excluded.author_profile_url,
            followers=COALESCE(excluded.followers, authors.followers),
            followers_status=excluded.followers_status,
            latest_seen_at=excluded.latest_seen_at
    """, (
        item["platform"], item.get("author_id", ""), item.get("sec_author_id", ""),
        item.get("author_name", ""), item.get("author_profile_url", ""),
        item.get("author_followers"), item.get("author_followers_status", ""),
        now, now,
        json.dumps({
            "author_id": item.get("author_id"),
            "author_name": item.get("author_name"),
            "author_followers": item.get("author_followers"),
        }, ensure_ascii=False),
    ))


# ── content_metrics_history ───────────────────────────────────────────────────

def insert_metrics_history(conn: sqlite3.Connection, item: dict):
    conn.execute("""
        INSERT INTO content_metrics_history (
            dedup_hash, run_id, liked_count, collected_count,
            comment_count, share_count, weighted_engagement,
            viral_ratio, total_boom_score, recorded_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        item["dedup_hash"], item.get("run_id", ""),
        _safe_int(item.get("liked_count")), _safe_int(item.get("collected_count")),
        _safe_int(item.get("comment_count")), _safe_int(item.get("share_count")),
        item.get("weighted_engagement", 0), item.get("viral_ratio"),
        item.get("total_boom_score", 0), _now(),
    ))


# ── dedup_hashes ──────────────────────────────────────────────────────────────

def upsert_dedup_hash(conn: sqlite3.Connection, item: dict):
    now = _now()
    conn.execute("""
        INSERT INTO dedup_hashes (dedup_hash, platform, content_id, first_seen_at, last_seen_at, seen_count)
        VALUES (?,?,?,?,?,1)
        ON CONFLICT(dedup_hash) DO UPDATE SET
            last_seen_at=excluded.last_seen_at,
            seen_count=dedup_hashes.seen_count + 1
    """, (item["dedup_hash"], item["platform"], item["content_id"], now, now))


# ── pipeline_summaries ────────────────────────────────────────────────────────

def insert_pipeline_summary(conn: sqlite3.Connection, summary: dict, summary_path: str):
    conn.execute("""
        INSERT OR REPLACE INTO pipeline_summaries (
            pipeline_run_id, keyword, platforms_json, status,
            summary_path, total_items, total_levels_count_json,
            top_items_overall_json, created_at, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        summary["pipeline_run_id"], summary.get("keyword", ""),
        json.dumps(summary.get("platforms", []), ensure_ascii=False),
        summary.get("status", ""),
        summary_path, summary.get("total_items", 0),
        json.dumps(summary.get("total_levels_count", {}), ensure_ascii=False),
        json.dumps(summary.get("top_items_overall", []), ensure_ascii=False),
        _now(),
        json.dumps(summary, ensure_ascii=False),
    ))


# ── feishu_write_queue ────────────────────────────────────────────────────────

def enqueue_feishu_write(conn: sqlite3.Connection, record_type: str,
                         dedup_hash: Optional[str], payload: dict):
    conn.execute("""
        INSERT INTO feishu_write_queue (record_type, dedup_hash, payload_json, status, created_at, updated_at)
        VALUES (?,?,?,'pending',?,?)
    """, (record_type, dedup_hash, json.dumps(payload, ensure_ascii=False), _now(), _now()))


# ── run_logs ──────────────────────────────────────────────────────────────────

def insert_log(conn: sqlite3.Connection, run_id: str, level: str, message: str,
               detail: Optional[dict] = None):
    conn.execute("""
        INSERT INTO run_logs (run_id, level, message, detail_json, created_at)
        VALUES (?,?,?,?,?)
    """, (run_id, level, message,
          json.dumps(detail, ensure_ascii=False) if detail else None, _now()))


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_int(v) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0
