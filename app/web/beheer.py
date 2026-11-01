"""Beheerschermen: indeling, plaatsdetail, boten, leden en beheerders. Schermen over boten en
plaatsen tonen de bootmutaties die erbij horen (BLB-025, BLB-043, ADR-006)."""

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app.domein import Regelfout, beheerders, boten, indeling, leden, log, toewijzing
from app.web import bp, inloggen_vereist, recent_ingelogd, uitvoeren


def _of_404(functie, *args):
    try:
        return functie(*args)
    except Regelfout:
        abort(404)


# Indeling


@bp.get("/indeling")
@inloggen_vereist
def indeling_overzicht():
    return render_template("indeling.html", rekken=indeling.rekken(), status=indeling.status,
                           bootsoorten=indeling.bootsoorten())


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
    return render_template(
        "plaats.html", plaats=p, oud_lid=p.boot and p.boot.lid and leden.is_oud_lid(p.boot.lid),
        boten=boten.zonder_plaats() if p.boot is None else [],
        bootsoorten=indeling.bootsoorten(),
        openbare_url=f"{current_app.config['BASIS_URL']}/p/{p.publieke_sleutel}",
        regels=log.regels([f"plaats:{p.id}"]))


@bp.post("/plaatsen/<int:plaats_id>/toewijzen")
@inloggen_vereist
def plaats_toewijzen(plaats_id):
    uitvoeren(toewijzing.toewijzen, plaats_id, request.form.get("boot_id", type=int),
              gelukt="De boot heeft de plaats gekregen.")
    return redirect(url_for("web.plaats_detail", plaats_id=plaats_id))


@bp.post("/plaatsen/<int:plaats_id>/vrijgeven")
@inloggen_vereist
def plaats_vrijgeven(plaats_id):
    uitvoeren(toewijzing.vrijgeven, plaats_id, gelukt="De plaats is vrijgegeven.")
    return redirect(url_for("web.plaats_detail", plaats_id=plaats_id))


@bp.post("/plaatsen/<int:plaats_id>")
@inloggen_vereist
def plaats_wijzigen(plaats_id):
    uitvoeren(indeling.plaats_wijzigen, plaats_id, request.form.get("code"),
              request.form.getlist("bootsoort", type=int), "clubplaats" in request.form,
              gelukt="De plaats is opgeslagen.")
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
    return render_template("boot.html", boot=b, regels=log.regels([f"boot:{b.id}"]),
                           bootsoorten=indeling.bootsoorten(), leden=leden.actieve_leden())


@bp.post("/boten/<int:boot_id>")
@inloggen_vereist
def boot_wijzigen(boot_id):
    _of_404(boten.boot, boot_id)
    eigenaar = request.form.get("eigenaar", "")
    lid_id = None if eigenaar == "club" else request.form.get("eigenaar", type=int)
    if eigenaar != "club" and lid_id is None:
        flash("Kies een eigenaar.", "fout")
    else:
        uitvoeren(boten.boot_wijzigen, boot_id, request.form.get("naam"),
                  request.form.get("bootsoort", type=int), lid_id, gelukt="De boot is opgeslagen.")
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


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


# Leden (BLB-006): alleen lezen; de bron is leidend en de integratiecontainer importeert


@bp.get("/leden")
@inloggen_vereist
def leden_overzicht():
    zoek = request.args.get("zoek", "")
    return render_template("leden.html", leden=leden.alle_leden(zoek), zoek=zoek,
                           runs=leden.laatste_runs(), is_oud_lid=leden.is_oud_lid)


@bp.get("/leden/<int:lid_id>")
@inloggen_vereist
def lid_detail(lid_id):
    # BLB-019: boten met plaats. Adres, telefoon en e-mail staan alleen op het plaatsdetail.
    lid = _of_404(leden.lid, lid_id)
    return render_template("lid.html", lid=lid, oud_lid=leden.is_oud_lid(lid),
                           regels=log.regels([f"lid:{lid.id}"]))


@bp.post("/leden/ophalen")
@inloggen_vereist
def leden_ophalen():
    uitvoeren(leden.import_aanvragen,
              gelukt="De import is aangevraagd. De integratiecontainer begint binnen een minuut; "
                     "ververs daarna de pagina.")
    return redirect(url_for("web.leden_overzicht"))


# Beheerders (BLB-023)


@bp.get("/beheerders")
@inloggen_vereist
def beheerders_overzicht():
    return render_template("beheerders.html", beheerders=beheerders.alle())


def _link(code, titel, uitleg):
    # De link staat alleen in dit antwoord; niet in een flash, want de sessiecookie is leesbaar.
    return render_template("link.html", titel=titel, uitleg=uitleg,
                           link=f"{current_app.config['BASIS_URL']}/uitnodiging/{code}")


@bp.post("/beheerders")
@inloggen_vereist
@recent_ingelogd
def beheerder_uitnodigen():
    code = uitvoeren(beheerders.uitnodigen, request.form.get("gebruikersnaam", "").strip())
    if code is None:
        return redirect(url_for("web.beheerders_overzicht"))
    return _link(code, "Beheerder uitgenodigd",
                 "Geef deze link aan de nieuwe beheerder. Hij werkt één keer en is 24 uur geldig.")


@bp.post("/beheerders/<int:beheerder_id>/herstellen")
@inloggen_vereist
@recent_ingelogd
def beheerder_herstellen(beheerder_id):
    code = uitvoeren(beheerders.herstellen, beheerder_id)
    if code is None:
        return redirect(url_for("web.beheerders_overzicht"))
    return _link(code, "Toegang hersteld",
                 "De oude inlogmethodes en sessies zijn ingetrokken. Geef deze link aan de "
                 "beheerder. Hij werkt één keer en is 24 uur geldig.")


@bp.post("/beheerders/<int:beheerder_id>/<any(blokkeren, deblokkeren, verwijderen):actie>")
@inloggen_vereist
def beheerder_wijzigen(beheerder_id, actie):
    uitvoeren(getattr(beheerders, actie), beheerder_id, gelukt={
        "blokkeren": "Het account is geblokkeerd.", "deblokkeren": "Het account is gedeblokkeerd.",
        "verwijderen": "Het account is verwijderd."}[actie])
    return redirect(url_for("web.beheerders_overzicht"))
