"""Tests for the style catalog."""

import pytest

from katachi.styles import STYLES, get_style


def test_v01_styles_present() -> None:
    assert set(STYLES) == {"informal_upright", "slanting", "windswept"}


@pytest.mark.parametrize("style", STYLES.values(), ids=list(STYLES))
def test_style_text_present(style) -> None:
    assert style.display_name and style.description


def test_get_style() -> None:
    assert get_style("windswept").display_name == "Windswept (Fukinagashi)"


def test_unknown_style() -> None:
    with pytest.raises(ValueError, match="Unknown style"):
        get_style("nope")
