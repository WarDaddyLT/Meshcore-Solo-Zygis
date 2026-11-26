#!/usr/bin/env python3
"""Generate Žygis logo mipmaps or exact-size monochrome splash emblems."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


def mip_bitmap(alpha, size):
    coverage = alpha.resize(size, Image.Resampling.BOX)
    bitmap = coverage.convert("1", dither=Image.Dither.NONE)
    if not bitmap.getbbox():
        # Keep one visible pixel if a small level falls entirely below 50%.
        samples = coverage.tobytes()
        strongest = max(samples)
        if strongest:
            row, column = divmod(samples.index(strongest), bitmap.width)
            bitmap.putpixel((column, row), 255)
    return bitmap


def save_contact_sheet(bitmaps, path):
    columns = 4
    cell_width, cell_height = 232, 218
    margin, header = 18, 60
    rows = (len(bitmaps) + columns - 1) // columns
    sheet = Image.new("1", (columns * cell_width + 2 * margin, header + rows * cell_height + margin))
    draw = ImageDraw.Draw(sheet)
    title = ImageFont.load_default(size=25)
    label = ImageFont.load_default(size=17)
    draw.text((margin, 14), "1-bit logo mipmaps", fill=255, font=title)

    for i, bitmap in enumerate(bitmaps):
        column, row = i % columns, i // columns
        x, y = margin + column * cell_width, header + row * cell_height
        preview = bitmap.copy()
        edge = max(bitmap.size)
        if edge < 80:
            zoom = 80 // edge
            preview = bitmap.resize((bitmap.width * zoom, bitmap.height * zoom), Image.Resampling.NEAREST)
        else:
            preview.thumbnail((176, 176), Image.Resampling.NEAREST)
        draw.text((x + 11, y + 8), f"{bitmap.width} x {bitmap.height}", fill=255, font=label)
        sheet.paste(preview, (x + (cell_width - preview.width) // 2, y + 34 + (176 - preview.height) // 2))

    sheet.save(path)


def generate(source_path, output_dir):
    with Image.open(source_path) as image:
        width, height = image.size
        alpha = image.convert("RGBA").getchannel("A")

    levels = []
    bitmaps = []
    pixels = bytearray()
    while True:
        bitmap = mip_bitmap(alpha, (width, height))
        bitmaps.append(bitmap)
        level = bitmap.tobytes()
        levels.append({
            "width": width,
            "height": height,
            "stride_bytes": (width + 7) // 8,
            "offset": len(pixels),
            "length": len(level),
        })
        pixels.extend(level)
        if width == height == 1:
            break
        width, height = max(1, width // 2), max(1, height // 2)

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = "zygis-logo-mipmaps.bin"
    (output_dir / filename).write_bytes(pixels)
    manifest = {
        "file": filename,
        "format": "packed1",
        "layout": "row-major, top-left origin, MSB first, zero pad at row ends",
        "bits": {"0": "background", "1": "foreground"},
        "levels": levels,
    }
    (output_dir / "zygis-logo-mipmaps.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    save_contact_sheet(bitmaps, output_dir / "zygis-logo-mipmaps.png")
    print(f"Wrote {len(levels)} levels, {len(pixels):,} bytes")


def generate_splash_emblems(source_path, output_dir):
    with Image.open(source_path) as image:
        alpha = image.convert("RGBA").getchannel("A")
    visible_bounds = alpha.getbbox()
    if visible_bounds is None:
        raise ValueError("The logo must contain visible pixels")
    alpha = alpha.crop(visible_bounds)
    output_dir.mkdir(parents=True, exist_ok=True)

    for width, height in ((94, 82), (46, 41)):
        scale = min(width / alpha.width, height / alpha.height)
        emblem = mip_bitmap(alpha, (round(alpha.width * scale), round(alpha.height * scale)))
        bitmap = Image.new("1", (width, height))
        bitmap.paste(emblem, ((width - emblem.width) // 2, (height - emblem.height) // 2))

        stem = f"zygis-emblem-{width}x{height}"
        bitmap.save(output_dir / f"{stem}.png")
        gray = bitmap.convert("L").tobytes()
        (output_dir / f"{stem}.gray8").write_bytes(gray)
        print(f"Wrote {stem}.png and {stem}.gray8 ({len(gray):,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs/design/zygis-logo.png")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/design")
    parser.add_argument("--splash", action="store_true", help="export the two firmware splash emblem sizes")
    args = parser.parse_args()
    if args.splash:
        generate_splash_emblems(args.source, args.output_dir)
    else:
        generate(args.source, args.output_dir)
