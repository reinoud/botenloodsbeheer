"""Overzichten voor de beheerder: vrije plaatsen (BLB-015), plaatsen van oud-leden (BLB-018), van
leden die gaan opzeggen (BLB-041), de export van de indeling (BLB-017) en de kaartjes met
QR-code (BLB-021). Alleen lezen."""

import segno
from flask import current_app, flash, redirect, render_template, request, url_for

from app.domein import indeling, instellingen, log
from app.web import bp, inloggen_vereist


@bp.get("/vrij")
@inloggen_vereist
def vrije_plaatsen():
    soort_id = request.args.get("bootsoort", type=int)
    soorten = indeling.bootsoorten()
    return render_template(
        "vrij.html", plaatsen=indeling.vrije_plaatsen(soort_id), bootsoorten=soorten,
        gekozen=next((s for s in soorten if s.id == soort_id), None),
        regels=log.regels(acties=("plaats.",)))


@bp.get("/opgezegd")
@inloggen_vereist
def opgezegd():
    rijen = indeling.plaatsen_van_oud_leden()
    return render_template(
        "opgezegd.html", rijen=rijen,
        regels=log.regels([f"plaats:{p.id}" for _d, p in rijen]) if rijen else [])


@bp.get("/opzeggend")
@inloggen_vereist
def opzeggend():
    plaatsen = indeling.plaatsen_van_opzeggende_leden()
    return render_template(
        "opzeggend.html", plaatsen=plaatsen,
        regels=log.regels([f"plaats:{p.id}" for p in plaatsen]) if plaatsen else [])


@bp.get("/indeling.xlsx")
@inloggen_vereist
def indeling_export():
    return indeling.export(instellingen.huidig()["naam"]), {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="indeling.xlsx"',
    }


@bp.get("/kaartjes")
@inloggen_vereist
def kaartjes_kiezen():
    return render_template("kaartjes.html", rekken=indeling.rekken())


def qr(sleutel):
    """De QR-code van de openbare pagina als inline SVG (ADR-011); alleen BASIS_URL en de
    publieke sleutel, zodat hernoemen het kaartje niet breekt (ADR-003)."""
    url = f"{current_app.config['BASIS_URL']}/p/{sleutel}"
    return segno.make(url, error="m").svg_inline(omitsize=True, svgclass="qr-kaartje")


@bp.get("/kaartjes/print")
@inloggen_vereist
def kaartjes_print():
    kaartjes = indeling.kaartjes(request.args.getlist("plaats", type=int),
                                 request.args.getlist("rek", type=int), "alle" in request.args)
    if not kaartjes:
        flash("Kies een of meer plaatsen, een rek of alle plaatsen.", "fout")
        return redirect(url_for("web.kaartjes_kiezen"))
    return render_template("kaartjes_print.html", kaartjes=kaartjes, qr=qr)
