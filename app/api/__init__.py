"""API /api/v1 (ADR-005, ADR-012). Alleen de dienst api registreert deze blueprint; Nginx
stuurt alleen de interne server op poort 8081 hierheen. Contract: openapi.yaml."""

from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, request

from app.domein import tokens

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
