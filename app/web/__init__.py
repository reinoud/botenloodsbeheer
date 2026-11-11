"""Webinterface: inloggen, indeling, boten, leden, openbare pagina en log."""

import time
from functools import wraps
from itertools import groupby
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
from werkzeug.exceptions import RequestEntityTooLarge

from app import INT_MAX
from app.domein import Actor, Regelfout, afbeeldingen, boten, instellingen, log
from app.models import Beheerder, db

bp = Blueprint("web", __name__)

SESSIEDUUR = 12 * 3600
# Recente inlog vereist voor elke route met blijvend effect op toegang of instellingen (ADR-001).
RECENT = 10 * 60
OPNIEUW = "Je inlog is ouder dan 10 minuten. Log opnieuw in en probeer het nog eens."


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


# app_errorhandler: MAX_CONTENT_LENGTH weigert al vóór de route en vóór CSRF. Terug naar het formulier
# met een melding en het blok open; elders blijft het de standaard 413.
@bp.app_errorhandler(RequestEntityTooLarge)
def bestand_te_groot(fout):
    # Lichaam weglezen, om dezelfde reden als in app.api (#91). Traefik begrenst het op 25 MB.
    while request.environ["wsgi.input"].read(65536):
        pass
    if "beheerder_id" not in session:  # geen flash voor wie niet is ingelogd
        return fout
    if request.endpoint == "web.logo_opslaan":
        doel, vorige = url_for("web.instellingen_scherm", open="logo"), instellingen.logo() is not None
    elif request.endpoint == "web.boot_foto":
        boot_id = request.view_args["boot_id"]
        doel, vorige = url_for("web.boot_detail", boot_id=boot_id, open="foto"), boten.heeft_foto(boot_id)
    elif request.endpoint == "web.boot_aanmaken":
        doel, vorige = url_for("web.boten_overzicht", open="nieuw"), False
    else:
        return fout
    flash(afbeeldingen.TE_GROOT + afbeeldingen.VORIGE * vorige, "fout")
    return redirect(doel)


@bp.app_context_processor
def naam_en_logo():
    """Naam en logo voor elke pagina (BLB-027)."""
    # Het aantal boten zonder eigenaar staat in het menu (#204); zonder beheerder is er geen menu.
    return {"vereniging": instellingen.huidig()["naam"], "logo": instellingen.logo(),
            "zonder_eigenaar": boten.aantal_zonder_eigenaar() if g.get("beheerder") else 0}


DAGEN = ("maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag")
MAANDEN = ("januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
           "september", "oktober", "november", "december")


@bp.app_template_filter("lokaal")
def lokaal(waarde):
    """Het tijdstip in de tijdzone van de installatie (TZ), niet in UTC."""
    return waarde.astimezone(ZoneInfo(current_app.config["TZ"]))


@bp.app_template_filter("tijd")
def tijd(waarde):
    return lokaal(waarde).strftime("%d-%m-%Y %H:%M")


@bp.app_template_filter("per_dag")
def per_dag(regels):
    """Regels die al op tijd gesorteerd zijn, als (lokale dag, regels) per dag."""
    return [(dag, list(rij)) for dag, rij in groupby(regels, key=lambda r: lokaal(r.tijdstip).date())]


@bp.app_template_filter("dagkop")
def dagkop(dag):
    return f"{DAGEN[dag.weekday()]} {dag.day} {MAANDEN[dag.month - 1]} {dag.year}"


@bp.get("/")
@inloggen_vereist
def start():
    """Geen startpagina (BV-64): een beheerder komt op het rekoverzicht, een bezoeker op het inloggen."""
    return redirect(url_for("web.rekoverzicht"))


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
