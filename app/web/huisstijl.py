"""Instellingen: naam, kleuren en logo van de vereniging (BLB-027, ADR-008, ADR-009) en de
bootsoorten (BLB-028)."""

import hashlib

from flask import current_app, flash, redirect, render_template, request, url_for

from app.config import UPLOAD_MAX
from app.domein import Regelfout, afbeeldingen, indeling, instellingen
from app.web import bp, inloggen_vereist, recent_ingelogd, uitvoeren


def logo_laden(app):
    """Leest het logo uit de installatie één keer bij het starten, met dezelfde controle als een
    upload (ADR-008). Ontbreekt het of is het ongeldig, dan toont de kopbalk alleen de naam en
    staat de reden in de containerlog. Een nieuw logo vraagt een herstart van web."""
    app.extensions["logo"] = None
    pad = app.config["LOGO_BESTAND"]
    if not pad:
        return
    try:
        with open(pad, "rb") as f:
            inhoud = f.read(UPLOAD_MAX + 1)
        if len(inhoud) > UPLOAD_MAX:
            raise Regelfout("groter dan 10 MB")
        png = afbeeldingen.verwerk(inhoud, "logo").inhoud
    except FileNotFoundError:
        app.logger.warning("Geen logo in %s; de kopbalk toont alleen de naam.", pad)
        return
    except (OSError, Regelfout):
        app.logger.warning("Het logo in %s is geen JPEG, PNG of WebP tot 10 MB; de kopbalk toont "
                           "alleen de naam.", pad)
        return
    app.extensions["logo"] = (hashlib.sha256(png).hexdigest()[:16], png)
    app.logger.info("Logo geladen uit %s.", pad)


@bp.get("/logo/<kenmerk>")
def logo(kenmerk):
    # Openbaar, zoals de openbare pagina. Het kenmerk is een hash van de inhoud, dus de inhoud
    # achter een URL wijzigt nooit en mag lang in de cache.
    logo = current_app.extensions["logo"]
    if logo is None or kenmerk != logo[0]:
        return "Niet gevonden", 404, {"Content-Type": "text/plain; charset=utf-8"}
    return logo[1], {
        "Content-Type": "image/png",
        "Content-Disposition": "inline",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=31536000, immutable",
    }


@bp.get("/huisstijl.css")
def huisstijl_css():
    # Openbaar, want ook de openbare pagina gebruikt de kleuren. Een eigen stylesheet past in
    # de CSP (style-src 'self'); huidig() geeft alleen geldige hexkleuren.
    stijl = instellingen.huidig()
    css = (f":root {{ --kleur-primair: {stijl['kleur_primair']}; "
           f"--kleur-secundair: {stijl['kleur_secundair']}; }}\n")
    return css, {"Content-Type": "text/css; charset=utf-8"}


@bp.get("/instellingen")
@inloggen_vereist
def instellingen_scherm():
    return render_template("instellingen.html", stijl=instellingen.huidig(),
                           bootsoorten=indeling.bootsoorten())


@bp.post("/instellingen")
@inloggen_vereist
@recent_ingelogd
def instellingen_opslaan():
    waarschuwingen = uitvoeren(instellingen.opslaan, request.form.get("naam"),
                               request.form.get("kleur_primair"),
                               request.form.get("kleur_secundair"),
                               gelukt="De instellingen zijn opgeslagen.")
    for tekst in waarschuwingen or []:
        flash(tekst, "fout")
    return redirect(url_for("web.instellingen_scherm"))



@bp.post("/bootsoorten")
@inloggen_vereist
@recent_ingelogd
def bootsoort_toevoegen():
    uitvoeren(indeling.bootsoort_toevoegen, request.form.get("naam"),
              gelukt="De bootsoort is toegevoegd.")
    return redirect(url_for("web.instellingen_scherm"))


@bp.post("/bootsoorten/<int:bootsoort_id>/naam")
@inloggen_vereist
@recent_ingelogd
def bootsoort_hernoemen(bootsoort_id):
    uitvoeren(indeling.bootsoort_hernoemen, bootsoort_id, request.form.get("naam"),
              gelukt="De naam van de bootsoort is opgeslagen.")
    return redirect(url_for("web.instellingen_scherm"))


@bp.post("/bootsoorten/<int:bootsoort_id>/verwijderen")
@inloggen_vereist
@recent_ingelogd
def bootsoort_verwijderen(bootsoort_id):
    uitvoeren(indeling.bootsoort_verwijderen, bootsoort_id, gelukt="De bootsoort is verwijderd.")
    return redirect(url_for("web.instellingen_scherm"))
