"""Inloggen, uitloggen, het instellen van een inlogmethode via een uitnodiging en het profiel
met de eigen inlogmethodes (ADR-001, BLB-038)."""

import time

import segno
from cryptography.fernet import Fernet
from flask import (
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

from app.domein import Actor, Regelfout, beheerders
from app.web import bp, getal, inloggen_vereist, recent_ingelogd, start_sessie

MISLUKT = (
    "Inloggen is mislukt. Na vijf fouten is inloggen met wachtwoord 15 minuten geblokkeerd."
)
TOTP_STAP_GELDIG = 300  # seconden tussen wachtwoord en TOTP-code


def _json(opties_json, challenge):
    session["webauthn_challenge"] = bytes_to_base64url(challenge)
    return current_app.response_class(opties_json, mimetype="application/json")


def _challenge():
    waarde = session.pop("webauthn_challenge", None)
    return base64url_to_bytes(waarde) if waarde else None


# Inloggen


@bp.get("/inloggen")
def inloggen():
    if g.beheerder:
        return redirect(url_for("web.rekoverzicht"))
    return render_template("inloggen.html")


@bp.post("/inloggen")
def inloggen_wachtwoord():
    b = beheerders.wachtwoord_controleren(
        request.form.get("gebruikersnaam", "").strip(), request.form.get("wachtwoord", "")
    )
    if not b:
        flash(MISLUKT, "fout")
        return redirect(url_for("web.inloggen"))
    session.clear()
    session.update(totp_beheerder=b.id, totp_tot=int(time.time()) + TOTP_STAP_GELDIG)
    return redirect(url_for("web.inloggen_code"))


@bp.route("/inloggen/code", methods=["GET", "POST"])
def inloggen_code():
    beheerder_id = session.get("totp_beheerder")
    if not beheerder_id or time.time() > session.get("totp_tot", 0):
        session.clear()
        return redirect(url_for("web.inloggen"))
    if request.method == "GET":
        return render_template("code.html")
    b = beheerders.totp_controleren(beheerder_id, request.form.get("code", ""))
    if not b:
        flash(MISLUKT, "fout")
        return redirect(url_for("web.inloggen_code"))
    start_sessie(b)
    return redirect(url_for("web.rekoverzicht"))


@bp.post("/inloggen/passkey/opties")
def inloggen_passkey_opties():
    return _json(*beheerders.passkey_inlogopties())


@bp.post("/inloggen/passkey")
def inloggen_passkey():
    challenge = _challenge()
    credential = request.get_json(silent=True)
    b = beheerders.passkey_inloggen(credential, challenge) if challenge and credential else None
    if not b:
        return jsonify(fout=MISLUKT), 400
    start_sessie(b)
    return jsonify(url=url_for("web.rekoverzicht"))


@bp.post("/uitloggen")
@inloggen_vereist
def uitloggen():
    beheerders.uitloggen(g.beheerder)
    session.clear()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("web.inloggen"))


# Uitnodiging: een inlogmethode instellen


def _fernet():
    return Fernet(current_app.config["TOTP_SLEUTEL"])


def _nieuw_geheim(gebruikersnaam):
    """(geheim, QR als data-URI). Het nieuwe geheim staat versleuteld in de sessie tot de
    beheerder het activeert."""
    if "totp_nieuw" not in session:
        geheim = beheerders.nieuw_totp_geheim()
        session["totp_nieuw"] = _fernet().encrypt(geheim.encode()).decode()
    geheim = _fernet().decrypt(session["totp_nieuw"].encode()).decode()
    return geheim, segno.make(beheerders.totp_uri(geheim, gebruikersnaam)).svg_data_uri(scale=5)


@bp.get("/uitnodiging/<code>")
def uitnodiging(code):
    try:
        b = beheerders.uitnodiging(code).beheerder
    except Regelfout as fout:
        return render_template("melding.html", melding=str(fout)), 404
    geheim, qr = _nieuw_geheim(b.gebruikersnaam)
    return render_template("uitnodiging.html", beheerder=b, code=code, geheim=geheim, qr=qr)


