"""Webinterface: inloggen, indeling, boten, leden, openbare pagina en log."""

import time
from functools import wraps
from itertools import groupby
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    abort,
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


# De endpoints die een kijker mag openen; alles wat hier niet in staat is voor hem dicht, ook een nieuwe
# route (ADR-015). Alleen de POST-routes onder Eigen inlog mag een kijker doen (besluit 8, #322).
KIJKER_TOEGESTAAN = frozenset(f"web.{naam}" for naam in (
    # Inzien
    "start", "rekoverzicht", "vrije_plaatsen", "boten_overzicht", "boten_zonder_plaats", "boot_detail", "plaats_detail", "zoeken",
    "afbeelding", "logo", "openbare_plaats",
    # Eigen inlog: de endpoints van app/web/inloggen.py
    "inloggen", "inloggen_wachtwoord", "inloggen_code", "inloggen_passkey_opties", "inloggen_passkey",
    "uitloggen", "uitnodiging", "uitnodiging_wachtwoord", "uitnodiging_passkey_opties",
    "uitnodiging_passkey", "profiel", "profiel_passkey_opties", "profiel_passkey", "profiel_wachtwoord",
    "profiel_intrekken"))


def getal(waarde):
    """type= voor querystring en formulier: buiten integer van PostgreSQL geeft Werkzeug de
    standaardwaarde, net als bij tekst die geen getal is (#74)."""
    n = int(waarde)
    if not -INT_MAX - 1 <= n <= INT_MAX:
        raise ValueError(waarde)
    return n


def _sessiebeheerder():
    """De beheerder van de sessie: actief account, sessieversie en sessieduur kloppen (ADR-001); de rol komt uit
    de database, nooit uit de cookie. Anders None, en een ongeldige sessie wordt gewist."""
    beheerder_id = session.get("beheerder_id")
    if beheerder_id is None:
        return None
    b = db.session.get(Beheerder, beheerder_id)
    if (
        not b
        or not b.actief
        or b.sessieversie != session.get("sessieversie")
        or time.time() - session.get("ingelogd_op", 0) > SESSIEDUUR
    ):
        session.clear()
        return None
    return b


@bp.before_request
def laad_beheerder():
    """Elk verzoek leest de beheerder uit de sessie en weigert een kijker buiten KIJKER_TOEGESTAAN (ADR-015)."""
    g.beheerder = b = _sessiebeheerder()
    # Een onbekende rol valt ook onder de weigering.
    if b and b.rol != "beheerder" and request.endpoint not in KIJKER_TOEGESTAAN:
        abort(403)


@bp.app_template_global("is_kijker")
def is_kijker():
    """Ingelogd zonder de rol beheerder: de schermen tonen dan geen knoppen, leden of lidnummers."""
    return g.get("beheerder") is not None and g.beheerder.rol != "beheerder"


@bp.app_template_global("kijker_mag")
def kijker_mag(endpoint):
    """Het menu toont een kijker alleen de items die hij mag openen (BV-100)."""
    return endpoint in KIJKER_TOEGESTAAN


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


def veilig_doel(doel):
    """Het doel na het inloggen als het een pad binnen de applicatie is, anders None (open redirect, #354).
    Eén `/` aan het begin, geen `\\` en geen stuurtekens; ook niet na het decoderen (`%0d`, `/%2f`, `/%5c`)."""
    if not isinstance(doel, str) or len(doel) > 1000:
        return None
    for tekst in (doel, unquote(doel)):
        if not tekst.startswith("/") or tekst.startswith("//") or "\\" in tekst \
                or any(ord(c) < 32 or ord(c) == 127 for c in tekst):
            return None
    return doel


def inlogdoel():
    """Waar de gebruiker na het inloggen heen moet: bij een GET de opgevraagde pagina, anders (formulier of
    fetch) de pagina uit de Referer van dezelfde host. None zonder bruikbaar doel (#354)."""
    if request.method == "GET":
        return veilig_doel(request.full_path.removesuffix("?"))
    deel = urlsplit(request.headers.get("Referer", ""))
    if deel.netloc != request.host:
        return None
    return veilig_doel(deel.path + ("?" + deel.query if deel.query else ""))


def naar_inloggen():
    """De URL van het inlogscherm met het doel, als dat er is."""
    return url_for("web.inloggen", volgende=inlogdoel())


def inloggen_vereist(view):
    @wraps(view)
    def binnen(*args, **kwargs):
        if g.beheerder is None:
            return redirect(naar_inloggen())
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
                return jsonify(fout=OPNIEUW, url=naar_inloggen()), 401
            return redirect(naar_inloggen())
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


FOUTEN = {400: ("Ongeldig verzoek", "Deze aanvraag klopt niet. Ga terug en probeer het opnieuw."),
          403: ("Geen toegang", "Met je account kun je deze pagina niet openen."),
          404: ("Pagina niet gevonden",
                "Dit adres leidt nergens heen. Misschien is de link verouderd of staat er een tikfout in.")}


# app_errorhandler: een onbekend adres raakt geen view van de blueprint, dus before_request is niet gelopen
# en g.beheerder niet gezet. De sessie lezen we hier opnieuw, zonder de kijkerweigering (BV-95, #341).
# De dienst api registreert deze blueprint niet en houdt zijn eigen JSON-fouten.
@bp.app_errorhandler(400)
@bp.app_errorhandler(403)
@bp.app_errorhandler(404)
def foutpagina(fout):
    g.beheerder = _sessiebeheerder()
    kop, tekst = FOUTEN[fout.code]
    # no-store zoals niet_bewaren: die after_request van het blueprint loopt niet bij een onbekend adres.
    return (render_template("fout.html", foutcode=fout.code, kop=kop, tekst=tekst), fout.code,
            {"Cache-Control": "no-store"})


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


bp.add_app_template_filter(log.actietekst, "actietekst")
bp.add_app_template_filter(lambda regels: log.namen(regels, met_leden=not is_kijker()), "lognamen")
bp.add_app_template_filter(lambda regels: log.zichtbaar(regels, met_leden=not is_kijker()), "logzichtbaar")
bp.add_app_template_filter(log.betreft, "betreft")


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
