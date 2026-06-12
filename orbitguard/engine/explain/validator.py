"""Post-validation: reject LLM output containing numbers not in the evidence.

The check is deliberately simple and conservative (plan Section 5.5): every
numeric token in the narration must be derivable from some number in the
evidence record — exact match, rounding to fewer decimals, or a km->m
conversion of a present value. Anything else => reject and fall back to the
deterministic template.
"""

from __future__ import annotations

import math
import re

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
# numbers that prose legitimately introduces (counts, small ordinals, dates handled separately)
_FREE_NUMBERS = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 100.0, 1000.0}


def _collect_numbers(node) -> set[float]:
    out: set[float] = set()
    if isinstance(node, bool):
        return out
    if isinstance(node, (int, float)):
        f = float(node)
        out.add(f)
        out.add(abs(f))
        out.add(f * 1000.0)   # km -> m
        out.add(f / 1000.0)   # m -> km
        return out
    if isinstance(node, str):
        for tok in _NUM_RE.findall(node):
            try:
                f = float(tok)
            except ValueError:
                continue
            out.add(f)
            out.add(abs(f))
        return out
    if isinstance(node, dict):
        for v in node.values():
            out |= _collect_numbers(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            out |= _collect_numbers(v)
    return out


def _is_rounding_of(candidate: float, source: float) -> bool:
    if source == 0.0:
        return candidate == 0.0
    if math.isclose(candidate, source, rel_tol=1e-9, abs_tol=1e-12):
        return True
    # rounding of the source to 0..6 decimals, or to N significant figures
    for nd in range(0, 7):
        if math.isclose(candidate, round(source, nd), rel_tol=1e-9, abs_tol=10.0 ** (-nd) / 2 + 1e-12):
            return True
    exp = math.floor(math.log10(abs(source)))
    for sig in range(1, 4):
        scaled = round(source, -exp + sig - 1)
        if math.isclose(candidate, scaled, rel_tol=1e-9, abs_tol=1e-12):
            return True
    return False


def validate_narration(text: str, evidence: dict) -> tuple[bool, list[str]]:
    """Returns (ok, offending_tokens)."""
    allowed = _collect_numbers(evidence) | _FREE_NUMBERS
    offending: list[str] = []
    for tok in _NUM_RE.findall(text):
        try:
            val = float(tok)
        except ValueError:
            continue
        if any(_is_rounding_of(val, src) for src in allowed):
            continue
        offending.append(tok)
    return (len(offending) == 0, offending)
