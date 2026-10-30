"""Naam, kleuren en logo van de vereniging (BLB-027, ADR-009)."""

from flask import flash, redirect, render_template, request, url_for

from app.domein import instellingen, log
from app.web import bp, inloggen_vereist, recent_ingelogd, uitvoeren


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
                           regels=log.regels(["instelling:huisstijl"]))


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


@bp.post("/instellingen/logo")
@inloggen_vereist
@recent_ingelogd
def logo_opslaan():
    bestand = request.files.get("logo")
    if not bestand or not bestand.filename:
        flash("Kies een logo.", "fout")
    else:
        uitvoeren(instellingen.logo_vervangen, bestand.read(), gelukt="Het logo is opgeslagen.")
    return redirect(url_for("web.instellingen_scherm"))
