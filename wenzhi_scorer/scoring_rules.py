"""Scoring rules and constants for 低粉高爆 evaluation."""

# ── Weighted engagement coefficients ─────────────────────────────────────────
# XHS: liked + collected*1.5 + comment*2 + share
XHS_WEIGHTS = {"liked": 1.0, "collected": 1.5, "comment": 2.0, "share": 1.0}
# Douyin: liked + comment*2 + share*2 + collected
DY_WEIGHTS = {"liked": 1.0, "collected": 1.0, "comment": 2.0, "share": 2.0}

# ── 低粉高爆 level thresholds ────────────────────────────────────────────────
# Each tuple: (max_followers, min_engagement, min_viral_ratio, spike_ratio_threshold)
LEVEL_S = {"max_followers": 20000, "min_engagement": 5000, "min_viral_ratio": 0.3, "spike_ratio": 20}
LEVEL_A = {"max_followers": 50000, "min_engagement": 3000, "min_viral_ratio": 0.2, "spike_ratio": 10}
LEVEL_B = {"max_followers": 100000, "min_engagement": 5000, "min_viral_ratio": 0.1, "spike_ratio": 5}
LEVEL_C_MIN_ENGAGEMENT = 1000

# ── Target user keywords ─────────────────────────────────────────────────────
TARGET_USER_KEYWORDS = [
    "女老板", "创业女性", "高知女性", "中年女性", "海外女性",
    "有钱女人", "高净值女性", "妈妈", "女性领导力",
]

# ── Topic reusability keywords ────────────────────────────────────────────────
TOPIC_KEYWORDS = [
    "水晶", "八字", "风水", "能量", "情绪", "失眠", "焦虑",
    "婚姻", "关系", "财富", "事业", "原生家庭", "家庭", "身体", "转运",
]

# ── Conversion keywords ──────────────────────────────────────────────────────
CONVERSION_KEYWORDS = [
    "水晶", "八字", "风水", "能量", "财富", "事业",
    "关系", "情绪", "失眠", "家庭",
]

# ── Comment need thresholds ──────────────────────────────────────────────────
COMMENT_THRESHOLDS = [(500, 15), (100, 10), (30, 6), (10, 3)]

# ── Viral score by level ─────────────────────────────────────────────────────
VIRAL_SCORE_MAP = {"S": 30, "A": 25, "B": 18, "C候选": 12, "淘汰": 0}
