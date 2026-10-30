"""Overzichten voor de beheerder: vrije plaatsen (BLB-015), plaatsen van oud-leden (BLB-018) en
de export van de indeling (BLB-017). Alleen lezen."""

from flask import render_template, request

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


@bp.get("/indeling.xlsx")
@inloggen_vereist
def indeling_export():
    return indeling.export(instellingen.huidig()["naam"]), {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="indeling.xlsx"',
    }
