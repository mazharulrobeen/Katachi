"""Tests for image validation."""

import io

import numpy as np
import pytest
from PIL import Image, ImageFilter

from katachi.validation import (
    BLUR_THRESHOLD,
    blur_score,
    subject_fraction,
    subject_size_warning,
    validate_image,
)


def _encode(image: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def sharp_image() -> Image.Image:
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, (600, 800, 3), dtype=np.uint8))


def test_valid_png(sharp_image: Image.Image) -> None:
    result = validate_image(_encode(sharp_image))
    assert result.ok
    assert result.errors == []
    assert result.warnings == []
    assert result.image.mode == "RGB"


def test_valid_jpeg_from_path(sharp_image: Image.Image, tmp_path) -> None:
    path = tmp_path / "tree.jpg"
    sharp_image.save(path, format="JPEG")
    assert validate_image(path).ok


def test_rejects_oversized_file(sharp_image: Image.Image) -> None:
    result = validate_image(_encode(sharp_image), max_upload_mb=0)
    assert not result.ok
    assert "limit" in result.errors[0]


def test_rejects_non_image() -> None:
    result = validate_image(b"definitely not an image")
    assert not result.ok
    assert "could not be read" in result.errors[0]


def test_rejects_unsupported_format(sharp_image: Image.Image) -> None:
    result = validate_image(_encode(sharp_image, "BMP"))
    assert not result.ok
    assert "not supported" in result.errors[0]


def test_rejects_low_resolution() -> None:
    small = Image.new("RGB", (400, 300), "white")
    result = validate_image(_encode(small), min_resolution=512)
    assert not result.ok
    assert "400x300" in result.errors[0]


def test_applies_exif_orientation(sharp_image: Image.Image) -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees on display
    buf = io.BytesIO()
    sharp_image.save(buf, format="JPEG", exif=exif)
    result = validate_image(buf.getvalue())
    assert result.image.size == (600, 800)


def test_blur_warns_but_does_not_block(sharp_image: Image.Image) -> None:
    blurry = sharp_image.filter(ImageFilter.GaussianBlur(radius=6))
    assert blur_score(blurry) < BLUR_THRESHOLD < blur_score(sharp_image)
    result = validate_image(_encode(blurry))
    assert result.ok
    assert any("blurry" in w for w in result.warnings)


def test_subject_size() -> None:
    mask = Image.new("L", (100, 100), 0)
    assert subject_fraction(mask) == 0.0
    assert subject_size_warning(mask) is not None

    mask.paste(255, (0, 0, 50, 100))
    assert subject_fraction(mask) == pytest.approx(0.5)
    assert subject_size_warning(mask) is None
