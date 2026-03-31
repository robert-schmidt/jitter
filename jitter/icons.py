"""Generate tray icons programmatically. Icons are created once and cached."""

from functools import lru_cache
from PIL import Image, ImageDraw

SIZE = 64


def _circle(color: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 20
    draw.ellipse([margin, margin, SIZE - margin, SIZE - margin], fill=color)
    return img


@lru_cache(maxsize=3)
def active_icon() -> Image.Image:
    return _circle("#22c55e")


@lru_cache(maxsize=3)
def skipping_icon() -> Image.Image:
    return _circle("#f59e0b")


@lru_cache(maxsize=3)
def paused_icon() -> Image.Image:
    return _circle("#9ca3af")
