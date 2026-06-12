"""Central configuration and physical constants.

All distances km, velocities km/s, times seconds unless noted.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --- Physical constants (WGS-72 values to stay consistent with SGP4) ---
MU_EARTH = 398600.8  # km^3/s^2 (WGS-72, the gravity model SGP4 GP data is fitted to)
R_EARTH = 6378.135  # km equatorial radius (WGS-72)

# --- Paths ---
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("ORBITGUARD_DATA_DIR", PACKAGE_ROOT / "data"))
FIXTURES_DIR = DATA_DIR / "fixtures"
CACHE_DIR = DATA_DIR / "cache"


@dataclass(frozen=True)
class ScreeningConfig:
    """Three-stage sieve parameters (plan Section 5.2)."""

    screen_dist_km: float = 10.0          # D: conjunction screening distance
    stage_a_pad_km: float = 25.0          # drift margin for perigee/apogee gate over the window
    coarse_step_s: float = 30.0           # Stage B grid step
    vrel_max_kms: float = 15.6            # 2 * v_circ(LEO floor) worst-case closing speed
    fine_step_s: float = 1.0              # Stage C bracketing step
    window_days: float = 7.0
    chunk_steps: int = 240                # 2 h of 30 s steps per propagation block
    dedupe_gap_s: float = 60.0            # merge TCA roots closer than this

    @property
    def pair_radius_km(self) -> float:
        """Padded Stage B radius: no true conjunction < D can evade the coarse net.

        If a miss < D occurs at t*, the nearest grid point is within dt/2, and the
        pair separates by at most vrel_max * dt/2 — so grid separation < D + that pad.
        """
        return self.screen_dist_km + self.vrel_max_kms * self.coarse_step_s / 2.0


@dataclass(frozen=True)
class RiskConfig:
    """Pc thresholds anchored to the NASA CA Handbook (plan Section 5.4)."""

    pc_dodge: float = 1e-4                # maneuver-consideration threshold
    pc_watch: float = 1e-6                # monitoring band floor
    escalation_miss_km: float = 5.0       # TLE-grade: PcMax high AND this close => ESCALATE
    low_vrel_kms: float = 0.1             # below this, 2D-Pc assumptions invalid
    default_hbr_m: float = 20.0           # combined hard-body radius when sizes unknown


@dataclass(frozen=True)
class CelestrakConfig:
    base_url: str = "https://celestrak.org/NORAD/elements/gp.php"
    min_refetch_hours: float = 2.0        # CelesTrak refresh cadence — never poll faster
    timeout_s: float = 60.0


@dataclass(frozen=True)
class GroqConfig:
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"
    fallback_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_output_tokens: int = 400
    timeout_s: float = 30.0

    @property
    def api_key(self) -> str | None:
        return os.environ.get("GROQ_API_KEY")


@dataclass(frozen=True)
class Settings:
    screening: ScreeningConfig = field(default_factory=ScreeningConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    celestrak: CelestrakConfig = field(default_factory=CelestrakConfig)
    groq: GroqConfig = field(default_factory=GroqConfig)


SETTINGS = Settings()
