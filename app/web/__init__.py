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

from app import INT_MAX
from app.domein import Actor, Regelfout, instellingen, log
from app.models import Beheerder, db

bp = Blueprint("web", __name__)

SESSIEDUUR = 12 * 3600
# Recente inlog vereist voor inlogmethodes, uitnodigen, herstellen en instellingen (ADR-001).
RECENT = 10 * 60
OPNIEUW = "Log opnieuw in om dit te wijzigen. Je inlog is ouder dan 10 minuten."


def getal(waarde):
    """type= voor querystring en formulier: buiten integer van PostgreSQL geeft Werkzeug de
    standaardwaarde, net als bij tekst die geen getal is (#74)."""
    n = int(waarde)
    if not -INT_MAX - 1 <= n <= INT_MAX:
        raise ValueError(waarde)
    return n


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
def naam_en_logo():
    """Naam en logo voor elke pagina; de kleuren komen via /huisstijl.css (BLB-027)."""
    logo = current_app.extensions.get("logo")
    return {"vereniging": instellingen.huidig()["naam"], "logo": logo[0] if logo else None}


@bp.app_template_filter("tijd")
def tijd(waarde):
    return waarde.astimezone(ZoneInfo(current_app.config["TZ"])).strftime("%d-%m-%Y %H:%M")


@bp.get("/")
@inloggen_vereist
def start():
    return render_template("start.html")


PER_PAGINA = 50


def _logpagina(technisch):
    # Bovengrens houdt de offset binnen bigint; zoveel pagina's krijgt het log in 5 jaar niet.
    pagina = min(max(request.args.get("pagina", 1, type=int), 1), 100_000)
    regels = log.regels(limiet=PER_PAGINA + 1, overslaan=(pagina - 1) * PER_PAGINA,
                        technisch=technisch)
    return render_template("log.html", regels=regels[:PER_PAGINA], technisch=technisch,
                           pagina=pagina, ouder=len(regels) > PER_PAGINA)


@bp.get("/log")
@inloggen_vereist
def logboek():
    return _logpagina(technisch=False)


@bp.get("/log/techniek")
@inloggen_vereist
def technisch_log():
    return _logpagina(technisch=True)


from app.web import beheer, huisstijl, inloggen, openbaar, overzichten, tokenschermen  # noqa: F401
from app.web.health import health  # noqa: F401
