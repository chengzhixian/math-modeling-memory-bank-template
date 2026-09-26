"""Render the Q1 13x17 row-normalized Ridge contrast matrix."""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/Q1/regmix/mixture_effect_ridge_v0.csv"
OUTPUT = ROOT / "paper/latex/figures/Q1/q1_interaction_heatmap.png"


def blend(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def color(v):
    neutral = (247, 247, 247)
    return blend(neutral, (54, 104, 166) if v < 0 else (191, 67, 66), abs(v))


def main():
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    domains = list(rows[0])[4:21]
    if len(rows) != 13 or len(domains) != 17:
        raise ValueError("expected the published 13-target x 17-domain matrix")
    values = [[float(row[domain]) for domain in domains] for row in rows]
    values = [[v / max(abs(x) for x in row) for v in row] for row in values]
    width, height = 1940, 1050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 23) if font_path.exists() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    x0, y0, cw, ch = 335, 85, 90, 50
    for i, (row, numbers) in enumerate(zip(rows, values)):
        y = y0 + i * ch
        draw.text((12, y + 12), row["target"], fill=(35, 45, 60), font=font)
        for j, value in enumerate(numbers):
            x = x0 + j * cw
            draw.rectangle((x, y, x + cw - 2, y + ch - 2), fill=color(value))
            draw.text((x + 19, y + 12), f"{value:+.2f}",
                      fill="white" if abs(value) > .62 else (35, 45, 60), font=small)
    for j, domain in enumerate(domains):
        label = Image.new("RGBA", (250, 34), (255, 255, 255, 0))
        ImageDraw.Draw(label).text((2, 2), domain, font=small, fill=(35, 45, 60))
        rotated = label.rotate(55, expand=True)
        image.paste(rotated, (x0 + j * cw - 7, y0 + len(rows) * ch + 6), rotated)
    ly = height - 74
    for i in range(201):
        v = -1 + i / 100
        draw.rectangle((x0 + i * 5, ly, x0 + i * 5 + 5, ly + 17), fill=color(v))
    draw.text((x0 - 25, ly + 25), "-1", fill=(35, 45, 60), font=small)
    draw.text((x0 + 495, ly + 25), "0", fill=(35, 45, 60), font=small)
    draw.text((x0 + 995, ly + 25), "+1", fill=(35, 45, 60), font=small)
    draw.text((x0 + 1070, ly + 5), "within-target relative contrast", fill=(35, 45, 60), font=small)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)


if __name__ == "__main__":
    main()