@bp.post("/uitnodiging/<code>/wachtwoord")
def uitnodiging_wachtwoord(code):
    if "totp_nieuw" not in session:
        return redirect(url_for("web.uitnodiging", code=code))
    if request.form.get("wachtwoord") != request.form.get("herhaling"):
        flash("De twee wachtwoorden zijn niet gelijk.", "fout")
        return redirect(url_for("web.uitnodiging", code=code))
    geheim = _fernet().decrypt(session["totp_nieuw"].encode()).decode()
    try:
        b = beheerders.wachtwoord_instellen(
            code, request.form.get("wachtwoord", ""), geheim, request.form.get("code", "")
        )
    except Regelfout as fout:
        flash(str(fout), "fout")
        return redirect(url_for("web.uitnodiging", code=code))
    start_sessie(b)
    return redirect(url_for("web.rekoverzicht"))


@bp.post("/uitnodiging/<code>/passkey/opties")
def uitnodiging_passkey_opties(code):
    try:
        return _json(*beheerders.passkey_registratieopties(code))
    except Regelfout as fout:
        return jsonify(fout=str(fout)), 404


@bp.post("/uitnodiging/<code>/passkey")
def uitnodiging_passkey(code):
    challenge = _challenge()
    credential = request.get_json(silent=True)
    if not challenge or not credential:
        return jsonify(fout="Start het registreren opnieuw."), 400
    try:
        b = beheerders.passkey_registreren(code, credential, challenge)
    except Regelfout as fout:
        return jsonify(fout=str(fout)), 400
    start_sessie(b)
    return jsonify(url=url_for("web.rekoverzicht"))


# Profiel: eigen inlogmethodes toevoegen of intrekken (BLB-038). Toevoegen en intrekken vragen
# een inlog van hooguit 10 minuten geleden; intrekken beëindigt alle eigen sessies (ADR-001).


@bp.get("/profiel")
@inloggen_vereist
def profiel():
    b = g.beheerder
    geheim = qr = None
    if not b.wachtwoordhash:
        geheim, qr = _nieuw_geheim(b.gebruikersnaam)
    return render_template("profiel.html", beheerder=b, geheim=geheim, qr=qr)


@bp.post("/profiel/passkey/opties")
@inloggen_vereist
@recent_ingelogd
def profiel_passkey_opties():
    return _json(*beheerders.registratieopties(g.beheerder))


@bp.post("/profiel/passkey")
@inloggen_vereist
@recent_ingelogd
def profiel_passkey():
    challenge = _challenge()
    credential = request.get_json(silent=True)
    if not challenge or not credential:
        return jsonify(fout="Start het toevoegen opnieuw."), 400
    try:
        beheerders.passkey_toevoegen(credential, challenge, Actor.van(g.beheerder))
    except Regelfout as fout:
        return jsonify(fout=str(fout)), 400
    flash("De passkey is toegevoegd.", "info")
    return jsonify(url=url_for("web.profiel"))


@bp.post("/profiel/wachtwoord")
@inloggen_vereist
@recent_ingelogd
def profiel_wachtwoord():
    if "totp_nieuw" not in session:
        return redirect(url_for("web.profiel"))
    if request.form.get("wachtwoord") != request.form.get("herhaling"):
        flash("De twee wachtwoorden zijn niet gelijk.", "fout")
        return redirect(url_for("web.profiel"))
    geheim = _fernet().decrypt(session["totp_nieuw"].encode()).decode()
    try:
        beheerders.wachtwoord_toevoegen(request.form.get("wachtwoord", ""), geheim,
                                        request.form.get("code", ""), Actor.van(g.beheerder))
    except Regelfout as fout:
        flash(str(fout), "fout")
        return redirect(url_for("web.profiel"))
    session.pop("totp_nieuw")
    flash("Wachtwoord en code zijn ingesteld.", "info")
    return redirect(url_for("web.profiel"))


@bp.post("/profiel/intrekken")
@inloggen_vereist
@recent_ingelogd
def profiel_intrekken():
    keuze = request.form.get("methode", "")
    passkey_id = None if keuze == "wachtwoord" else request.form.get("methode", type=getal)
    if keuze != "wachtwoord" and passkey_id is None:
        flash("Kies een inlogmethode.", "fout")
        return redirect(url_for("web.profiel"))
    try:
        beheerders.methode_intrekken(passkey_id, Actor.van(g.beheerder))
    except Regelfout as fout:
        flash(str(fout), "fout")
        return redirect(url_for("web.profiel"))
    session.clear()
    flash("De inlogmethode is ingetrokken. Log opnieuw in met een methode die je nog hebt.", "info")
    return redirect(url_for("web.inloggen"))
