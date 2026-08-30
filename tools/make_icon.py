# -*- coding: utf-8 -*-
"""Uygulama simgesini uret: assets/app.ico + assets/app.png.

Pillow kurulu degilse sessizce cikar - program simgesiz de calisir.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCENT = (91, 141, 239)
FG = (255, 255, 255)
SIZES = [16, 24, 32, 48, 64, 128, 256]


def build(size: int):
    """Tek bir kare simge uret."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1],
                        radius=int(size * 0.22), fill=ACCENT)
    font = None
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(name, int(size * 0.62))
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), "Я", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1]), "Я",
           font=font, fill=FG)
    return img


def main() -> int:
    """Simgeleri diske yaz."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow kurulu degil - simge uretilmedi (program simgesiz calisir).")
        print("Kurmak icin: pip install pillow")
        return 0
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    base = build(256)
    base.save(out / "app.ico", format="ICO", sizes=[(s, s) for s in SIZES])
    base.save(out / "app.png")
    print(f"Uretildi: {out / 'app.ico'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
