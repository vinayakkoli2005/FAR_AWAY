"""CCSDS OCM (Orbit Comprehensive Message) parser — TraCSS profile.

Tolerant KVN reader: collects every KEY = VALUE pair (flat), plus the
TRAJ_START..TRAJ_STOP data block. Trajectory epochs may be ISO timestamps or
relative seconds from EPOCH_TZERO (both CCSDS-legal); we detect per line.
Times are returned as seconds from a caller-supplied reference epoch so the
screening engine never touches datetime objects in hot loops.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_ISO_RE = re.compile(r"^\d{4}-\d{2}")


def _parse_time(s: str) -> datetime:
    s = s.strip().replace("Z", "")
    # CCSDS allows yyyy-dddThh:mm:ss (day-of-year); handle both
    if re.match(r"^\d{4}-\d{3}T", s):
        dt = datetime.strptime(s[:8], "%Y-%j").replace(tzinfo=timezone.utc)
        rest = s[9:]
        h, m, sec = rest.split(":")
        return dt.replace(hour=int(h), minute=int(m)) + __import__("datetime").timedelta(
            seconds=float(sec)
        )
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


@dataclass
class OcmEphemeris:
    obj_id: str
    fields: dict[str, str]
    epoch_tzero: datetime
    times_s: np.ndarray        # seconds from ref_epoch
    pos_km: np.ndarray         # (n, 3)
    vel_kms: np.ndarray | None # (n, 3) when TRAJ_TYPE carries velocity
    usable_start_s: float
    usable_stop_s: float
    od_epoch: datetime | None
    source_file: str = ""


def parse_ocm(path: Path | str, ref_epoch: datetime) -> OcmEphemeris:
    fields: dict[str, str] = {}
    data_rows: list[list[float]] = []
    iso_rows: list[tuple[datetime, list[float]]] = []
    in_traj = False

    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("COMMENT"):
                continue
            if line == "TRAJ_START":
                in_traj = True
                continue
            if line == "TRAJ_STOP":
                in_traj = False
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                fields[key.strip()] = val.strip()
                continue
            if in_traj:
                parts = line.split()
                if _ISO_RE.match(parts[0]):
                    iso_rows.append((_parse_time(parts[0]), [float(x) for x in parts[1:7]]))
                else:
                    data_rows.append([float(x) for x in parts[:7]])

    tzero = _parse_time(
        fields.get("EPOCH_TZERO") or fields.get("START_TIME") or fields["USEABLE_START_TIME"]
    )
    t0_offset = (tzero - ref_epoch).total_seconds()

    if iso_rows:
        times = np.array([(t - ref_epoch).total_seconds() for t, _ in iso_rows])
        vals = np.array([v for _, v in iso_rows])
    else:
        arr = np.array(data_rows)
        times = arr[:, 0] + t0_offset
        vals = arr[:, 1:7]

    pos = vals[:, 0:3]
    vel = vals[:, 3:6] if vals.shape[1] >= 6 else None

    def _bound(key: str, default_s: float) -> float:
        if key in fields:
            return (_parse_time(fields[key]) - ref_epoch).total_seconds()
        return default_s

    usable_start = _bound("USEABLE_START_TIME", float(times[0]))
    usable_stop = _bound("USEABLE_STOP_TIME", float(times[-1]))

    od_epoch = None
    if "OD_EPOCH" in fields:
        od_epoch = _parse_time(fields["OD_EPOCH"])

    obj_id = (
        fields.get("OBJECT_DESIGNATOR")
        or fields.get("OBJECT_ID")
        or fields.get("OBJECT_NAME")
        or Path(path).stem
    )
    return OcmEphemeris(
        obj_id=str(obj_id).strip(),
        fields=fields,
        epoch_tzero=tzero,
        times_s=times,
        pos_km=np.ascontiguousarray(pos),
        vel_kms=np.ascontiguousarray(vel) if vel is not None else None,
        usable_start_s=usable_start,
        usable_stop_s=usable_stop,
        od_epoch=od_epoch,
        source_file=str(path),
    )
