"""Beheerschermen: indeling, plaatsdetail, boten en leden. Elk scherm toont het log dat erbij
hoort (BLB-025, ADR-006)."""

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app.domein import Regelfout, boten, indeling, leden, log, toewijzing
from app.web import bp, inloggen_vereist, uitvoeren


def _of_404(functie, *args):
    try:
        return functie(*args)
    except Regelfout:
        abort(404)


# Indeling


@bp.get("/indeling")
@inloggen_vereist
def indeling_overzicht():
    return render_template("indeling.html", rekken=indeling.rekken(),
                           bootsoorten=indeling.bootsoorten(),
                           regels=log.regels(acties=("rek.", "plaats.")))


@bp.post("/rekken")
@inloggen_vereist
def rek_aanmaken():
    uitvoeren(indeling.rek_aanmaken, request.form.get("naam"), gelukt="Het rek is aangemaakt.")
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/naam")
@inloggen_vereist
def rek_wijzigen(rek_id):
    uitvoeren(indeling.rek_wijzigen, rek_id, request.form.get("naam"))
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/verwijderen")
@inloggen_vereist
def rek_verwijderen(rek_id):
    uitvoeren(indeling.rek_verwijderen, rek_id, gelukt="Het rek is verwijderd.")
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/plaatsen")
@inloggen_vereist
def plaats_aanmaken(rek_id):
    uitvoeren(indeling.plaats_aanmaken, rek_id, request.form.get("code"),
              request.form.getlist("bootsoort", type=int), "clubplaats" in request.form,
              gelukt="De plaats is aangemaakt.")
    return redirect(url_for("web.indeling_overzicht"))


# Plaatsdetail (BLB-012) en toewijzen (BLB-010)


@bp.get("/plaatsen/<int:plaats_id>")
@inloggen_vereist
def plaats_detail(plaats_id):
    p = _of_404(indeling.plaats, plaats_id)
    verwijzingen = [f"plaats:{p.id}", *([f"boot:{p.boot_id}"] if p.boot_id else [])]
    return render_template(
        "plaats.html", plaats=p, oud_lid=p.boot and p.boot.lid and leden.is_oud_lid(p.boot.lid),
        boten=boten.zonder_plaats() if p.boot is None else [],
        openbare_url=f"{current_app.config['BASIS_URL']}/p/{p.publieke_sleutel}",
        regels=log.regels(verwijzingen))


@bp.post("/plaatsen/<int:plaats_id>/toewijzen")
@inloggen_vereist
def plaats_toewijzen(plaats_id):
    uitvoeren(toewijzing.toewijzen, plaats_id, request.form.get("boot_id", type=int),
              gelukt="De boot heeft de plaats gekregen.")
    return redirect(url_for("web.plaats_detail", plaats_id=plaats_id))


@bp.post("/plaatsen/<int:plaats_id>/verwijderen")
@inloggen_vereist
def plaats_verwijderen(plaats_id):
    if uitvoeren(indeling.plaats_verwijderen, plaats_id, gelukt="De plaats is verwijderd.") is None:
        return redirect(url_for("web.plaats_detail", plaats_id=plaats_id))
    return redirect(url_for("web.indeling_overzicht"))


# Boten (BLB-005)


def _foto():
    bestand = request.files.get("foto")
    return bestand.read() if bestand and bestand.filename else None


@bp.get("/boten")
@inloggen_vereist
def boten_overzicht():
    return render_template("boten.html", boten=boten.boten(), bootsoorten=indeling.bootsoorten(),
                           leden=leden.actieve_leden(), regels=log.regels(acties=("boot.",)))


@bp.post("/boten")
@inloggen_vereist
def boot_aanmaken():
    eigenaar = request.form.get("eigenaar", "")
    lid_id = None if eigenaar == "club" else request.form.get("eigenaar", type=int)
    if eigenaar != "club" and lid_id is None:
        flash("Kies een eigenaar.", "fout")
        return redirect(url_for("web.boten_overzicht"))
    b = uitvoeren(boten.boot_aanmaken, request.form.get("naam"),
                  request.form.get("bootsoort", type=int), lid_id, _foto(),
                  gelukt="De boot is vastgelegd.")
    if b is None:
        return redirect(url_for("web.boten_overzicht"))
    return redirect(url_for("web.boot_detail", boot_id=b.id))


@bp.get("/boten/<int:boot_id>")
@inloggen_vereist
def boot_detail(boot_id):
    b = _of_404(boten.boot, boot_id)
    return render_template("boot.html", boot=b, regels=log.regels([f"boot:{b.id}"]))


@bp.post("/boten/<int:boot_id>/foto")
@inloggen_vereist
def boot_foto(boot_id):
    foto = _foto()
    if foto is None:
        flash("Kies een foto.", "fout")
    else:
        uitvoeren(boten.foto_vervangen, boot_id, foto, gelukt="De foto is opgeslagen.")
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


@bp.post("/boten/<int:boot_id>/verwijderen")
@inloggen_vereist
def boot_verwijderen(boot_id):
    if uitvoeren(boten.boot_verwijderen, boot_id, gelukt="De boot is verwijderd.") is None:
        return redirect(url_for("web.boot_detail", boot_id=boot_id))
    return redirect(url_for("web.boten_overzicht"))


# Leden (BLB-006): alleen lezen; de bron is leidend


@bp.get("/leden")
@inloggen_vereist
def leden_overzicht():
    return render_template("leden.html", leden=leden.alle_leden(), runs=leden.laatste_runs(),
                           is_oud_lid=leden.is_oud_lid,
                           regels=log.regels(acties=("lid.", "leden.")))


@bp.post("/leden/ophalen")
@inloggen_vereist
def leden_ophalen():
    uitvoeren(leden.synchronisatie_aanvragen,
              gelukt="De synchronisatie is aangevraagd. Ververs de pagina over een halve minuut.")
    return redirect(url_for("web.leden_overzicht"))
