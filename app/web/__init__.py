"""Webinterface. Slice 1a: inloggen, uitnodiging, startpagina en log."""

import time
from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, g, redirect, render_template, session, url_for

from app.domein import log
from app.models import Beheerder, Instelling, db

bp = Blueprint("web", __name__)

SESSIEDUUR = 12 * 3600


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
    response.headers["Cache-Control"] = "no-store"
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
        "start.html", regels=log.regels(f"beheerder:{g.beheerder.id}", limiet=10)
    )


@bp.get("/log")
@inloggen_vereist
def logboek():
    return render_template("log.html", regels=log.regels())


from app.web import inloggen  # noqa: F401  routes op bp
from app.web.health import health  # noqa: F401
