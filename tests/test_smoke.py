"""Phase 0 smoke tests: the package imports and settings load."""

import katachi
from katachi.config import SPECIES_DIR, Settings


def test_version() -> None:
    assert katachi.__version__


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("KATACHI_MAX_UPLOAD_MB", raising=False)
    settings = Settings.from_env()
    assert settings.max_upload_mb >= 1


def test_settings_env_override(monkeypatch) -> None:
    monkeypatch.setenv("KATACHI_MAX_UPLOAD_MB", "5")
    monkeypatch.setenv("KATACHI_SPECIES_MIN_CONFIDENCE", "0.7")
    settings = Settings.from_env()
    assert settings.max_upload_mb == 5
    assert settings.species_min_confidence == 0.7


def test_species_dir_exists() -> None:
    assert SPECIES_DIR.is_dir()
