"""Orchestrates the flow: validate the photo, then isolate the tree and pot.

CLI usage:
    python -m katachi.pipeline --image tree.jpg [--out outdir]
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from katachi.config import EXAMPLES_DIR, Settings
from katachi.segmentation import SegmentationResult, Segmenter, get_segmenter
from katachi.validation import subject_size_warning, validate_image


class InvalidImageError(ValueError):
    """Raised when an input image fails validation; `errors` holds user-facing messages."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(" ".join(errors))
        self.errors = errors


@dataclass
class PipelineResult:
    """Everything produced by one run, for the UI or CLI to display."""

    original: Image.Image
    segmentation: SegmentationResult
    warnings: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)


def run(
    source: str | Path | bytes,
    *,
    settings: Settings | None = None,
    segmenter: Segmenter | None = None,
) -> PipelineResult:
    """Validate the photo and isolate the tree and pot."""
    settings = settings or Settings.from_env()
    segmenter = segmenter or get_segmenter(settings.segmenter, settings.rembg_model)

    start = time.perf_counter()
    checked = validate_image(
        source, max_upload_mb=settings.max_upload_mb, min_resolution=settings.min_resolution
    )
    if not checked.ok:
        raise InvalidImageError(checked.errors)
    warnings = list(checked.warnings)

    segmentation = segmenter.segment(checked.image)
    if warning := subject_size_warning(segmentation.mask):
        warnings.append(warning)

    return PipelineResult(
        original=checked.image,
        segmentation=segmentation,
        warnings=warnings,
        timings={"total": time.perf_counter() - start},
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Isolate the tree and pot in a bonsai photo.")
    parser.add_argument("--image", required=True, type=Path, help="input JPG or PNG")
    parser.add_argument("--out", type=Path, default=EXAMPLES_DIR / "outputs")
    args = parser.parse_args(argv)

    try:
        result = run(args.image)
    except InvalidImageError as exc:
        parser.exit(1, "Image rejected:\n" + "\n".join(f"  - {e}" for e in exc.errors) + "\n")

    for warning in result.warnings:
        print(f"Warning: {warning}")
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{args.image.stem}_cutout.png"
    result.segmentation.cutout.save(path)
    print(
        f"Saved {path} (subject covers {result.segmentation.coverage:.0%} of the frame, "
        f"{result.timings['total']:.1f}s)"
    )


if __name__ == "__main__":
    main()
