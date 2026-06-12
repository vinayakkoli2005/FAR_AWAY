"""Groq explanation client with cache and deterministic fallback.

Free-tier budget discipline (verified limits: 30 RPM / 1K RPD / 12K TPM /
100K TPD): explanations are generated lazily, cached in SQLite keyed by
(pair, TCA minute, verdict, grade), and every failure path — no key, network
error, rate limit, post-validation rejection — lands on the template
renderer. The explainer is decorative to correctness by design.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import httpx

from engine.config import SETTINGS, CACHE_DIR
from engine.explain.prompts import SYSTEM_PROMPT, user_prompt
from engine.explain.templates import render_explanation
from engine.explain.validator import validate_narration

log = logging.getLogger(__name__)


@dataclass
class Explanation:
    text: str
    source: str          # "groq" | "template" | "cache"
    model: str | None = None
    rejected_tokens: list[str] | None = None


def _cache_key(evidence: dict) -> str:
    tca_minute = evidence["tca_utc"][:16]  # YYYY-MM-DDTHH:MM
    return "|".join(
        [
            str(evidence["asset"]["norad_id"]),
            str(evidence["object"]["norad_id"]),
            tca_minute,
            evidence["verdict"],
            evidence["data_grade"],
        ]
    )


class ExplanationCache:
    def __init__(self, path: Path | None = None):
        self.path = path or (CACHE_DIR / "explanations.sqlite")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS explanations "
                "(key TEXT PRIMARY KEY, text TEXT, source TEXT, model TEXT)"
            )

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def get(self, key: str) -> Explanation | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT text, source, model FROM explanations WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return None
        return Explanation(text=row[0], source="cache", model=row[2])

    def put(self, key: str, exp: Explanation) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT OR REPLACE INTO explanations VALUES (?,?,?,?)",
                (key, exp.text, exp.source, exp.model),
            )


def _call_groq(evidence: dict, model: str) -> str:
    cfg = SETTINGS.groq
    resp = httpx.post(
        f"{cfg.base_url}/chat/completions",
        headers={"Authorization": f"Bearer {cfg.api_key}"},
        json={
            "model": model,
            "max_tokens": cfg.max_output_tokens,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(json.dumps(evidence, indent=1))},
            ],
        },
        timeout=cfg.timeout_s,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def explain(evidence: dict, cache: ExplanationCache | None = None) -> Explanation:
    """Best-effort LLM narration; guaranteed to return something usable."""
    cache = cache or ExplanationCache()
    key = _cache_key(evidence)
    cached = cache.get(key)
    if cached is not None:
        return cached

    cfg = SETTINGS.groq
    if cfg.api_key:
        for model in (cfg.model, cfg.fallback_model):
            try:
                text = _call_groq(evidence, model)
            except Exception as exc:  # rate limit, network, 5xx — all land on fallback
                log.warning("groq call failed (%s): %s", model, exc)
                continue
            ok, offending = validate_narration(text, evidence)
            if ok:
                exp = Explanation(text=text, source="groq", model=model)
                cache.put(key, exp)
                return exp
            log.warning("groq narration rejected, hallucinated numbers: %s", offending)
            exp = Explanation(
                text=render_explanation(evidence),
                source="template",
                rejected_tokens=offending,
            )
            cache.put(key, exp)
            return exp

    exp = Explanation(text=render_explanation(evidence), source="template")
    cache.put(key, exp)
    return exp
