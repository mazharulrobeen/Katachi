"""Restyle generation behind a swappable `RestyleBackend` interface.

The default backend runs Stable Diffusion 1.5 img2img guided by a ControlNet (canny edges or
depth) through Hugging Face `diffusers`. Models load lazily on first use and are cached.
After generation, the original background is composited back outside a dilated tree mask so
the scene stays identical and only the tree (and its immediate surroundings) can change.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import numpy as np
from PIL import Image, ImageFilter

from katachi.config import Settings
from katachi.styles import Conditioning, Style

# Fraction of the image's long side to grow the mask by before compositing, so restyled
# branches have room to extend past the original silhouette.
MASK_GROW_FRACTION = 0.08
MASK_FEATHER_FRACTION = 0.02


class RestyleBackend(Protocol):
    """Turns a photo of a tree into the same tree in a different style."""

    name: str

    def restyle(
        self, image: Image.Image, style: Style, *, seed: int, mask: Image.Image | None = None
    ) -> Image.Image: ...


def select_device(preference: str = "auto") -> str:
    """Pick the torch device: CUDA, then Apple MPS, then CPU (slow)."""
    if preference != "auto":
        return preference
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def fit_to_model(image: Image.Image, max_side: int) -> Image.Image:
    """Resize so the long side is `max_side` and both sides are multiples of 8."""
    scale = max_side / max(image.size)
    w, h = (max(8, round(d * scale / 8) * 8) for d in image.size)
    return image.convert("RGB").resize((w, h), Image.LANCZOS)


def canny_map(image: Image.Image, low: int = 100, high: int = 200) -> Image.Image:
    """Canny edge map as a 3-channel image for the canny ControlNet."""
    import cv2

    edges = cv2.Canny(np.asarray(image.convert("L")), low, high)
    return Image.fromarray(np.stack([edges] * 3, axis=-1))


def composite_background(
    original: Image.Image, generated: Image.Image, mask: Image.Image
) -> Image.Image:
    """Keep the original pixels outside a grown, feathered tree mask."""
    generated = generated.resize(original.size, Image.LANCZOS)
    long_side = max(original.size)
    grow = max(3, int(long_side * MASK_GROW_FRACTION)) | 1  # MaxFilter needs an odd size
    soft = (
        mask.convert("L")
        .resize(original.size)
        .filter(ImageFilter.MaxFilter(min(grow, 255)))
        .filter(ImageFilter.GaussianBlur(long_side * MASK_FEATHER_FRACTION))
    )
    return Image.composite(generated, original.convert("RGB"), soft)


class DiffusersRestyler:
    """SD 1.5 img2img + ControlNet via `diffusers`. Weights download on first use."""

    name = "diffusers"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.device = select_device(settings.device)
        self._base = None
        self._pipes: dict[Conditioning, object] = {}
        self._depth_estimator = None

    @property
    def _dtype(self):
        import torch

        return torch.float32 if self.device == "cpu" else torch.float16

    def _controlnet_id(self, conditioning: Conditioning) -> str:
        return {
            "canny": self.settings.controlnet_canny_model,
            "depth": self.settings.controlnet_depth_model,
        }[conditioning]

    def _pipeline(self, conditioning: Conditioning):
        """Load (once) the pipeline for a conditioning type, sharing the base model weights."""
        if conditioning in self._pipes:
            return self._pipes[conditioning]
        try:
            from diffusers import (
                ControlNetModel,
                StableDiffusionControlNetImg2ImgPipeline,
                UniPCMultistepScheduler,
            )
        except ImportError as exc:
            raise RuntimeError(
                "diffusers is not installed. Run: pip install -e '.[restyle]'"
            ) from exc

        controlnet = ControlNetModel.from_pretrained(
            self._controlnet_id(conditioning), torch_dtype=self._dtype
        )
        if self._base is None:
            pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                self.settings.sd_model,
                controlnet=controlnet,
                torch_dtype=self._dtype,
                variant=None if self.device == "cpu" else "fp16",  # half-size download
            )
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
            pipe.set_progress_bar_config(disable=True)
            pipe = pipe.to(self.device)
            if self.device == "mps":
                pipe.enable_attention_slicing()
            self._base = pipe
        else:
            pipe = StableDiffusionControlNetImg2ImgPipeline(
                **{**self._base.components, "controlnet": controlnet.to(self.device)}
            )
            pipe.set_progress_bar_config(disable=True)
        self._pipes[conditioning] = pipe
        return pipe

    def control_image(self, image: Image.Image, conditioning: Conditioning) -> Image.Image:
        """Build the ControlNet conditioning image for `image`."""
        if conditioning == "canny":
            return canny_map(image)
        if self._depth_estimator is None:
            from transformers import pipeline

            self._depth_estimator = pipeline(
                "depth-estimation", model=self.settings.depth_estimator_model
            )
        depth = self._depth_estimator(image)["depth"]
        return depth.convert("RGB").resize(image.size)

    def restyle(
        self, image: Image.Image, style: Style, *, seed: int, mask: Image.Image | None = None
    ) -> Image.Image:
        import torch

        work = fit_to_model(image, self.settings.max_side)
        pipe = self._pipeline(style.controlnet_conditioning)
        generated = pipe(
            prompt=style.prompt,
            negative_prompt=style.negative_prompt,
            image=work,
            control_image=self.control_image(work, style.controlnet_conditioning),
            strength=style.strength,
            controlnet_conditioning_scale=style.controlnet_scale,
            guidance_scale=style.guidance_scale,
            num_inference_steps=self.settings.num_inference_steps,
            generator=torch.Generator(device="cpu").manual_seed(seed),
        ).images[0]
        if mask is None:
            return generated.resize(image.size, Image.LANCZOS)
        return composite_background(image, generated, mask)


# Backend name -> factory taking settings. Add new backends (e.g. a hosted API) here.
RESTYLERS: dict[str, Callable[[Settings], RestyleBackend]] = {"diffusers": DiffusersRestyler}

_instances: dict[str, RestyleBackend] = {}


def get_restyler(settings: Settings) -> RestyleBackend:
    """Return a cached restyle backend so models stay loaded between runs."""
    name = settings.restyle_backend
    if name not in RESTYLERS:
        raise ValueError(f"Unknown restyle backend {name!r}. Options: {sorted(RESTYLERS)}")
    if name not in _instances:
        _instances[name] = RESTYLERS[name](settings)
    return _instances[name]
