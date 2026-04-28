"""wenzhi_config - Collector layer configuration."""

# Keywords to collect
KEYWORDS = ["女老板 失眠"]

# Max items per keyword per platform
MAX_ITEMS_PER_KEYWORD = 5

# Platforms to collect
PLATFORMS = ["xhs", "douyin"]

# Author enrichment settings
XHS_AUTHOR_ENRICH_SLEEP = 1.5
DOUYIN_AUTHOR_ENRICH_SLEEP = 2.0
DOUYIN_AUTHOR_ENRICH_RETRIES = 1
DOUYIN_AUTHOR_ENRICH_BACKOFF = 3.0
