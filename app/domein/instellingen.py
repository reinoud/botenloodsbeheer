"""Naam en kleuren van de vereniging (BLB-027, ADR-009). Staan in de tabel instelling;
een lege of ontbrekende waarde is de neutrale standaard. Het logo komt uit de installatie
(app.web.huisstijl.logo_laden, ADR-008)."""

import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.domein import Regelfout, log
from app.models import Instelling, db

STANDAARD = {"naam": "Botenloods", "kleur_primair": "#3f6fb5", "kleur_secundair": "#5f6b7a"}
HEX = re.compile(r"#[0-9a-fA-F]{6}")
MIN_CONTRAST = 4.5  # WCAG AA voor gewone tekst (ADR-002)
# Waar de kleur in stijl.css als tekst of achtergrond van tekst staat.
TEGENKLEUR = {"kleur_primair": ("#ffffff", "de tekst in de kopbalk"),
              "kleur_secundair": ("#f5f6f8", "de koppen op de achtergrond")}


def huidig():
    """Naam en kleuren. Een ongeldige kleur in de database wordt de standaard, zodat de
    stylesheet nooit iets anders dan een hexkleur bevat."""
    waarden = {i.sleutel: i.waarde for i in db.session.scalars(select(Instelling))}
    uit = {k: waarden.get(k) or v for k, v in STANDAARD.items()}
    for k in TEGENKLEUR:
        if not HEX.fullmatch(uit[k]):
            uit[k] = STANDAARD[k]
    return uit


def contrast(kleur1, kleur2):
    """Contrastverhouding volgens WCAG 2.x, van 1 tot 21."""
    def luminantie(kleur):
        kanalen = [int(kleur[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in kanalen)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    licht, donker = sorted((luminantie(kleur1), luminantie(kleur2)), reverse=True)
    return (licht + 0.05) / (donker + 0.05)


def _vergrendel(sleutels):
    """Maakt ontbrekende rijen leeg aan en vergrendelt ze, zodat ook de eerste keer twee
    gelijktijdige wijzigingen op elkaar wachten."""
    db.session.execute(insert(Instelling).values([{"sleutel": s, "waarde": ""} for s in sleutels])
                       .on_conflict_do_nothing())
    rijen = db.session.scalars(select(Instelling).where(Instelling.sleutel.in_(sleutels))
                               .with_for_update().execution_options(populate_existing=True))
    return {i.sleutel: i for i in rijen}


def opslaan(naam, kleur_primair, kleur_secundair, actor):
    """Slaat naam en kleuren op. Geeft waarschuwingen bij slecht leesbare tekst; opslaan gaat
    dan toch door (BLB-027)."""
    nieuw = {"naam": (naam or "").strip(), "kleur_primair": (kleur_primair or "").strip().lower(),
             "kleur_secundair": (kleur_secundair or "").strip().lower()}
    if not 1 <= len(nieuw["naam"]) <= 100:
        raise Regelfout("Geef de vereniging een naam van 1 tot 100 tekens.")
    if not all(HEX.fullmatch(nieuw[k]) for k in TEGENKLEUR):
        raise Regelfout("Kies een kleur als #3f6fb5.")
    rijen = _vergrendel(list(nieuw))
    wijzigingen = {}
    for k, waarde in nieuw.items():
        oud = rijen[k].waarde or STANDAARD[k]
        if waarde != oud:
            wijzigingen[k] = [oud, waarde]
        rijen[k].waarde = waarde
    if wijzigingen:
        log.schrijf(actor, "instelling.gewijzigd", ["instelling:huisstijl"], wijzigingen)
    db.session.commit()
    waarschuwingen = []
    for k, (tegen, waar) in TEGENKLEUR.items():
        verhouding = contrast(nieuw[k], tegen)
        if verhouding < MIN_CONTRAST:
            waarschuwingen.append(f"Met {nieuw[k]} is {waar} slecht leesbaar: contrast "
                                  f"{verhouding:.1f} op 1, minimaal {MIN_CONTRAST} op 1.")
    return waarschuwingen

