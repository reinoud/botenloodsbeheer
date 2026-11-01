"""API /api/v1 (ADR-005, ADR-012). Alleen de dienst api registreert deze blueprint; Traefik
stuurt alleen het entrypoint intern op poort 8081 hierheen (ADR-013). Contract: openapi.yaml."""

from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.domein import leden, tokens

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


@bp.errorhandler(RequestEntityTooLarge)
def te_groot(_fout):
    return {"fout": "Het verzoek is groter dan 2 MB."}, 413


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
