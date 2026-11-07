"""Meet de plaatjes van het rekoverzicht (issue #155): contrast van wat de toestand draagt, tegen de
celachtergronden, op het weergaveformaat van de cel (56 px). Draaien: `python -m tests.unit.meet_plaatjes [map]`."""
import statistics
import sys
from pathlib import Path

from PIL import Image

ACHTERGRONDEN = {"surface-raised": "#FFFFFF", "surface": "#F7FAFC"}  # cel en hoverkleur van de cel
WEERGAVE = 56
BOTEN = Path(__file__).resolve().parents[2] / "app" / "web" / "static" / "boten"


def luminantie(rgb):
    def kanaal(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (kanaal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminantie(a), luminantie(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def minimaal_contrast(rgb):
    return min(contrast(rgb, hex_rgb(h)) for h in ACHTERGRONDEN.values())


def runs(lijn, donker):
    """De stukken opeenvolgende donkere pixels in een rij of kolom, als lijsten pixels."""
    stuk = []
    for px in lijn:
        if donker(px):
            stuk.append(px)
        elif stuk:
            yield stuk
            stuk = []
    if stuk:
        yield stuk


def meet(pad):
    """Geeft {'rand': contrast van de rand, 'dikte': mediane lijndikte in pixels, 'midden': kleur van het midden}."""
    foto = Image.open(pad).convert("RGB").resize((WEERGAVE, WEERGAVE), Image.LANCZOS)
    pix = foto.load()
    rijen = [[pix[x, y] for x in range(WEERGAVE)] for y in range(WEERGAVE)]
    kolommen = [[pix[x, y] for y in range(WEERGAVE)] for x in range(WEERGAVE)]
    donker = lambda px: luminantie(px) < 0.5  # onder de helft tussen vulling en rand
    sterk = lambda px: minimaal_contrast(px) >= 3
    stukken = [s for lijn in rijen + kolommen for s in runs(lijn, donker)]
    donkerste = sorted(minimaal_contrast(min(s, key=luminantie)) for s in stukken)
    dikte = [len(s) for lijn in rijen + kolommen for s in runs(lijn, sterk)]
    return {"rand": donkerste[len(donkerste) // 10], "dikte": statistics.median(dikte) if dikte else 0,
            "midden": pix[WEERGAVE // 2, WEERGAVE // 2]}


if __name__ == "__main__":
    for bestand in sorted(Path(sys.argv[1] if len(sys.argv) > 1 else BOTEN).glob("*.jpg")):
        m = meet(bestand)
        print(f"{bestand.name:28} rand {m['rand']:5.1f}:1  dikte {m['dikte']:3.1f}px  midden {m['midden']}")
