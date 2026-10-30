"""Webinterface: inloggen, indeling, boten, leden, openbare pagina en log."""

import time
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
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

from app.domein import Actor, Regelfout, log
from app.models import Beheerder, Instelling, db

bp = Blueprint("web", __name__)

SESSIEDUUR = 12 * 3600
RECENT = 10 * 60  # recente inlog vereist voor inlogmethodes, uitnodigen en herstellen (ADR-001)
OPNIEUW = "Log opnieuw in om je inlogmethodes te wijzigen. Je inlog is ouder dan 10 minuten."


@bp.before_request
def laad_beheerder():
    """Elk verzoek controleert of het account actief is en de sessieversie klopt (ADR-001)."""
    g.beheerder = None
    beheerder_id = session.get("beheerder_id")
    if beheerder_id is None:
        return
    b = db.session.get(Beheerder, beheerder_id)
    if (
        not b
        or not b.actief
        or b.sessieversie != session.get("sessieversie")
        or time.time() - session.get("ingelogd_op", 0) > SESSIEDUUR
    ):
        session.clear()
        return
    g.beheerder = b


@bp.after_request
def niet_bewaren(response):
    # Beheerpagina's en het TOTP-geheim bij het instellen horen niet in een browsercache.
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def start_sessie(beheerder):
    session.clear()
    session.permanent = True
    session.update(
        beheerder_id=beheerder.id,
        sessieversie=beheerder.sessieversie,
        ingelogd_op=int(time.time()),
    )


def inloggen_vereist(view):
    @wraps(view)
    def binnen(*args, **kwargs):
        if g.beheerder is None:
            return redirect(url_for("web.inloggen"))
        return view(*args, **kwargs)

    return binnen


def recent_ingelogd(view):
    """Na inloggen_vereist: de inlog is hooguit 10 minuten oud, anders opnieuw inloggen."""

    @wraps(view)
    def binnen(*args, **kwargs):
        if time.time() - session.get("ingelogd_op", 0) > RECENT:
            session.clear()
            flash(OPNIEUW, "info")
            if request.is_json:
                return jsonify(fout=OPNIEUW, url=url_for("web.inloggen")), 401
            return redirect(url_for("web.inloggen"))
        return view(*args, **kwargs)

    return binnen


def uitvoeren(functie, *args, gelukt=None):
    """Roept een wijzigende domeinfunctie aan met de ingelogde beheerder als actor. Een
    Regelfout wordt een foutmelding (ADR-002); geeft dan None."""
    try:
        resultaat = functie(*args, Actor.van(g.beheerder))
    except Regelfout as fout:
        flash(str(fout), "fout")
        return None
    if gelukt:
        flash(gelukt, "info")
    return resultaat


@bp.app_context_processor
def vereniging():
    naam = db.session.get(Instelling, "naam")
    return {"vereniging": naam.waarde if naam else "Botenloods"}


@bp.app_template_filter("tijd")
def tijd(waarde):
    return waarde.astimezone(ZoneInfo(current_app.config["TZ"])).strftime("%d-%m-%Y %H:%M")


@bp.get("/")
@inloggen_vereist
def start():
    return render_template(
        "start.html", regels=log.regels([f"beheerder:{g.beheerder.id}"], limiet=10)
    )


@bp.get("/log")
@inloggen_vereist
def logboek():
    return render_template("log.html", regels=log.regels())


from app.web import beheer, inloggen, openbaar  # noqa: F401  routes op bp
from app.web.health import health  # noqa: F401
