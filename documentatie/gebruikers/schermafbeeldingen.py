"""Maakt de schermafbeeldingen van de handleiding, in de container botenloods-e2e (Playwright).
Wordt aangeroepen door schermafbeeldingen.sh met een fase: import, opzeggers of schermen.
Alleen synthetische gegevens. Geheimen (TOTP-sleutel, QR-code, uitnodigingscode) worden vóór
elke opname uit het scherm gehaald."""

import json
import os
import struct
import sys
import time
import urllib.request
import zlib
from datetime import date, timedelta
from pathlib import Path

import pyotp
from playwright.sync_api import expect, sync_playwright

BASIS = "http://localhost:8080"
API = "http://localhost:8081/api/v1"
UIT = Path("/documentatie/gebruikers/afbeeldingen")
LEDEN = json.loads(Path("/fixtures/leden.json").read_text(encoding="utf-8"))
WACHTWOORD = "voorbeeld wachtwoord voor de loods"


def importeren(leden):
    verzoek = urllib.request.Request(
        f"{API}/leden", data=json.dumps({"leden": leden}).encode(), method="PUT",
        headers={"Authorization": f"Bearer {os.environ['DOC_TOKEN']}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(verzoek, timeout=60) as r:
        assert r.status == 200


def opzeggers():
    """Drie leden met een boot op een plaats zeggen over 20, 45 en 90 dagen op."""
    nummers = os.environ["DOC_OPZEGGERS"].split(",")
    for lid, dagen in zip((l for l in LEDEN if l["lidnummer"] in nummers), (20, 45, 90)):
        lid["opzegdatum"] = (date.today() + timedelta(days=dagen)).isoformat()
    importeren(LEDEN)


def foto():
    """Een kleine, geldige PNG met water en lucht, zonder Pillow (het image heeft het niet)."""
    breedte, hoogte = 480, 300
    def blok(soort, data):
        return (struct.pack(">I", len(data)) + soort + data
                + struct.pack(">I", zlib.crc32(soort + data)))
    rijen = b"".join(b"\x00" + (bytes((150, 200, 235)) if y < 150 else bytes((40, 100, 160)))
                     * breedte for y in range(hoogte))
    return (b"\x89PNG\r\n\x1a\n"
            + blok(b"IHDR", struct.pack(">IIBBBBB", breedte, hoogte, 8, 2, 0, 0, 0))
            + blok(b"IDAT", zlib.compress(rijen)) + blok(b"IEND", b""))


class Opnamen:
    def __init__(self, page):
        self.page = page

    def maak(self, naam, hoogte=None, element=None):
        """Eerste scherm van de pagina (hooguit `hoogte` pixels), of alleen `element`."""
        UIT.mkdir(parents=True, exist_ok=True)
        pad = UIT / f"{naam}.png"
        if element is not None:
            element.screenshot(path=pad)
        elif hoogte:
            self.page.screenshot(path=pad, full_page=True,
                                 clip={"x": 0, "y": 0, "width": 1100, "height": hoogte})
        else:
            self.page.screenshot(path=pad, full_page=True)


def verberg_geheimen(page):
    """QR-code en sleutel zijn een TOTP-geheim; de uitnodigingslink bevat de eenmalige code."""
    page.evaluate("""() => {
        const qr = document.querySelector('img.qr');
        if (qr) { const b = qr.getBoundingClientRect(); qr.removeAttribute('src'); qr.alt = '';
          qr.style.cssText = `width:${b.width}px;height:${b.height}px;background:#ddd;display:block`; }
        const sleutel = document.querySelector('#totp-geheim');
        if (sleutel) sleutel.textContent = 'ABCD EFGH IJKL MNOP';
        const link = document.querySelector('#uitnodigingslink');
        if (link) link.textContent = link.textContent.replace(/\\/uitnodiging\\/.*/, '/uitnodiging/<code>');
    }""")


def nieuwe_code(totp, vorige):
    """Een code die de server nog niet kent: wacht tot de stap van 30 seconden is omgeslagen."""
    while totp.now() == vorige:
        time.sleep(1)
    return totp.now()


def schermen(browser):
    ctx = browser.new_context(base_url=BASIS, viewport={"width": 1100, "height": 800},
                              locale="nl-NL", timezone_id="Europe/Amsterdam")
    page = ctx.new_page()
    foto_bytes = foto()

    # Account instellen met een wachtwoord en TOTP.
    page.goto(os.environ["DOC_LINK"])
    totp = pyotp.TOTP(page.locator("#totp-geheim").inner_text())
    eerste = totp.now()
    page.get_by_label("Wachtwoord (12 tot 128 tekens)").fill(WACHTWOORD)
    page.get_by_label("Wachtwoord nog een keer").fill(WACHTWOORD)
    page.get_by_label("Code van zes cijfers uit de app").fill("123456")
    verberg_geheimen(page)
    Opnamen(page).maak("uitnodiging")
    page.get_by_label("Code van zes cijfers uit de app").fill(eerste)
    page.get_by_role("button", name="Wachtwoord instellen").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")
    ctx.close()

    # Inloggen, zoals een beheerder het doet. Deze sessie blijft voor de rest.
    ctx = browser.new_context(base_url=BASIS, viewport={"width": 1100, "height": 800},
                              locale="nl-NL", timezone_id="Europe/Amsterdam")
    page = ctx.new_page()
    o = Opnamen(page)
    page.goto("/inloggen")
    o.maak("inloggen")
    page.get_by_label("Gebruikersnaam").fill("beheerder.een")
    page.get_by_label("Wachtwoord", exact=True).fill(WACHTWOORD)
    page.get_by_role("button", name="Verder").click()
    o.maak("code")
    page.get_by_label("Code van zes cijfers").fill(nieuwe_code(totp, eerste))
    page.get_by_role("button", name="Inloggen").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")

    # Beheerders.
    page.goto("/beheerders")
    page.get_by_label("Gebruikersnaam (a-z, cijfers, punt, - en _)").fill("beheerder.twee")
    page.get_by_role("button", name="Uitnodigen").click()
    verberg_geheimen(page)
    o.maak("uitnodiging-link", hoogte=400)
    page.goto("/beheerders")
    o.maak("beheerders", hoogte=700)
    page.goto("/profiel")
    o.maak("profiel", hoogte=700)

    # Indeling.
    page.goto("/indeling")
    o.maak("indeling", hoogte=900)
    sectie = page.locator("section.kaart", has=page.get_by_role("heading", name="Rek J"))
    sectie.get_by_text("Plaats toevoegen aan Rek J").click()
    o.maak("plaats-toevoegen", element=sectie.locator("details").first)

    # Plaatsen: een bezette en een vrije.
    page.goto("/opzeggend")
    page.locator("tbody tr").first.get_by_role("link").last.click()
    o.maak("plaats-bezet", hoogte=1000)
    page.goto("/vrij")
    page.locator("tbody tr").first.get_by_role("link").click()
    o.maak("plaats-vrij", hoogte=900)
    vrije_plaats = page.url

    # Boten: nieuwe boot met foto, daarna toewijzen aan de vrije plaats.
    page.goto("/boten")
    page.get_by_label("Naam van de boot").fill("Zwaluw 7")
    page.get_by_label("Bootsoort").select_option(label="Kajak")
    page.get_by_label("Eigenaar").select_option(index=3)
    page.get_by_label("Foto (JPEG, PNG of WebP, niet verplicht)").set_input_files(
        {"name": "zwaluw.png", "mimeType": "image/png", "buffer": foto_bytes})
    o.maak("boten", hoogte=900)
    page.get_by_role("button", name="Boot vastleggen").click()
    expect(page.get_by_text("De boot is vastgelegd.")).to_be_visible()
    o.maak("boot", hoogte=1000)
    page.goto(vrije_plaats)
    kies = page.locator("#boot option", has_text="Zwaluw 7").get_attribute("value")
    page.get_by_label("Boot zonder plaats").select_option(value=kies)
    page.get_by_role("button", name="Plaats toewijzen").click()
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    o.maak("plaats-toegewezen", hoogte=1000)
    openbaar = page.locator("#openbare-link").get_attribute("href")

    # Overzichten.
    page.goto("/vrij")
    page.get_by_label("Geschikt voor").select_option(label="Kajak")
    page.get_by_role("button", name="Filteren").click()
    o.maak("vrij", hoogte=700)
    page.goto("/opgezegd")
    o.maak("opgezegd", hoogte=600)
    page.goto("/opzeggend")
    o.maak("opzeggend", hoogte=600)

    # Leden en import.
    page.goto("/leden")
    page.get_by_role("button", name="Leden nu ophalen").click()
    expect(page.get_by_text("De import is aangevraagd.")).to_be_visible()
    o.maak("leden", hoogte=800)

    page.goto("/log")
    o.maak("log", hoogte=700)
    page.goto("/instellingen")
    o.maak("instellingen", hoogte=800)

    # De openbare pagina, zonder inloggen.
    bezoeker = browser.new_context(base_url=BASIS, viewport={"width": 700, "height": 600},
                                   locale="nl-NL")
    pagina = bezoeker.new_page()
    pagina.goto(openbaar)
    pagina.screenshot(path=UIT / "openbaar.png", full_page=True)
    ctx.close()
    bezoeker.close()


def main():
    fase = sys.argv[1]
    if fase == "import":
        importeren(LEDEN)
    elif fase == "opzeggers":
        opzeggers()
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            schermen(browser)
            browser.close()


main()
