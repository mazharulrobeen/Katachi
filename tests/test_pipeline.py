"""Pipeline and restyle helper tests with fake backends (no models, no GPU)."""

import io

import numpy as np
import pytest
from PIL import Image

from katachi.config import Settings
from katachi.pipeline import InvalidImageError, before_after, main, run
from katachi.restyle import composite_background, fit_to_model
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


class FakeRestyler:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def restyle(self, image, style, *, seed, mask=None):
        self.calls.append({"style": style.id, "seed": seed, "mask": mask})
        return Image.new("RGB", image.size, "green")


def test_run_returns_all_outputs(photo_bytes: bytes) -> None:
    restyler = FakeRestyler()
    result = run(
        photo_bytes,
        "windswept",
        seed=7,
        settings=Settings(),
        segmenter=FakeSegmenter(),
        restyler=restyler,
    )
    assert result.restyled.size == result.original.size
    assert result.segmentation.coverage == pytest.approx(0.5)
    assert result.seed == 7
    assert result.warnings == []
    assert restyler.calls[0]["style"] == "windswept"
    assert restyler.calls[0]["mask"] is not None
    assert {"segment", "restyle", "total"} <= result.timings.keys()


def test_random_seed_when_not_given(photo_bytes: bytes) -> None:
    kwargs = {"settings": Settings(), "segmenter": FakeSegmenter(), "restyler": FakeRestyler()}
    seeds = {run(photo_bytes, "windswept", **kwargs).seed for _ in range(5)}
    assert len(seeds) > 1


def test_small_subject_warns(photo_bytes: bytes) -> None:
    result = run(
        photo_bytes,
        "windswept",
        settings=Settings(),
        segmenter=FakeSegmenter(box_fraction=0.02),
        restyler=FakeRestyler(),
    )
    assert any("small" in w for w in result.warnings)


def test_invalid_image_raises() -> None:
    with pytest.raises(InvalidImageError) as exc:
        run(b"nope", "windswept", settings=Settings(), segmenter=FakeSegmenter(),
            restyler=FakeRestyler())  # fmt: skip
    assert exc.value.errors


def test_unknown_style_raises(photo_bytes: bytes) -> None:
    with pytest.raises(ValueError, match="Unknown style"):
        run(photo_bytes, "cascade", settings=Settings(), segmenter=FakeSegmenter(),
            restyler=FakeRestyler())  # fmt: skip


def test_fit_to_model_multiples_of_8() -> None:
    out = fit_to_model(Image.new("RGB", (1000, 750)), 768)
    assert max(out.size) == 768
    assert all(d % 8 == 0 for d in out.size)


def test_composite_keeps_background() -> None:
    original = Image.new("RGB", (200, 200), "blue")
    generated = Image.new("RGB", (200, 200), "red")
    mask = Image.new("L", (200, 200), 0)
    mask.paste(255, (80, 80, 120, 120))
    out = composite_background(original, generated, mask)
    assert out.getpixel((2, 2)) == (0, 0, 255)  # far corner: original background
    assert out.getpixel((100, 100)) == (255, 0, 0)  # tree centre: generated


def test_before_after_layout() -> None:
    combo = before_after(Image.new("RGB", (100, 80)), Image.new("RGB", (50, 40)))
    assert combo.size == (200, 120)


def test_cli_writes_outputs(photo_bytes: bytes, tmp_path, monkeypatch) -> None:
    image_path = tmp_path / "tree.png"
    image_path.write_bytes(photo_bytes)
    monkeypatch.setattr("katachi.pipeline.get_segmenter", lambda *a: FakeSegmenter())
    monkeypatch.setattr("katachi.pipeline.get_restyler", lambda s: FakeRestyler())
    main(["--image", str(image_path), "--style", "windswept", "--seed", "3", "--out",
          str(tmp_path / "out")])  # fmt: skip
    names = sorted(p.name for p in (tmp_path / "out").iterdir())
    assert names == [
        "tree_windswept_3_before_after.png",
        "tree_windswept_3_cutout.png",
        "tree_windswept_3_result.png",
    ]
