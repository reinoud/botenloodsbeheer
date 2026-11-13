"""Beheerschermen: indeling, plaatsdetail, boten, leden, beheerders en de technische status.
Schermen over boten en plaatsen tonen de bootmutaties die erbij horen (BLB-025, BLB-043, ADR-006)."""

import json
from functools import partial

import segno
from flask import abort, current_app, flash, g, redirect, render_template, request, url_for
from markupsafe import Markup

from app.domein import (
    Actor,
    Regelfout,
    beheerders,
    bezetting_csv,
    boten,
    csvbestand,
    indeling,
    leden,
    log,
    rekindeling_csv,
    status,
    toewijzing,
    vandaag,
    wachtlijst,
)
from app.domein.csvbestand import CsvFout
from app.web import bp, getal, inloggen_vereist, recent_ingelogd, uitvoeren


def _of_404(functie, *args):
    try:
        return functie(*args)
    except Regelfout:
        abort(404)


# Indeling


def _vakken():
    """De paren (verdieping, vak) uit het raster, waarde "2-3". Een misvormde waarde wordt (0, 0):
    het domein weigert dat met zijn eigen melding."""
    paren = set()
    for waarde in request.form.getlist("vak"):
        try:
            verdieping, vak = (getal(d) for d in waarde.split("-"))
        except ValueError:
            verdieping = vak = 0
        paren.add((verdieping, vak))
    return paren


def _bootsoorten_per_verdieping():
    """{verdieping: id} uit de keuzes bootsoort-<verdieping>. Leeg is geen keuze; tekst die geen
    geldig getal is wordt 0, een id die niet bestaat: het domein weigert dat met zijn melding."""
    keuze = {}
    for verdieping in indeling.VERDIEPINGEN:
        waarde = request.form.get(f"bootsoort-{verdieping}", "")
        if waarde:
            try:
                keuze[verdieping] = getal(waarde)
            except ValueError:
                keuze[verdieping] = 0
    return keuze


def _indeling_scherm(**extra):
    return render_template("indeling.html", rekken=indeling.rekken(), status=indeling.status,
                           bootsoorten=indeling.bootsoorten(),
                           verdiepingen=indeling.VERDIEPINGEN, vakken=indeling.VAKKEN,
                           naam_max=indeling.NAAM_MAX, omschrijving_max=indeling.OMSCHRIJVING_MAX, **extra)


def _import_export_scherm(**extra):
    # Ook de 422 uit een importroute markeert Import/export in het menu (BV-76).
    return render_template("import_export.html", huidig="web.import_export_scherm",
                           csv_max=csvbestand.MAX_BYTES // 1024,
                           lopende_import=bezetting_csv.lopend(), **extra)


@bp.get("/import-export")
@inloggen_vereist
def import_export_scherm():
    return _import_export_scherm()


@bp.get("/indeling")
@inloggen_vereist
def indeling_overzicht():
    return _indeling_scherm()


@bp.get("/rekindeling.csv")
@inloggen_vereist
def rekindeling_export():
    leeg = request.args.get("leeg") == "1"
    try:
        inhoud = rekindeling_csv.export(leeg)
    except Regelfout as fout:
        flash(str(fout), "fout")
        return redirect(url_for("web.import_export_scherm"))
    return inhoud, {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="rekindeling{"-leeg" if leeg else ""}.csv"',
    }


def _csv_data():
    """De inhoud van het geüploade CSV-bestand, of None met een melding (ADR-014 §1)."""
    bestand = request.files.get("bestand")
    if bestand is None or not bestand.filename:
        flash("Kies een CSV-bestand.", "fout")
    elif not bestand.filename.lower().endswith(".csv"):
        flash("Kies een bestand met de extensie .csv.", "fout")
    else:
        # Eén byte meer dan de grens: de import weigert dan, zonder verder te lezen.
        return bestand.stream.read(csvbestand.MAX_BYTES + 1)
    return None


