"""Runtime settings loaded from environment variables (see `.env.example`)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = REPO_ROOT / "species"
EXAMPLES_DIR = REPO_ROOT / "examples"


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, "").strip() or default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    """All tunable settings in one place."""

    max_upload_mb: int = 10
    min_resolution: int = 512
    segmenter: str = "rembg"
    rembg_model: str = "u2net"
    species_provider: str = "manual"
    plantnet_api_key: str = field(default="", repr=False)
    species_min_confidence: float = 0.5

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from the environment, loading `.env` if present."""
        load_dotenv()
        return cls(
            max_upload_mb=_env_int("KATACHI_MAX_UPLOAD_MB", cls.max_upload_mb),
            min_resolution=_env_int("KATACHI_MIN_RESOLUTION", cls.min_resolution),
            segmenter=_env_str("KATACHI_SEGMENTER", cls.segmenter),
            rembg_model=_env_str("KATACHI_REMBG_MODEL", cls.rembg_model),
            species_provider=_env_str("KATACHI_SPECIES_PROVIDER", cls.species_provider),
            plantnet_api_key=_env_str("PLANTNET_API_KEY", ""),
            species_min_confidence=_env_float(
                "KATACHI_SPECIES_MIN_CONFIDENCE", cls.species_min_confidence
            ),
        )
