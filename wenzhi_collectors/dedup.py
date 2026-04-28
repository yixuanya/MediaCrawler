"""Deduplication utilities."""
import hashlib
from typing import List
from .schemas import NormalizedItem


def make_dedup_hash(platform: str, content_id: str) -> str:
    return hashlib.sha256(f"{platform}:{content_id}".encode()).hexdigest()[:16]


def dedup_items(items: List[NormalizedItem]) -> tuple[List[NormalizedItem], int]:
    """Return (unique_items, removed_count)."""
    seen: set = set()
    unique: List[NormalizedItem] = []
    for item in items:
        if item.dedup_hash in seen:
            continue
        seen.add(item.dedup_hash)
        unique.append(item)
    return unique, len(items) - len(unique)