@bp.post("/rekindeling/import")
@inloggen_vereist
@recent_ingelogd
def rekindeling_importeren():
    data = _csv_data()
    if data is not None:
        try:
            n = rekindeling_csv.importeren(data, Actor.van(g.beheerder))
        except CsvFout as fout:
            return _import_export_scherm(import_fouten=fout.regels), 422
        except Regelfout as fout:
            flash(str(fout), "fout")
        else:
            flash(f"De indeling is geïmporteerd. Rekken: {n['rekken_nieuw']} nieuw, "
                  f"{n['rekken_gewijzigd']} gewijzigd. Plaatsen: {n['plaatsen_nieuw']} nieuw, "
                  f"{n['plaatsen_gewijzigd']} gewijzigd.", "info")
    return redirect(url_for("web.import_export_scherm"))


# Bezetting als CSV (issue #158, ADR-014 §3 en §5). Geen naam of veld uit het bestand in een
# flash: de sessiecookie is leesbaar. Het overzicht toont ze, geëscapet, in het antwoord zelf.


@bp.get("/bezetting.csv")
@inloggen_vereist
def bezetting_export():
    leeg = request.args.get("leeg") == "1"
    try:
        inhoud = bezetting_csv.export(leeg)
    except Regelfout as fout:
        flash(str(fout), "fout")
        return redirect(url_for("web.import_export_scherm"))
    return inhoud, {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="bezetting{"-leeg" if leeg else ""}.csv"',
    }


@bp.post("/bezetting/import")
@inloggen_vereist
@recent_ingelogd
def bezetting_uploaden():
    data = _csv_data()
    if data is not None:
        try:
            bezetting_csv.uploaden(data, Actor.van(g.beheerder))
        except CsvFout as fout:
            return _import_export_scherm(import_fouten=fout.regels), 422
        except Regelfout as fout:
            flash(str(fout), "fout")
        else:
            return redirect(url_for("web.bezetting_import"))
    return redirect(url_for("web.import_export_scherm"))


@bp.get("/bezetting/import")
@inloggen_vereist
def bezetting_import():
    overzicht = bezetting_csv.overzicht()
    if overzicht is None:
        flash("Er loopt geen bezettingsimport. Upload een bestand op de pagina Import/export.", "info")
        return redirect(url_for("web.import_export_scherm"))
    return render_template("bezetting_import.html", **overzicht)


@bp.post("/bezetting/import/koppelen")
@inloggen_vereist
def bezetting_koppelen():
    keuzes = {naam.removeprefix("keuze-") if naam.startswith("keuze-") else naam: waarde
              for naam, waarde in request.form.items() if naam.startswith(("keuze-", "soort-"))}
    uitvoeren(bezetting_csv.koppelen, keuzes, gelukt="De keuzes zijn opgeslagen.")
    return redirect(url_for("web.bezetting_import"))


@bp.post("/bezetting/import/bevestigen")
@inloggen_vereist
@recent_ingelogd
def bezetting_bevestigen():
    n = uitvoeren(bezetting_csv.bevestigen)
    if n is None:
        return redirect(url_for("web.bezetting_import"))
    flash(f"De bezetting is geïmporteerd. Nieuwe boten: {n['nieuw']}, toegewezen: "
          f"{n['toegewezen']}, overschreven: {n['overschreven']}, verplaatst: {n['verplaatst']}, "
          f"ongewijzigd: {n['ongewijzigd']}, overgeslagen: {n['overgeslagen']}.", "info")
    return redirect(url_for("web.import_export_scherm"))


@bp.post("/bezetting/import/annuleren")
@inloggen_vereist
def bezetting_annuleren():
    uitvoeren(bezetting_csv.annuleren, gelukt="De import is geannuleerd.")
    return redirect(url_for("web.import_export_scherm"))


@bp.get("/bezetting/koppelingen")
@inloggen_vereist
def bezetting_koppelingen():
    return render_template("bezetting_koppelingen.html", koppelingen=bezetting_csv.koppelingen())


