"""Tokenschermen (BLB-030, BLB-031, BLB-032, BLB-035; ADR-005 v1.4.0). Elke beheerder ziet en
beheert alle tokens. Maken, rechten wijzigen en intrekken vragen een recente inlog (ADR-001)."""

from flask import current_app, flash, redirect, render_template, request, url_for

from app.domein import tokens
from app.web import bp, inloggen_vereist, recent_ingelogd, uitvoeren


@bp.get("/tokens")
@inloggen_vereist
def tokens_overzicht():
    return render_template("tokens.html", tokens=tokens.alle(), rechten=tokens.WEBRECHTEN)


def _formulier(invoer):
    return render_template("token_nieuw.html", invoer=invoer, rechten=tokens.WEBRECHTEN,
                           standaard=tokens.STANDAARD_DAGEN, max_dagen=tokens.MAX_DAGEN)


@bp.route("/tokens/nieuw", methods=["GET", "POST"])
@inloggen_vereist
@recent_ingelogd
def token_nieuw():
    if request.method == "GET":
        return _formulier({"soort": "persoonlijk", "dagen": tokens.STANDAARD_DAGEN,
                           "rechten": [], "whitelist": current_app.config["KOPPELNET"]})
    f = request.form
    invoer = {"soort": f.get("soort", ""), "naam": f.get("naam", "").strip(),
              "dagen": f.get("dagen", ""), "rechten": f.getlist("recht"),
              "whitelist": f.get("whitelist", "")}
    dagen = f.get("dagen", type=int)
    if dagen is None:
        flash("Geldigheid: geef een aantal dagen.", "fout")
        return _formulier(invoer)
    whitelist = [r for r in invoer["whitelist"].split(",") if r.strip()]
    waarde = uitvoeren(tokens.maken, invoer["soort"], invoer["naam"], invoer["rechten"],
                       whitelist, dagen)
    if waarde is None:
        return _formulier(invoer)
    # De waarde staat alleen in dit antwoord: geen redirect, geen flash in de sessiecookie, en
    # Cache-Control: no-store zet bp.after_request op elke beheerpagina.
    return render_template("token_waarde.html", naam=invoer["naam"], waarde=waarde)


@bp.post("/tokens/<int:token_id>/rechten")
@inloggen_vereist
@recent_ingelogd
def token_rechten(token_id):
    uitvoeren(tokens.rechten_wijzigen, token_id, request.form.getlist("recht"),
              gelukt="De rechten zijn gewijzigd. Ze gelden vanaf de volgende aanroep.")
    return redirect(url_for("web.tokens_overzicht"))


@bp.post("/tokens/<int:token_id>/intrekken")
@inloggen_vereist
@recent_ingelogd
def token_intrekken(token_id):
    uitvoeren(tokens.intrekken, token_id, gelukt="Het token is ingetrokken.")
    return redirect(url_for("web.tokens_overzicht"))
