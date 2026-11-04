"""API /api/v1 (ADR-005, ADR-012). Alleen de dienst api registreert deze blueprint; Traefik
stuurt het entrypoint intern op poort 8081 hierheen, en met compose.api-extern.yml ook websecure
(ADR-013). Contract: openapi.yaml."""

from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.domein import boten, leden, tokens, uitlezen

bp = Blueprint("api", __name__, url_prefix="/api/v1")

# Eén tekst voor elke weigering, zodat het antwoord niet verraadt welke controle faalde.
GEEN_TOEGANG = {"fout": "Geen toegang."}


def aanroep(recht=None):
    """Controle per aanroep (ADR-005); recht None: elk geldig token. Een geslaagde aanroep werkt
    alleen laatst_gebruikt_op bij, zonder logregel (ADR-005 v1.2.0)."""

    def deco(view):
        @wraps(view)
        def binnen(*args, **kwargs):
            try:
                token = tokens.controleer(request.headers.get("Authorization"),
                                          request.remote_addr, recht, request.path)
            except tokens.Geweigerd as w:
                return GEEN_TOEGANG, w.status
            antwoord = view(token, *args, **kwargs)
            tokens.gebruikt(token)
            return antwoord

        return binnen

    return deco


@bp.after_request
def niet_bewaren(response):
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@bp.get("/ik")
@aanroep()
def ik(token):
    tz = ZoneInfo(current_app.config["TZ"])
    return {"token": token.naam, "rechten": token.rechten,
            "verloopt_op": token.verloopt_op.astimezone(tz).date().isoformat()}


# app_errorhandler: de 413 ontstaat al in before_request, ook op paden zonder view (#91).
@bp.app_errorhandler(RequestEntityTooLarge)
def te_groot(_fout):
    # Lichaam weglezen: sluit Gunicorn met ongelezen data, dan stuurt de kernel een RST en geeft
    # Traefik 502 in plaats van deze 413 (#91). Traefik begrenst het lichaam op 3 MB.
    while request.environ["wsgi.input"].read(65536):
        pass
    return {"fout": "Het verzoek is groter dan 2 MB."}, 413


# app_errorhandler: een onbekend pad of een verkeerde methode raakt geen view van de blueprint, en
# alleen de dienst api registreert hem (#68).
@bp.app_errorhandler(404)
def onbekend_pad(_fout):
    return {"fout": "Onbekend pad."}, 404


@bp.app_errorhandler(405)
def verkeerde_methode(fout):
    allow = ", ".join(fout.valid_methods or ())
    return {"fout": "Deze methode kan niet op dit pad."}, 405, {"Allow": allow}


def _veld(naam):
    gegevens = request.get_json(silent=True)
    return gegevens.get(naam) if isinstance(gegevens, dict) else None


@bp.get("/leden/importverzoek")
@aanroep("leden:importeren")
def importverzoek(_token):
    return {"aangevraagd": leden.import_aangevraagd()}


@bp.put("/leden")
@aanroep("leden:importeren")
def leden_importeren(_token):
    """De volledige lijst uit de bron (ADR-012). Wijzigingen in leden komen niet in het log;
    boten die daardoor van de wachtlijst gaan wel, met het token als actor (#27)."""
    try:
        return leden.importeer(_veld("leden"), tokens.als_actor(_token))
    except leden.Ongeldig as fout:
        return {"fout": str(fout)}, 422
    except (leden.ImportLoopt, leden.Veiligheidsgrens) as fout:
        return {"fout": str(fout)}, 409


@bp.post("/leden/import-mislukt")
@aanroep("leden:importeren")
def import_mislukt(_token):
    try:
        leden.import_mislukt(_veld("reden"))
    except leden.Ongeldig as fout:
        return {"fout": str(fout)}, 422
    return {}, 201


@bp.get("/bootaantallen")
@aanroep("bootaantallen:lezen")
def bootaantallen(_token):
    """Per lid het aantal boten met een plaats per bootsoort (BLB-009); terugschrijven doet de
    integratiecontainer pas als de vereniging dat aanzet (ADR-004)."""
    return boten.bootaantallen_ophalen()


# Leesaanroepen (ADR-012 v1.6.0): de hele lijst, zonder filters. persoonsgegevens voegt velden toe.


def _met_persoonsgegevens(token):
    return "persoonsgegevens" in token.rechten


@bp.get("/plaatsen")
@aanroep("plaatsen:lezen")
def plaatsen(_token):
    return uitlezen.plaatsen()


@bp.get("/boten")
@aanroep("boten:lezen")
def boten_lezen(token):
    return uitlezen.boten(_met_persoonsgegevens(token))


@bp.get("/leden")
@aanroep("leden:lezen")
def leden_lezen(token):
    return uitlezen.leden(_met_persoonsgegevens(token))


@bp.get("/wachtlijst")
@aanroep("wachtlijst:lezen")
def wachtlijst(token):
    return uitlezen.wachtlijst(_met_persoonsgegevens(token))