@bp.post("/bezetting/koppelingen/<int:koppeling_id>/verwijderen")
@inloggen_vereist
def bezetting_koppeling_verwijderen(koppeling_id):
    uitvoeren(bezetting_csv.koppeling_verwijderen, koppeling_id,
              gelukt="De koppeling is verwijderd.")
    return redirect(url_for("web.bezetting_koppelingen"))


@bp.get("/rekoverzicht")
@inloggen_vereist
def rekoverzicht():
    return render_template("rekoverzicht.html", rekken=indeling.rekken(),
                           vakken_van=indeling.rekoverzicht)


@bp.post("/rekken")
@inloggen_vereist
def rek_aanmaken():
    uitvoeren(partial(indeling.rek_aanmaken, bootsoort_per_verdieping=_bootsoorten_per_verdieping()),
              request.form.get("naam"), request.form.get("omschrijving"), _vakken(),
              gelukt="Het rek is aangemaakt.")
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/naam")
@inloggen_vereist
def rek_wijzigen(rek_id):
    uitvoeren(indeling.rek_wijzigen, rek_id, request.form.get("naam"),
              request.form.get("omschrijving"), gelukt="Het rek is opgeslagen.")
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/indeling")
@inloggen_vereist
def indeling_instellen(rek_id):
    uitvoeren(indeling.indeling_instellen, rek_id, _vakken(), gelukt="De indeling is opgeslagen.")
    return redirect(url_for("web.indeling_overzicht"))


@bp.post("/rekken/<int:rek_id>/verwijderen")
@inloggen_vereist
def rek_verwijderen(rek_id):
    uitvoeren(indeling.rek_verwijderen, rek_id, gelukt="Het rek is verwijderd.")
    return redirect(url_for("web.indeling_overzicht"))


# Plaatsdetail (BLB-012) en toewijzen (BLB-010)


@bp.get("/plaatsen/<int:plaats_id>")
@inloggen_vereist
def plaats_detail(plaats_id):
    p = _of_404(indeling.plaats, plaats_id)
    # BLB-014: de wachtenden voor een passende bootsoort bovenaan, de langst wachtende eerst.
    # Een clubplaats krijgt nooit een boot van een lid (toewijzen weigert dat), dus geen wachtenden.
    wachtend = sorted((w for s, rij in wachtlijst.lijsten() if s in p.bootsoorten for w in rij),
                      key=lambda w: w.aangemeld_op) if p.boot is None and not p.is_clubplaats else []
    return render_template(
        "plaats.html", plaats=p, oud_lid=p.boot and p.boot.lid and leden.is_oud_lid(p.boot.lid),
        boten=[b for b in boten.zonder_plaats() if toewijzing.past(p, b)] if p.boot is None else [], wachtend=wachtend,
        bootsoorten=indeling.bootsoorten(),
        openbare_url=f"{current_app.config['BASIS_URL']}/p/{p.publieke_sleutel}",
        regels=log.regels([f"plaats:{p.id}"]))


