"""De uploadgrenzen via Traefik (#209, ADR-008, ADR-013). Tot 10 MB neemt de applicatie een bestand
aan, daarboven geeft zij zelf een melding (een 302 naar het formulier, #190) en Traefik laat tot 25 MB
door op de routers van het logo en van /boten. Boven 25 MB weigert Traefik op de kop Content-Length,
vóór het lichaam. Een ingelogde beheerder krijgt van de applicatie nooit een kale 413 op deze paden;
een 413 zonder omleiding komt dus van Traefik.

De test zet geen globale staat: elke grens weigert het bestand. Neemt de applicatie bij een regressie
toch een logo aan, dan zet finally het logo van het begin terug (#285)."""

import http.client
from urllib.parse import urlsplit

from conftest import STEMPEL, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, png

MB = 1024 * 1024
TE_GROOT = "Dit bestand is groter dan 10 MB. Kies een kleiner bestand."


def csrf(page):
    return page.locator("input[name=csrf_token]").first.get_attribute("value")


def post(page, pad, veld, inhoud, csrf_token):
    """Een formulier van de beheerder, zonder omleiding te volgen; de sessie loopt mee."""
    return page.request.post(pad, max_redirects=0, multipart={
        "csrf_token": csrf_token,
        veld: {"name": "groot.png", "mimeType": "image/png", "buffer": inhoud}})


def kop_alleen(page, base_url, pad, lengte):
    """Stuurt alleen de kop met Content-Length, met de sessie van de beheerder; geeft (status,
    kopnamen, lichaam). Een router zonder grens laat de kop door en wacht dan op een lichaam
    dat niet komt: de time-out geeft status None."""
    deel = urlsplit(base_url)
    verbinding = http.client.HTTPConnection(deel.hostname, deel.port, timeout=10)
    verbinding.putrequest("POST", pad)
    verbinding.putheader("Cookie", "; ".join(f"{c['name']}={c['value']}" for c in page.context.cookies()))
    verbinding.putheader("Content-Type", "multipart/form-data; boundary=grens")
    verbinding.putheader("Content-Length", str(lengte))
    verbinding.endheaders()
    try:
        antwoord = verbinding.getresponse()
        return antwoord.status, {k.lower() for k, _ in antwoord.getheaders()}, antwoord.read()
    except TimeoutError:
        return None, set(), b"geen antwoord: de kop kwam bij de applicatie"
    finally:
        verbinding.close()


def huidig_logo(page):
    """(src, inhoud) van het logo in de kopbalk, of (None, None) zonder logo."""
    page.goto("/instellingen")
    img = page.locator("header .dj-logo img.bl-logo")
    src = img.get_attribute("src") if img.count() else None
    return src, page.request.get(src).body() if src else None


def test_logo_en_foto_tussen_10_en_25_mb_melding_boven_25_mb_413_van_traefik(page, base_url):
    wachtwoord_instellen(page, "uploadgrens")
    begin, inhoud = huidig_logo(page)
    try:
        _grenzen(page, base_url)
    finally:
        if huidig_logo(page)[0] != begin:
            if inhoud:
                post(page, "/instellingen/logo", "logo", inhoud, csrf(page))
            else:
                page.request.post("/instellingen/logo/verwijderen", max_redirects=0,
                                  form={"csrf_token": csrf(page)})
            assert (huidig_logo(page)[0] is None) == (begin is None), "logo niet hersteld"


def _grenzen(page, base_url):
    naam = f"Uploadboot {STEMPEL}"  # een clubboot zonder plaats: geen rek nodig
    boot_vastleggen(page, naam, "Kajak")
    page.goto("/boten")
    boot_id = page.get_by_role("link", name=naam, exact=True).get_attribute("href").rsplit("/", 1)[1]
    groot = png() + b"0" * (15 * MB)
    logo, foto = "/instellingen/logo", f"/boten/{boot_id}/foto"

    # 15 MB: Traefik laat door (-25mb), de applicatie weigert met een melding en een omleiding.
    # Die melding staat in haar sessie; Traefik stuurt geen Location en zet geen sessie.
    page.goto("/instellingen")
    antwoord = post(page, logo, "logo", groot, csrf(page))
    assert antwoord.status == 302, antwoord.status  # 413 is van Traefik, 400 of 404 van de router
    assert antwoord.headers["location"].endswith("/instellingen?open=logo")
    page.goto(antwoord.headers["location"])
    expect(page.get_by_role("alert")).to_contain_text(TE_GROOT)

    page.goto(f"/boten/{boot_id}")
    antwoord = post(page, foto, "foto", groot, csrf(page))
    assert antwoord.status == 302, antwoord.status
    assert antwoord.headers["location"].endswith(f"/boten/{boot_id}?open=foto")
    page.goto(antwoord.headers["location"])
    expect(page.get_by_role("alert")).to_contain_text(TE_GROOT)

    # Boven 25 MB: alleen de kop. Op alleen een kop antwoordt de applicatie niet (status None, zie
    # kop_alleen); een 413 zonder Location komt dus van Traefik.
    for pad in (logo, foto):
        status, koppen, lichaam = kop_alleen(page, base_url, pad, 25 * MB + 1)
        assert status == 413 and "location" not in koppen, (pad, status, lichaam[:80])
