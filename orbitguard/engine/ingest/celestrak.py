"""CelesTrak GP (OMM JSON) fetcher with hard cache discipline.

CelesTrak refreshes GP data every 2 hours and IP-blocks over-fetchers.
The discipline is enforced in code, not convention: a snapshot younger than
`min_refetch_hours` is always served from cache, and `force` cannot override
a snapshot younger than 30 minutes.

OMM-first policy (plan Section 4.2): we consume JSON OMM records and store
catalog IDs as integers end-to-end. Legacy TLE never enters the pipeline.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from engine.config import SETTINGS, CACHE_DIR

log = logging.getLogger(__name__)

_HARD_FLOOR_HOURS = 0.5  # even force=True will not refetch younger than this


def _snapshot_dir(cache_dir: Path | None = None) -> Path:
    d = (cache_dir or CACHE_DIR) / "celestrak"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _snapshot_path(group: str, ts: float, cache_dir: Path | None = None) -> Path:
    stamp = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _snapshot_dir(cache_dir) / f"gp_{group}_{stamp}.json"


def latest_snapshot(group: str, cache_dir: Path | None = None) -> Path | None:
    files = sorted(_snapshot_dir(cache_dir).glob(f"gp_{group}_*.json"))
    return files[-1] if files else None


def snapshot_age_hours(path: Path) -> float:
    return (time.time() - path.stat().st_mtime) / 3600.0


def load_snapshot(path: Path) -> list[dict]:
    with open(path) as f:
        records = json.load(f)
    if not isinstance(records, list):
        raise ValueError(f"{path} is not a GP JSON array")
    return records


def fetch_group(
    group: str = "active",
    cache_dir: Path | None = None,
    force: bool = False,
) -> tuple[list[dict], Path]:
    """Return (records, snapshot_path), downloading only if the cache is stale."""
    cfg = SETTINGS.celestrak
    existing = latest_snapshot(group, cache_dir)
    if existing is not None:
        age = snapshot_age_hours(existing)
        if age < _HARD_FLOOR_HOURS or (not force and age < cfg.min_refetch_hours):
            log.info("celestrak: serving %s from cache (%.1f h old)", group, age)
            return load_snapshot(existing), existing

    url = f"{cfg.base_url}?GROUP={group}&FORMAT=json"
    log.info("celestrak: downloading %s", url)
    with httpx.Client(timeout=cfg.timeout_s, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        records = resp.json()
    if not isinstance(records, list) or not records:
        raise ValueError(f"unexpected CelesTrak response for group={group!r}")

    path = _snapshot_path(group, time.time(), cache_dir)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(records, f)
    tmp.rename(path)
    log.info("celestrak: cached %d records -> %s", len(records), path.name)
    return records, path