@bp.post("/plaatsen/<int:plaats_id>/toewijzen")
@inloggen_vereist
def plaats_toewijzen(plaats_id):
    uitvoeren(toewijzing.toewijzen, plaats_id, request.form.get("boot_id", type=getal),
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
    uitvoeren(indeling.plaats_wijzigen, plaats_id,
              request.form.getlist("bootsoort", type=getal), "clubplaats" in request.form,
              gelukt="De plaats is opgeslagen.")
    return redirect(url_for("web.plaats_detail", plaats_id=plaats_id))


# Boten (BLB-005)


def _foto():
    bestand = request.files.get("foto")
    return bestand.read() if bestand and bestand.filename else None


@bp.get("/boten")
@inloggen_vereist
def boten_overzicht():
    zoek = request.args.get("zoek", "")
    soort_id = request.args.get("bootsoort", type=getal)
    return render_template("boten.html", boten=boten.boten(zoek, soort_id), zoek=zoek, soort_id=soort_id,
                           bootsoorten=indeling.bootsoorten(), leden=leden.actieve_leden(),
                           regels=log.regels(acties=("boot.",)),
                           nieuw_open=request.args.get("open") == "nieuw")


def _eigenaar(onbekend_mag=True):
    """(lid_id, clubboot) uit het veld eigenaar: een lid, `club`, of `onbekend`. Anders None en
    een melding; de waarde onbekend telt alleen waar de keuzelijst hem biedt (#204)."""
    waarde = request.form.get("eigenaar", "")
    if waarde == "club":
        return None, True
    if waarde == "onbekend" and onbekend_mag:
        return None, False
    if (lid_id := request.form.get("eigenaar", type=getal)) is not None:
        return lid_id, False
    flash("Kies een eigenaar.", "fout")
    return None


@bp.post("/boten")
@inloggen_vereist
def boot_aanmaken():
    # Na een weigering staat het blok Nieuwe boot open, met de melding erboven (#208).
    if (eigenaar := _eigenaar()) is None:
        return redirect(url_for("web.boten_overzicht", open="nieuw"))
    lid_id, clubboot = eigenaar
    b = uitvoeren(partial(boten.boot_aanmaken, clubboot=clubboot), request.form.get("naam"),
                  request.form.get("bootsoort", type=getal), lid_id, _foto(),
                  gelukt="De boot is vastgelegd.")
    if b is None:
        return redirect(url_for("web.boten_overzicht", open="nieuw"))
    return redirect(url_for("web.boot_detail", boot_id=b.id))


@bp.get("/boten/zonder-eigenaar")
@inloggen_vereist
def boten_zonder_eigenaar():
    return render_template("boten_zonder_eigenaar.html", boten=boten.zonder_eigenaar(),
                           leden=leden.actieve_leden())


@bp.post("/boten/<int:boot_id>/eigenaar")
@inloggen_vereist
def boot_eigenaar_kiezen(boot_id):
    naam = _of_404(boten.boot, boot_id).naam
    if (eigenaar := _eigenaar(onbekend_mag=False)) is not None:
        lid_id, clubboot = eigenaar
        uitvoeren(partial(boten.eigenaar_kiezen, clubboot=clubboot), boot_id, lid_id,
                  gelukt=f"De eigenaar van {naam} is opgeslagen.")
    return redirect(url_for("web.boten_zonder_eigenaar"))


@bp.get("/boten/<int:boot_id>")
@inloggen_vereist
def boot_detail(boot_id):
    b = _of_404(boten.boot, boot_id)
    oud_lid = b.lid is not None and leden.is_oud_lid(b.lid)
    # #132, #205: een boot zonder plaats kiest uit de vrije plaatsen die toewijzen accepteert;
    # een clubboot ook uit de clubplaatsen.
    vrij = [] if b.plaats or oud_lid else indeling.vrije_plaatsen(b.bootsoort_id, ook_club=b.clubboot)
    return render_template("boot.html", boot=b, regels=log.regels([f"boot:{b.id}"]),
                           bootsoorten=indeling.bootsoorten(), leden=leden.actieve_leden(),
                           oud_lid=oud_lid, vrij=vrij, vandaag=vandaag(),
                           foto_open=request.args.get("open") == "foto")


@bp.post("/boten/<int:boot_id>/toewijzen")
@inloggen_vereist
def boot_toewijzen(boot_id):
    uitvoeren(toewijzing.toewijzen, request.form.get("plaats_id", type=getal), boot_id,
              gelukt="De boot heeft de plaats gekregen.")
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


@bp.post("/boten/<int:boot_id>")
@inloggen_vereist
def boot_wijzigen(boot_id):
    _of_404(boten.boot, boot_id)
    if (eigenaar := _eigenaar()) is not None:
        lid_id, clubboot = eigenaar
        was_wachtend = boten.boot(boot_id).wachtlijst is not None
        if uitvoeren(partial(boten.boot_wijzigen, clubboot=clubboot), boot_id, request.form.get("naam"),
                     request.form.get("bootsoort", type=getal), lid_id,
                     gelukt="De boot is opgeslagen.") and was_wachtend \
                and boten.boot(boot_id).wachtlijst is None:
            flash("De eigenaar is nu onbekend en de boot is van de wachtlijst gehaald."
                  if lid_id is None and not clubboot else
                  "De boot heeft een andere eigenaar en is van de wachtlijst gehaald.", "info")
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


@bp.post("/boten/<int:boot_id>/foto")
@inloggen_vereist
def boot_foto(boot_id):
    foto = _foto()
    if foto is None:
        flash("Kies een foto.", "fout")
        gelukt = False
    else:
        gelukt = uitvoeren(boten.foto_vervangen, boot_id, foto, gelukt="De foto is opgeslagen.")
    # Na een weigering staat het blok Foto vervangen open, met de melding erboven (#208).
    return redirect(url_for("web.boot_detail", boot_id=boot_id, **({} if gelukt else {"open": "foto"})))


@bp.post("/boten/<int:boot_id>/verwijderen")
@inloggen_vereist
def boot_verwijderen(boot_id):
    if uitvoeren(boten.boot_verwijderen, boot_id, gelukt="De boot is verwijderd.") is None:
        return redirect(url_for("web.boot_detail", boot_id=boot_id))
    return redirect(url_for("web.boten_overzicht"))


# Wachtlijst (BLB-013, BLB-014): de beheerder kiest zelf; de applicatie wijst niet toe


@bp.get("/wachtlijst")
@inloggen_vereist
def wachtlijst_overzicht():
    zoek = request.args.get("zoek", "")
    soort_id = request.args.get("bootsoort", type=getal)
    return render_template("wachtlijst.html", lijsten=wachtlijst.lijsten(zoek, soort_id), zoek=zoek,
                           soort_id=soort_id, bootsoorten=indeling.bootsoorten(),
                           wachttijd=wachtlijst.wachttijd, regels=log.regels(acties=("wachtlijst.",)))


@bp.post("/boten/<int:boot_id>/wachtlijst")
@inloggen_vereist
def boot_op_wachtlijst(boot_id):
    uitvoeren(wachtlijst.erop_zetten, boot_id, request.form.get("aangemeld_op"),
              gelukt="De boot staat op de wachtlijst.")
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


@bp.post("/boten/<int:boot_id>/wachtlijst/verwijderen")
@inloggen_vereist
def boot_van_wachtlijst(boot_id):
    uitvoeren(wachtlijst.eraf_halen, boot_id, gelukt="De boot is van de wachtlijst gehaald.")
    if request.form.get("terug") == "wachtlijst":
        return redirect(url_for("web.wachtlijst_overzicht"))
    return redirect(url_for("web.boot_detail", boot_id=boot_id))


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
    # BLB-019: boten met plaats.
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
    link = f"{current_app.config['BASIS_URL']}/uitnodiging/{code}"
    qr = segno.make(link, error="m").svg_inline(omitsize=True, svgclass="bl-qr").replace(
        "<svg ", '<svg role="img" aria-label="QR-code van de uitnodigingslink" ', 1)
    return render_template("link.html", titel=titel, uitleg=uitleg, link=link, qr=Markup(qr))


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
@recent_ingelogd
def beheerder_wijzigen(beheerder_id, actie):
    uitvoeren(getattr(beheerders, actie), beheerder_id, gelukt={
        "blokkeren": "Het account is geblokkeerd.", "deblokkeren": "Het account is gedeblokkeerd.",
        "verwijderen": "Het account is verwijderd."}[actie])
    return redirect(url_for("web.beheerders_overzicht"))


# Technische status (BLB-037)


@bp.get("/status.json")
@bp.get("/status")  # de eerste regel: url_for geeft /status
@inloggen_vereist
def statuspagina():
    """HTML en JSON uit dezelfde gegevens, zodat ze niet uit elkaar lopen (ADR-010)."""
    s = status.status()
    if request.path.endswith(".json"):
        return current_app.response_class(
            json.dumps(s, default=lambda t: t.isoformat(), ensure_ascii=False),
            mimetype="application/json")
    return render_template("status.html", s=s)
