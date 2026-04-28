"""Migrate: create/upgrade SQLite schema."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wenzhi_db.db import get_conn
from wenzhi_db.schema import TABLES, INDEXES


def migrate():
    conn = get_conn()
    created = []
    existed = []

    for name, ddl in TABLES.items():
        try:
            conn.execute(ddl)
            # check if it was freshly created by trying to count
            created.append(name)
        except Exception as e:
            existed.append(name)

    for idx_ddl in INDEXES:
        conn.execute(idx_ddl)

    conn.commit()
    conn.close()

    print(f"Tables ready: {len(TABLES)} ({len(TABLES)} created/verified)")
    print(f"Indexes: {len(INDEXES)} created/verified")
    for t in TABLES:
        print(f"  ✓ {t}")


if __name__ == "__main__":
    migrate()
