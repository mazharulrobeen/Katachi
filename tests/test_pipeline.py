"""Pipeline tests with a fake segmenter (no models downloaded)."""

import io

import numpy as np
import pytest
from PIL import Image

from katachi.config import Settings
from katachi.pipeline import InvalidImageError, main, run
from katachi.segmentation import SegmentationResult, result_from_mask


@pytest.fixture
def photo_bytes() -> bytes:
    rng = np.random.default_rng(1)
    image = Image.fromarray(rng.integers(0, 256, (600, 800, 3), dtype=np.uint8))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


class FakeSegmenter:
    name = "fake"

    def __init__(self, box_fraction: float = 0.5) -> None:
        self.box_fraction = box_fraction

    def segment(self, image: Image.Image) -> SegmentationResult:
        mask = Image.new("L", image.size, 0)
        w, h = image.size
        mask.paste(255, (0, 0, int(w * self.box_fraction), h))
        return result_from_mask(image, mask)


def test_run_returns_segmentation(photo_bytes: bytes) -> None:
    result = run(photo_bytes, settings=Settings(), segmenter=FakeSegmenter())
    assert result.segmentation.coverage == pytest.approx(0.5)
    assert result.segmentation.cutout.mode == "RGBA"
    assert result.segmentation.cutout.size == result.original.size
    assert result.warnings == []
    assert "total" in result.timings


def test_small_subject_warns(photo_bytes: bytes) -> None:
    result = run(photo_bytes, settings=Settings(), segmenter=FakeSegmenter(box_fraction=0.02))
    assert any("small" in w for w in result.warnings)


def test_invalid_image_raises() -> None:
    with pytest.raises(InvalidImageError) as exc:
        run(b"nope", settings=Settings(), segmenter=FakeSegmenter())
    assert exc.value.errors


def test_cli_writes_cutout(photo_bytes: bytes, tmp_path, monkeypatch) -> None:
    image_path = tmp_path / "tree.png"
    image_path.write_bytes(photo_bytes)
    monkeypatch.setattr("katachi.pipeline.get_segmenter", lambda *a: FakeSegmenter())
    main(["--image", str(image_path), "--out", str(tmp_path / "out")])
    assert [p.name for p in (tmp_path / "out").iterdir()] == ["tree_cutout.png"]
