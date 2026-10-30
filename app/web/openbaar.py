"""Zonder inloggen: de openbare pagina van een plaats (BLB-020) en afbeeldingen (ADR-008)."""

from flask import render_template

from app.domein import afbeeldingen, indeling
from app.web import bp


@bp.get("/p/<sleutel>")
def openbare_plaats(sleutel):
    # Geen zoekfunctie en geen log op deze pagina; alleen via de QR-link (ADR-003).
    gegevens = indeling.openbaar(sleutel)
    if gegevens is None:
        return render_template("openbaar.html", plaats=None), 404
    return render_template("openbaar.html", plaats=gegevens)


@bp.get("/afbeelding/<sleutel>")
def afbeelding(sleutel):
    a = afbeeldingen.op_sleutel(sleutel)
    if a is None:
        return "Niet gevonden", 404, {"Content-Type": "text/plain; charset=utf-8"}
    # De sleutel wijzigt bij elke upload, dus de inhoud achter een URL wijzigt nooit.
    return a.inhoud, {
        "Content-Type": a.mime_type,
        "Content-Disposition": "inline",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=31536000, immutable",
    }
