"""Bonsai style catalog: the style ids species files may reference, with display text.

The Tree Profile uses this to show which styles suit a species and to label the rest
"not recommended".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    """A bonsai style as shown to the user."""

    id: str
    display_name: str
    description: str


STYLES: dict[str, Style] = {
    s.id: s
    for s in [
        Style(
            id="informal_upright",
            display_name="Informal upright (Moyogi)",
            description="Trunk rises with gentle curves, with the apex roughly above the base.",
        ),
        Style(
            id="slanting",
            display_name="Slanting (Shakan)",
            description="Trunk grows at a clear angle to the soil, leaning to one side.",
        ),
        Style(
            id="windswept",
            display_name="Windswept (Fukinagashi)",
            description="Trunk and branches sweep to one side, as if shaped by constant wind.",
        ),
    ]
}


def get_style(style_id: str) -> Style:
    """Look up a style by id, with a helpful error for unknown ids."""
    try:
        return STYLES[style_id]
    except KeyError:
        raise ValueError(f"Unknown style {style_id!r}. Options: {sorted(STYLES)}") from None
