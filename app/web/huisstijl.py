"""Instellingen: naam en logo van de vereniging (BLB-027, ADR-008, ADR-009) en de
bootsoorten (BLB-028)."""

from flask import flash, redirect, render_template, request, url_for

from app.domein import indeling, instellingen
from app.web import bp, inloggen_vereist, recent_ingelogd, uitvoeren


@bp.get("/logo/<kenmerk>")
def logo(kenmerk):
    # Openbaar, zoals de openbare pagina. Het kenmerk wijzigt met elk nieuw logo, dus de inhoud
    # achter een URL wijzigt nooit en mag lang in de cache.
    afbeelding = instellingen.logo_op_kenmerk(kenmerk)
    if afbeelding is None:
        return "Niet gevonden", 404, {"Content-Type": "text/plain; charset=utf-8"}
    return afbeelding.inhoud, {
        "Content-Type": afbeelding.mime_type,
        "Content-Disposition": "inline",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=31536000, immutable",
    }


@bp.get("/instellingen")
@inloggen_vereist
def instellingen_scherm():
    return render_template("instellingen.html", stijl=instellingen.huidig(),
                           bootsoorten=indeling.bootsoorten(),
                           bootsoorten_open=request.args.get("open") == "bootsoorten",
                           logo_open=request.args.get("open") == "logo")


@bp.post("/instellingen")
@inloggen_vereist
@recent_ingelogd
def instellingen_opslaan():
    uitvoeren(instellingen.opslaan, request.form.get("naam"),
              gelukt="De instellingen zijn opgeslagen.")
    return redirect(url_for("web.instellingen_scherm"))


@bp.post("/instellingen/logo")
@inloggen_vereist
@recent_ingelogd
def logo_opslaan():
    bestand = request.files.get("logo")
    if not bestand or not bestand.filename:
        flash("Kies een logo.", "fout")
        gelukt = False
    else:
        gelukt = uitvoeren(instellingen.logo_vervangen, bestand.read(), gelukt="Het logo is opgeslagen.")
    return _naar_logo(gelukt)


@bp.post("/instellingen/logo/verwijderen")
@inloggen_vereist
@recent_ingelogd
def logo_verwijderen():
    gelukt = uitvoeren(instellingen.logo_verwijderen, gelukt="Het logo is verwijderd.")
    return _naar_logo(gelukt)


def _naar_logo(gelukt):
    """Na een geweigerde actie staat het blok Logo open, met de melding erboven."""
    return redirect(url_for("web.instellingen_scherm", **({} if gelukt else {"open": "logo"})))


def _naar_bootsoorten():
    """Na een actie op bootsoorten staat het blok Bootsoorten open (BV-64)."""
    return redirect(url_for("web.instellingen_scherm", open="bootsoorten", _anchor="bootsoorten"))


@bp.post("/bootsoorten")
@inloggen_vereist
@recent_ingelogd
def bootsoort_toevoegen():
    uitvoeren(indeling.bootsoort_toevoegen, request.form.get("naam"),
              gelukt="De bootsoort is toegevoegd.")
    return _naar_bootsoorten()


@bp.post("/bootsoorten/<int:bootsoort_id>/naam")
@inloggen_vereist
@recent_ingelogd
def bootsoort_hernoemen(bootsoort_id):
    uitvoeren(indeling.bootsoort_hernoemen, bootsoort_id, request.form.get("naam"),
              gelukt="De naam van de bootsoort is opgeslagen.")
    return _naar_bootsoorten()


@bp.post("/bootsoorten/<int:bootsoort_id>/verwijderen")
@inloggen_vereist
@recent_ingelogd
def bootsoort_verwijderen(bootsoort_id):
    uitvoeren(indeling.bootsoort_verwijderen, bootsoort_id, gelukt="De bootsoort is verwijderd.")
    return _naar_bootsoorten()
