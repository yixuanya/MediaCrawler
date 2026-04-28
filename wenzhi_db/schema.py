"""SQLite schema DDL for wenzhi intelligence database."""

TABLES = {
    "crawl_runs": """
CREATE TABLE IF NOT EXISTS crawl_runs (
    run_id          TEXT PRIMARY KEY,
    platform        TEXT NOT NULL,
    source_type     TEXT,
    source_keyword  TEXT,
    started_at      TEXT,
    finished_at     TEXT,
    status          TEXT,
    raw_path        TEXT,
    normalized_path TEXT,
    scored_path     TEXT,
    summary_path    TEXT,
    raw_items_count     INTEGER DEFAULT 0,
    normalized_items_count INTEGER DEFAULT 0,
    scored_items_count  INTEGER DEFAULT 0,
    blockers_json   TEXT DEFAULT '[]',
    risks_json      TEXT DEFAULT '[]',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours'))
)""",

    "content_items": """
CREATE TABLE IF NOT EXISTS content_items (
    dedup_hash              TEXT PRIMARY KEY,
    platform                TEXT NOT NULL,
    content_id              TEXT NOT NULL,
    content_url             TEXT,
    title                   TEXT,
    desc                    TEXT,
    author_id               TEXT,
    sec_author_id           TEXT,
    author_name             TEXT,
    author_profile_url      TEXT,
    author_followers        INTEGER,
    author_followers_status TEXT,
    liked_count             INTEGER DEFAULT 0,
    collected_count         INTEGER DEFAULT 0,
    comment_count           INTEGER DEFAULT 0,
    share_count             INTEGER DEFAULT 0,
    weighted_engagement     REAL DEFAULT 0,
    viral_ratio             REAL,
    low_follower_high_viral_level TEXT,
    total_boom_score        INTEGER DEFAULT 0,
    scoring_status          TEXT,
    recommended_action      TEXT DEFAULT '',
    publish_time            TEXT,
    first_seen_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    last_seen_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    latest_run_id           TEXT,
    raw_json                TEXT
)""",

    "authors": """
CREATE TABLE IF NOT EXISTS authors (
    platform            TEXT NOT NULL,
    author_id           TEXT NOT NULL,
    sec_author_id       TEXT,
    author_name         TEXT,
    author_profile_url  TEXT,
    followers           INTEGER,
    followers_status    TEXT,
    last_enriched_at    TEXT,
    latest_seen_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    raw_json            TEXT,
    PRIMARY KEY (platform, author_id)
)""",

    "content_metrics_history": """
CREATE TABLE IF NOT EXISTS content_metrics_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dedup_hash          TEXT NOT NULL,
    run_id              TEXT NOT NULL,
    liked_count         INTEGER DEFAULT 0,
    collected_count     INTEGER DEFAULT 0,
    comment_count       INTEGER DEFAULT 0,
    share_count         INTEGER DEFAULT 0,
    weighted_engagement REAL DEFAULT 0,
    viral_ratio         REAL,
    total_boom_score    INTEGER DEFAULT 0,
    recorded_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours'))
)""",

    "dedup_hashes": """
CREATE TABLE IF NOT EXISTS dedup_hashes (
    dedup_hash      TEXT PRIMARY KEY,
    platform        TEXT NOT NULL,
    content_id      TEXT NOT NULL,
    first_seen_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    last_seen_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    seen_count      INTEGER DEFAULT 1
)""",

    "pipeline_summaries": """
CREATE TABLE IF NOT EXISTS pipeline_summaries (
    pipeline_run_id         TEXT PRIMARY KEY,
    keyword                 TEXT,
    platforms_json          TEXT,
    status                  TEXT,
    summary_path            TEXT,
    total_items             INTEGER DEFAULT 0,
    total_levels_count_json TEXT,
    top_items_overall_json  TEXT,
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    raw_json                TEXT
)""",

    "feishu_write_queue": """
CREATE TABLE IF NOT EXISTS feishu_write_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type     TEXT NOT NULL,
    dedup_hash      TEXT,
    payload_json    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    retry_count     INTEGER DEFAULT 0,
    last_error      TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours'))
)""",

    "run_logs": """
CREATE TABLE IF NOT EXISTS run_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT,
    level       TEXT NOT NULL DEFAULT 'INFO',
    message     TEXT NOT NULL,
    detail_json TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S+08:00','now','+8 hours'))
)""",
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_content_items_platform ON content_items(platform)",
    "CREATE INDEX IF NOT EXISTS idx_content_items_level ON content_items(low_follower_high_viral_level)",
    "CREATE INDEX IF NOT EXISTS idx_content_items_score ON content_items(total_boom_score DESC)",
    "CREATE INDEX IF NOT EXISTS idx_content_items_run ON content_items(latest_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_dedup ON content_metrics_history(dedup_hash)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_run ON content_metrics_history(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_dedup_platform ON dedup_hashes(platform)",
    "CREATE INDEX IF NOT EXISTS idx_feishu_status ON feishu_write_queue(status)",
    "CREATE INDEX IF NOT EXISTS idx_run_logs_run ON run_logs(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_authors_platform ON authors(platform)",
]
