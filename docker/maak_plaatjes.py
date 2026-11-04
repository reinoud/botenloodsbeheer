"""Maakt vooraanzichten van boten voor het rekoverzicht: per boottype een 'bezet' en een 'vrij' plaatje.

Draaien vanuit de root van de repository: `uv run python docker/maak_plaatjes.py` (issue #87).
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 128          # eindmaat in pixels (vierkant)
SS = 4              # supersampling voor gladde randen
OUT = Path(__file__).resolve().parent.parent / "app" / "web" / "static" / "boten"

# breedte, diepte romp, vorm bodem (<2 = V, 2 = rond, >2 = vlak), hoogte dek (0 = open boot)
TYPES = {
    "kajak":         {"w": 0.56, "d": 0.22, "n": 1.8, "deck": 0.10},
    "canadese-kano": {"w": 0.84, "d": 0.30, "n": 2.6, "deck": 0.0},
    "surfski":       {"w": 0.32, "d": 0.20, "n": 1.6, "deck": 0.06},
    "wildwaterboot": {"w": 0.58, "d": 0.15, "n": 5.0, "deck": 0.14},
}
COLORS = {
    "bezet": {"hull": "#1f4e79", "line": "#0d2740", "rim": "#0d2740"},
    "vrij":  {"hull": "#d6e6f5", "line": "#8fb3d6", "rim": "#8fb3d6"},
}


def superellipse_half(a, b, n, top, steps=60):
    """Punten van rechts naar links langs de onderste (top=False) of bovenste helft."""
    pts = []
    for i in range(steps + 1):
        t = math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2 / n), c)
        y = b * abs(s) ** (2 / n)
        pts.append((x, -y if top else y))
    return pts


def draw(boot, status):
    p, col = TYPES[boot], COLORS[status]
    S = SIZE * SS
    img = Image.new("RGB", (S, S), "white")
    g = ImageDraw.Draw(img)
    cx = 0.5
    top = p["deck"] + 0.035
    waterline = 0.5 + (top - p["d"]) / 2  # romp verticaal gecentreerd

    def px(pts):
        return [((cx + x) * S, (waterline + y) * S) for x, y in pts]

    a = p["w"] / 2
    bottom = superellipse_half(a, p["d"], p["n"], top=False)       # rechts -> links via onder
    if p["deck"]:
        deck = superellipse_half(a, p["deck"], 2, top=True)[::-1]  # links -> rechts via boven
    else:
        deck = [(-a, 0), (a, 0)]
    hull = px(bottom + deck)

    g.polygon(hull, fill=col["hull"], outline=col["line"])
    g.line(hull + [hull[0]], fill=col["line"], width=3 * SS, joint="curve")

    if p["deck"]:  # kuiprand bovenop het dek
        rw, top = 0.09, waterline - p["deck"]
        g.rounded_rectangle([(cx - rw) * S, (top - 0.035) * S, (cx + rw) * S, (top + 0.01) * S],
                            radius=1.5 * SS, fill=col["rim"])
    else:          # open kano: dolboorden als twee knobbels
        for sx in (-a, a - 0.05):
            g.rounded_rectangle([(cx + sx) * S, (waterline - 0.025) * S, (cx + sx + 0.05) * S, (waterline + 0.015) * S],
                                radius=1.5 * SS, fill=col["rim"])
        g.line([((cx - a + 0.04) * S, waterline * S), ((cx + a - 0.04) * S, waterline * S)],
               fill=col["line"], width=2 * SS)

    return img.resize((SIZE, SIZE), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for boot in TYPES:
        for status in COLORS:
            f = OUT / f"{boot}-{status}.jpg"
            draw(boot, status).save(f, quality=92)
            assert Image.open(f).size == (SIZE, SIZE)
            print(f.name)
