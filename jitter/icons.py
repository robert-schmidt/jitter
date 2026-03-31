"""Generate tray icons programmatically."""

from PIL import Image, ImageDraw

SIZE = 64


def _circle(color: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 20
    draw.ellipse([margin, margin, SIZE - margin, SIZE - margin], fill=color)
    return img


def active_icon() -> Image.Image:
    return _circle("#22c55e")


def skipping_icon() -> Image.Image:
    return _circle("#f59e0b")


def paused_icon() -> Image.Image:
    return _circle("#9ca3af")
