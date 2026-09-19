from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICON_PNG = ASSETS / "gg_scan_icon.png"
ICON_ICO = ASSETS / "gg_scan.ico"


def remove_white_background(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            whiteness = min(red, green, blue)
            color_spread = max(red, green, blue) - min(red, green, blue)
            if whiteness > 238 and color_spread < 18:
                distance = 255 - whiteness
                new_alpha = max(0, min(alpha, distance * 10))
                pixels[x, y] = (red, green, blue, new_alpha)

    return image


def crop_to_subject(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value > 25 else 0).getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    pad = int(max(width, height) * 0.08)
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(image.width, right + pad)
    bottom = min(image.height, bottom + pad)
    return image.crop((left, top, right, bottom))


def build_icon_canvas(subject: Image.Image) -> Image.Image:
    subject.thumbnail((226, 226), Image.Resampling.LANCZOS)

    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    subject_alpha = subject.getchannel("A")
    shadow_layer = Image.new("RGBA", subject.size, (23, 20, 38, 85))
    shadow_layer.putalpha(subject_alpha.filter(ImageFilter.GaussianBlur(4)))

    x = (256 - subject.width) // 2
    y = (256 - subject.height) // 2
    shadow.alpha_composite(shadow_layer, (x + 4, y + 7))

    canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(subject, (x, y))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="Genereaza iconita GG-Scan dintr-o imagine.")
    parser.add_argument(
        "source",
        type=Path,
        help="Calea catre imaginea sursa. Exemplu: python tools/create_icon.py mascot.avif",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f"Imaginea sursa nu exista: {args.source}")

    ASSETS.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.source)
    transparent = remove_white_background(source)
    subject = crop_to_subject(transparent)
    icon = build_icon_canvas(subject)

    icon.save(ICON_PNG)
    icon.save(ICON_ICO, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(ICON_PNG)
    print(ICON_ICO)


if __name__ == "__main__":
    main()
