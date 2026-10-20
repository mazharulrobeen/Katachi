"""Style definitions, fixed prompts, and suitability logic.

Prompts are fixed and tuned per style; users never write prompts. Every prompt asks the model
to keep the same pot, background, lighting, and tree identity. Tested values are recorded in
`docs/adding-a-style.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Conditioning = Literal["canny", "depth"]

PRESERVE = (
    "same tree, same species, same foliage texture and color, same bark, same pot, "
    "same background, same lighting, same camera angle"
)

COMMON_NEGATIVE = (
    "different pot, different background, different species, extra trees, extra pots, "
    "people, hands, text, watermark, cartoon, painting, illustration, blurry, lowres, "
    "deformed, duplicate trunk, floating branches, oversaturated"
)


@dataclass(frozen=True)
class Style:
    """A bonsai style and the generation settings tuned for it."""

    id: str
    display_name: str
    description: str
    prompt: str
    negative_prompt: str
    controlnet_conditioning: Conditioning
    strength: float  # img2img strength, 0-1; higher changes more
    controlnet_scale: float = 0.5  # how strongly the edge/depth map constrains the result
    guidance_scale: float = 7.0


STYLES: dict[str, Style] = {
    s.id: s
    for s in [
        Style(
            id="windswept",
            display_name="Windswept (Fukinagashi)",
            description="Trunk and branches sweep to one side, as if shaped by constant wind.",
            prompt=(
                "professional photo of a windswept fukinagashi bonsai tree, trunk leaning and "
                "all branches sweeping strongly to one side as if shaped by constant wind, "
                f"{PRESERVE}, highly detailed, sharp focus"
            ),
            negative_prompt=f"{COMMON_NEGATIVE}, symmetrical crown, upright formal shape",
            controlnet_conditioning="canny",
            strength=0.55,
            controlnet_scale=0.45,
        ),
    ]
}


def get_style(style_id: str) -> Style:
    """Look up a style by id, with a helpful error for unknown ids."""
    try:
        return STYLES[style_id]
    except KeyError:
        raise ValueError(f"Unknown style {style_id!r}. Options: {sorted(STYLES)}") from None
