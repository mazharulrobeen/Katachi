"""Background removal behind a swappable `Segmenter` interface.

To add a backend (e.g. SAM), implement `Segmenter` and register it in `SEGMENTERS`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Protocol

from PIL import Image

from katachi.validation import subject_fraction


@dataclass
class SegmentationResult:
    """A foreground mask (tree + pot) and the matching cutout."""

    mask: Image.Image  # mode "L", 255 = foreground
    cutout: Image.Image  # mode "RGBA", background transparent

    @property
    def coverage(self) -> float:
        return subject_fraction(self.mask)


class Segmenter(Protocol):
    """Isolates the tree and pot from the background."""

    name: str

    def segment(self, image: Image.Image) -> SegmentationResult: ...


def result_from_mask(image: Image.Image, mask: Image.Image) -> SegmentationResult:
    """Build a `SegmentationResult` from an RGB image and a foreground mask."""
    mask = mask.convert("L").resize(image.size)
    cutout = image.convert("RGBA")
    cutout.putalpha(mask)
    return SegmentationResult(mask=mask, cutout=cutout)


class RembgSegmenter:
    """U2-Net family background removal via `rembg`. Weights download on first use."""

    name = "rembg"

    def __init__(self, model: str = "u2net") -> None:
        self.model = model
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                from rembg import new_session
            except ImportError as exc:
                raise RuntimeError(
                    "rembg is not installed. Run: pip install -e '.[segment]'"
                ) from exc
            self._session = new_session(self.model)
        return self._session

    def segment(self, image: Image.Image) -> SegmentationResult:
        from rembg import remove

        mask = remove(image.convert("RGB"), session=self._get_session(), only_mask=True)
        return result_from_mask(image, mask)


# Backend name -> factory taking a model name. Add new backends here.
SEGMENTERS: dict[str, Callable[[str], Segmenter]] = {"rembg": RembgSegmenter}


@cache
def get_segmenter(name: str = "rembg", model: str = "u2net") -> Segmenter:
    """Return a cached segmenter instance, so models load once per process."""
    if name not in SEGMENTERS:
        raise ValueError(f"Unknown segmenter {name!r}. Options: {sorted(SEGMENTERS)}")
    return SEGMENTERS[name](model)
