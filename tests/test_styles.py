"""Tests for style definitions."""

import pytest

from katachi.styles import STYLES, get_style


@pytest.mark.parametrize("style", STYLES.values(), ids=list(STYLES))
def test_style_values_are_sane(style) -> None:
    assert 0.0 < style.strength < 1.0
    assert 0.0 <= style.controlnet_scale <= 2.0
    assert style.controlnet_conditioning in {"canny", "depth"}
    assert style.display_name and style.description


@pytest.mark.parametrize("style", STYLES.values(), ids=list(STYLES))
def test_prompts_ask_to_preserve_identity(style) -> None:
    for phrase in ("same pot", "same background", "same lighting", "same tree"):
        assert phrase in style.prompt


def test_windswept_exists() -> None:
    assert get_style("windswept").display_name == "Windswept (Fukinagashi)"


def test_unknown_style() -> None:
    with pytest.raises(ValueError, match="Unknown style"):
        get_style("nope")
