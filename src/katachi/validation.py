"""Image checks: file size, format, resolution, blur, and subject size.

Hard problems (too large, wrong format, too small) are errors and block the run.
Soft problems (blurry, tree small in frame) are warnings: shown to the user, never blocking.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = frozenset({"JPEG", "PNG"})

# Variance of the Laplacian on a grayscale image downscaled to BLUR_ANALYSIS_SIZE on its long side.
# Below this the photo is probably out of focus. Tuned on the sample photos; see tests for bounds.
BLUR_THRESHOLD = 60.0
BLUR_ANALYSIS_SIZE = 512

# Warn when the segmented tree + pot covers less than this fraction of the frame.
MIN_SUBJECT_FRACTION = 0.08


@dataclass
class ValidationResult:
    """Outcome of validating an input image."""

    image: Image.Image | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and self.image is not None


def validate_image(
    source: str | Path | bytes,
    *,
    max_upload_mb: int = 10,
    min_resolution: int = 512,
) -> ValidationResult:
    """Validate an uploaded image and return it as an upright RGB image if usable."""
    data = Path(source).read_bytes() if isinstance(source, str | Path) else source
    result = ValidationResult()

    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_upload_mb:
        result.errors.append(f"File is {size_mb:.1f} MB; the limit is {max_upload_mb} MB.")
        return result

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError):
        result.errors.append("This file could not be read as an image. Please upload a JPG or PNG.")
        return result

    if image.format not in ALLOWED_FORMATS:
        result.errors.append(f"{image.format or 'This'} format is not supported. Use JPG or PNG.")
        return result

    image = ImageOps.exif_transpose(image).convert("RGB")
    if min(image.size) < min_resolution:
        result.errors.append(
            f"Image is {image.width}x{image.height}px; the shorter side must be at least "
            f"{min_resolution}px."
        )
        return result

    result.image = image
    if blur_score(image) < BLUR_THRESHOLD:
        result.warnings.append("The photo looks blurry, so results may be less accurate.")
    return result


def blur_score(image: Image.Image) -> float:
    """Variance of the Laplacian (higher means sharper), computed at a fixed analysis size."""
    gray = image.convert("L")
    gray.thumbnail((BLUR_ANALYSIS_SIZE, BLUR_ANALYSIS_SIZE))
    a = np.asarray(gray, dtype=np.float32)
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def subject_fraction(mask: Image.Image) -> float:
    """Fraction of the frame covered by the foreground of a segmentation mask."""
    return float((np.asarray(mask.convert("L")) > 127).mean())


def subject_size_warning(mask: Image.Image) -> str | None:
    """Return a warning if the tree occupies too little of the frame, else None."""
    if subject_fraction(mask) < MIN_SUBJECT_FRACTION:
        return "The tree looks small in the frame. A closer photo will give better results."
    return None
