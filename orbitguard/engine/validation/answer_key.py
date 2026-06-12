"""Loader for the TraCSS CSieve answer-key CSVs.

Spherical key semantics (User's Guide): one row per conjunction with
obj1 < obj2, miss distance = local minimum within 10 km, TCA strictly inside
the screening window 2025-01-01T12:00 .. 2025-01-08T12:00 UTC.
"""

from __future__ import annotations

import csv
import gzip
from datetime import datetime, timezone
from pathlib import Path

from engine.validation.matching import KeyEvent

SCREEN_WINDOW_START = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
SCREEN_WINDOW_STOP = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)


def _parse_epoch(s: str) -> datetime:
    return datetime.fromisoformat(s.strip()).replace(tzinfo=timezone.utc)


def load_answer_key(
    path: Path | str,
    ref_epoch: datetime = SCREEN_WINDOW_START,
    t_min: float | None = None,
    t_max: float | None = None,
) -> list[KeyEvent]:
    """Returns KeyEvents with tca_s in seconds from ref_epoch.

    t_min/t_max (seconds from ref_epoch) optionally slice the key for
    subset-first runs (e.g. day 1 only).
    """
    opener = gzip.open if str(path).endswith(".gz") else open
    events: list[KeyEvent] = []
    with opener(path, "rt") as f:
        for row in csv.DictReader(f):
            tca_s = (_parse_epoch(row["epoch"]) - ref_epoch).total_seconds()
            if t_min is not None and tca_s < t_min:
                continue
            if t_max is not None and tca_s > t_max:
                continue
            events.append(
                KeyEvent(
                    id_a=row["obj1"].strip(),
                    id_b=row["obj2"].strip(),
                    tca_s=tca_s,
                    miss_km=float(row["min_range"]),
                )
            )
    return events
