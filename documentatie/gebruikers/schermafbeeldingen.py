"""Maakt de schermafbeeldingen van de handleiding, in de container botenloods-e2e (Playwright).
Wordt aangeroepen door schermafbeeldingen.sh met een fase: import, opzeggers of schermen.
Alleen synthetische gegevens. Geheimen (TOTP-sleutel, QR-code, uitnodigingscode) worden vóór
elke opname uit het scherm gehaald."""

import json
import os
import re
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
UIT = Path(os.environ.get("DOC_UIT", "/documentatie/gebruikers/afbeeldingen"))
BREEDTE = int(os.environ.get("DOC_BREEDTE", "1100"))  # een andere breedte is voor controle, bijvoorbeeld 390 (telefoon)
LEDEN = json.loads(Path("/fixtures/leden.json").read_text(encoding="utf-8"))
WACHTWOORD = "voorbeeld wachtwoord voor de loods"


def importeren(leden):
    verzoek = urllib.request.Request(
        f"{os.environ['DOC_API']}/leden", data=json.dumps({"leden": leden}).encode(),
        method="PUT",
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
                                 clip={"x": 0, "y": 0, "width": BREEDTE, "height": hoogte})
        else:
            self.page.screenshot(path=pad, full_page=True)


def verberg_geheimen(page):
    """QR-code en sleutel zijn een TOTP-geheim; de uitnodigingslink bevat de eenmalige code; de
    tokenwaarde is een geheim."""
    page.evaluate("""() => {
        const qr = document.querySelector('img.qr');
        if (qr) { const b = qr.getBoundingClientRect(); const vak = document.createElement('div');
          vak.style.cssText = `width:${b.width}px;height:${b.height}px;background:#ddd`; qr.replaceWith(vak); }
        const sleutel = document.querySelector('#totp-geheim');
        if (sleutel) sleutel.textContent = 'ABCD EFGH IJKL MNOP';
        const link = document.querySelector('#uitnodigingslink');
        if (link) link.textContent = link.textContent.replace(/\\/uitnodiging\\/.*/, '/uitnodiging/<code>');
        const token = document.querySelector('#tokenwaarde');
        if (token) token.textContent = 'blb_<waarde>';
    }""")


def nieuwe_code(totp, vorige):
    """Een code die de server nog niet kent: wacht tot de stap van 30 seconden is omgeslagen."""
    while totp.now() == vorige:
        time.sleep(1)
    return totp.now()


def schermen(browser):
    ctx = browser.new_context(base_url=BASIS, viewport={"width": BREEDTE, "height": 800},
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
    ctx = browser.new_context(base_url=BASIS, viewport={"width": BREEDTE, "height": 800},
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
    # Tokens: een persoonlijk token en een robottoken, binnen 10 minuten na het inloggen.
    page.goto("/tokens/nieuw")
    page.get_by_label("Naam (a-z, cijfers, punt, - en _)").fill("laptop-penningmeester")
    for recht in ("boten:lezen", "leden:lezen"):
        page.get_by_label(recht, exact=True).check()
    o.maak("token-nieuw", hoogte=900)
    page.get_by_role("button", name="Token maken").click()
    verberg_geheimen(page)
    o.maak("token-waarde", hoogte=400)
    page.goto("/tokens")
    o.maak("tokens", hoogte=900)
    page.locator("summary", has_text="laptop-penningmeester").click()
    o.maak("token-rechten", element=page.locator("section.kaart").nth(1))
    page.goto("/profiel")
    o.maak("profiel", hoogte=700)

    # Indeling.
    page.goto("/indeling")
    o.maak("indeling", hoogte=1100)
    sectie = page.locator("section.kaart", has=page.get_by_role("heading", name="J", exact=True))
    sectie.get_by_text("Rek wijzigen of verwijderen").click()
    o.maak("rek-wijzigen", element=sectie.locator("details").first)
    page.goto("/rekoverzicht")
    o.maak("rekoverzicht", element=page.locator(
        "section.kaart", has=page.get_by_role("heading", name="F", exact=True)))

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
    page.get_by_label("Aanmelddatum (leeg is vandaag; een eerdere datum mag)").fill("2025-04-01")
    o.maak("boot-wachtlijst", element=page.locator("section.kaart",
                                                   has=page.get_by_role("heading", name="Wachtlijst")))
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
    page.wait_for_url(re.compile(r"/vrij\?bootsoort=\d+$"))
    o.maak("vrij", hoogte=700)
    page.goto("/wachtlijst")
    o.maak("wachtlijst", hoogte=1000)
    page.goto("/opgezegd")
    o.maak("opgezegd", hoogte=600)
    page.goto("/opzeggend")
    o.maak("opzeggend", hoogte=600)

    # Kaartjes van het eerste rek (BLB-021).
    page.goto("/kaartjes")
    page.locator("fieldset").first.get_by_label("Heel ", exact=False).check()
    page.get_by_role("button", name="Kaartjes maken").click()
    o.maak("kaartjes", hoogte=900)

    # Leden en import.
    page.goto("/leden")
    page.get_by_role("button", name="Leden nu ophalen").click()
    expect(page.get_by_text("De import is aangevraagd.")).to_be_visible()
    o.maak("leden", hoogte=800)

    page.goto("/log")
    o.maak("log", hoogte=700)
    page.goto("/log/techniek")
    o.maak("log-techniek", hoogte=700)
    page.goto("/instellingen")
    o.maak("instellingen")  # hele pagina, met het blok Bootsoorten
    page.goto("/status")
    o.maak("status", hoogte=900)

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
            # Het datumveld volgt LANGUAGE van het browserproces, niet de locale van de context, en
            # alleen de volledige Chromium leest die (de headless shell niet).
            browser = p.chromium.launch(channel="chromium", env={**os.environ, "LANGUAGE": "nl_NL"})
            schermen(browser)
            browser.close()


main()
