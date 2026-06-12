"""Match screened events to the TraCSS answer key and score them.

An event matches a key row when the (unordered) object pair is identical and
|TCA difference| <= tolerance. Each key row can be claimed once (greedy by
TCA proximity) so duplicates count against precision, not for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KeyEvent:
    id_a: str
    id_b: str
    tca_s: float
    miss_km: float | None = None

    @property
    def pair(self) -> frozenset[str]:
        return frozenset((self.id_a, self.id_b))


@dataclass
class MatchReport:
    n_key: int
    n_found: int
    n_matched: int
    recall: float
    precision: float
    f1: float
    tca_errors_s: list[float] = field(default_factory=list)
    miss_errors_km: list[float] = field(default_factory=list)
    missed: list[KeyEvent] = field(default_factory=list)       # false negatives
    spurious: list[KeyEvent] = field(default_factory=list)     # false positives


def match_events(
    found: list[KeyEvent],
    key: list[KeyEvent],
    tca_tol_s: float = 5.0,
) -> MatchReport:
    by_pair: dict[frozenset[str], list[KeyEvent]] = {}
    for k in key:
        by_pair.setdefault(k.pair, []).append(k)

    claimed: set[int] = set()
    n_matched = 0
    tca_errors: list[float] = []
    miss_errors: list[float] = []
    spurious: list[KeyEvent] = []
    matched_key_ids: set[int] = set()

    for f in sorted(found, key=lambda e: e.tca_s):
        candidates = [
            (abs(f.tca_s - k.tca_s), idx, k)
            for idx, k in enumerate(by_pair.get(f.pair, []))
            if id(k) not in matched_key_ids and abs(f.tca_s - k.tca_s) <= tca_tol_s
        ]
        if not candidates:
            spurious.append(f)
            continue
        err, _, best = min(candidates, key=lambda c: c[0])
        matched_key_ids.add(id(best))
        n_matched += 1
        tca_errors.append(f.tca_s - best.tca_s)
        if f.miss_km is not None and best.miss_km is not None:
            miss_errors.append(f.miss_km - best.miss_km)

    missed = [k for k in key if id(k) not in matched_key_ids]
    recall = n_matched / len(key) if key else 1.0
    precision = n_matched / len(found) if found else 1.0
    f1 = (
        2 * recall * precision / (recall + precision)
        if (recall + precision) > 0
        else 0.0
    )
    return MatchReport(
        n_key=len(key),
        n_found=len(found),
        n_matched=n_matched,
        recall=recall,
        precision=precision,
        f1=f1,
        tca_errors_s=tca_errors,
        miss_errors_km=miss_errors,
        missed=missed,
        spurious=spurious,
    )
