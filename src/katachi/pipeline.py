"""Orchestrates the full flow: validate, segment, restyle.

CLI usage:
    python -m katachi.pipeline --image tree.jpg --style windswept [--seed 42] [--out outdir]
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from katachi.config import EXAMPLES_DIR, Settings
from katachi.restyle import RestyleBackend, get_restyler
from katachi.segmentation import SegmentationResult, Segmenter, get_segmenter
from katachi.styles import STYLES, get_style
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
    restyled: Image.Image
    style_id: str
    seed: int
    warnings: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)


def run(
    source: str | Path | bytes,
    style_id: str,
    *,
    seed: int | None = None,
    settings: Settings | None = None,
    segmenter: Segmenter | None = None,
    restyler: RestyleBackend | None = None,
) -> PipelineResult:
    """Validate the photo, isolate the tree, and restyle it. A new seed gives a new variation."""
    settings = settings or Settings.from_env()
    style = get_style(style_id)
    seed = random.randrange(2**31) if seed is None else seed
    segmenter = segmenter or get_segmenter(settings.segmenter, settings.rembg_model)
    restyler = restyler or get_restyler(settings)
    timings: dict[str, float] = {}

    start = time.perf_counter()
    checked = validate_image(
        source, max_upload_mb=settings.max_upload_mb, min_resolution=settings.min_resolution
    )
    if not checked.ok:
        raise InvalidImageError(checked.errors)
    warnings = list(checked.warnings)

    t = time.perf_counter()
    segmentation = segmenter.segment(checked.image)
    timings["segment"] = time.perf_counter() - t
    if warning := subject_size_warning(segmentation.mask):
        warnings.append(warning)

    t = time.perf_counter()
    restyled = restyler.restyle(checked.image, style, seed=seed, mask=segmentation.mask)
    timings["restyle"] = time.perf_counter() - t
    timings["total"] = time.perf_counter() - start

    return PipelineResult(
        original=checked.image,
        segmentation=segmentation,
        restyled=restyled,
        style_id=style.id,
        seed=seed,
        warnings=warnings,
        timings=timings,
    )


def before_after(before: Image.Image, after: Image.Image, label_height: int = 40) -> Image.Image:
    """Side-by-side comparison image with 'Before' / 'After' labels."""
    after = after.resize(before.size)
    w, h = before.size
    canvas = Image.new("RGB", (w * 2, h + label_height), "white")
    canvas.paste(before.convert("RGB"), (0, label_height))
    canvas.paste(after.convert("RGB"), (w, label_height))
    draw = ImageDraw.Draw(canvas)
    for x, text in ((0, "Before"), (w, "After")):
        draw.text((x + 12, label_height // 3), text, fill="black")
    return canvas


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Restyle a bonsai photo.")
    parser.add_argument("--image", required=True, type=Path, help="input JPG or PNG")
    parser.add_argument("--style", required=True, choices=sorted(STYLES))
    parser.add_argument("--seed", type=int, default=None, help="fixed seed (default: random)")
    parser.add_argument("--out", type=Path, default=EXAMPLES_DIR / "outputs")
    args = parser.parse_args(argv)

    try:
        result = run(args.image, args.style, seed=args.seed)
    except InvalidImageError as exc:
        parser.exit(1, "Image rejected:\n" + "\n".join(f"  - {e}" for e in exc.errors) + "\n")

    for warning in result.warnings:
        print(f"Warning: {warning}")
    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"{args.image.stem}_{result.style_id}_{result.seed}"
    result.segmentation.cutout.save(args.out / f"{stem}_cutout.png")
    result.restyled.save(args.out / f"{stem}_result.png")
    before_after(result.original, result.restyled).save(args.out / f"{stem}_before_after.png")
    times = ", ".join(f"{k} {v:.1f}s" for k, v in result.timings.items())
    print(f"Saved to {args.out}/{stem}_*.png ({times})")


if __name__ == "__main__":
    main()
