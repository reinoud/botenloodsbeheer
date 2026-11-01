"""API-tokens (ADR-005, ADR-012): robottoken maken en intrekken, controle per aanroep en de
logregel van elke weigering. Persoonlijke tokens en de tokenschermen volgen in slice 10."""

import base64
import hashlib
import hmac
import ipaddress
import re
import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app
from sqlalchemy import select

from app.domein import Actor, Regelfout, log
from app.models import Token, db

# Vaste lijst in code (ADR-005, ADR-009).
RECHTEN = ("plaatsen:lezen", "boten:lezen", "leden:lezen", "wachtlijst:lezen",
           "persoonsgegevens", "leden:importeren", "bootaantallen:lezen")
MAX_DAGEN = 3 * 365  # hooguit 3 jaar (besluit stakeholder, vraag 1)
STANDAARD_DAGEN = 365
NAAM = re.compile(r"[a-z0-9._-]{2,50}")
VOORVOEGSEL = "blb_"
TOKEN = re.compile(r"blb_([A-Z2-7]{8})[A-Z2-7]{52}")


class Geweigerd(Exception):
    """Een geweigerde aanroep. De reden komt in het log, niet in het antwoord (ADR-005)."""

    def __init__(self, reden, status=401):
        super().__init__(reden)
        self.reden, self.status = reden, status


def _nu():
    return datetime.now(UTC)


def _b32(n):
    return base64.b32encode(secrets.token_bytes(n)).decode().rstrip("=")


def _hash(waarde):
    return hashlib.sha256(waarde.encode()).hexdigest()


def als_actor(token):
    return Actor("token", token.id, token.naam)


def whitelist_lezen(reeksen):
    """Adressen en reeksen in CIDR-notatie, IPv4 en IPv6 (BLB-033). Een reeks met hostbits
    weigeren we, net als PostgreSQL cidr: dan is niet duidelijk welke reeks bedoeld is."""
    try:
        return [ipaddress.ip_network(r.strip()) for r in reeksen]
    except ValueError:
        raise Regelfout("Whitelist: alleen IPv4- of IPv6-adressen of reeksen zoals "
                        "10.203.0.0/24 of fd00::/64.") from None


def robot_maken(naam, rechten, whitelist, dagen, actor):
    """Maakt een robottoken en geeft de waarde terug; die is daarna nergens meer te zien.
    Zonder whitelist het netwerk van de integratiecontainer (KOPPELNET), zonder dagen 365."""
    if not NAAM.fullmatch(naam):
        raise Regelfout("Naam: 2 tot 50 tekens, alleen a-z, cijfers, punt, - en _.")
    rechten = list(dict.fromkeys(rechten))
    if not rechten:
        raise Regelfout("Kies minstens één recht.")
    if onbekend := [r for r in rechten if r not in RECHTEN]:
        raise Regelfout(f"Onbekend recht: {', '.join(onbekend)}. Kies uit: {', '.join(RECHTEN)}.")
    netten = whitelist_lezen(whitelist or [current_app.config["KOPPELNET"]])
    dagen = STANDAARD_DAGEN if dagen is None else dagen
    if not 1 <= dagen <= MAX_DAGEN:
        raise Regelfout(f"Geldigheid: 1 tot en met {MAX_DAGEN} dagen (3 jaar).")
    if db.session.scalar(select(Token.id).where(Token.naam == naam)):
        raise Regelfout("Er is al een token met deze naam.")

    prefix = _b32(5)
    waarde = f"{VOORVOEGSEL}{prefix}{_b32(32)}"
    token = Token(naam=naam, soort="robot", prefix=prefix, hash=_hash(waarde), rechten=rechten,
                  ip_whitelist=netten, verloopt_op=_nu() + timedelta(days=dagen))
    db.session.add(token)
    db.session.flush()
    log.schrijf(actor, "token.gemaakt", [f"token:{token.id}"],
                {"naam": naam, "soort": "robot", "rechten": rechten,
                 "whitelist": [str(n) for n in netten],
                 "verloopt_op": token.verloopt_op.isoformat(timespec="minutes")})
    db.session.commit()
    return waarde


def intrekken(naam, actor):
    """Trekt een token in; de volgende aanroep wordt geweigerd (ADR-012 v1.1.0)."""
    token = db.session.scalar(
        select(Token).where(Token.naam == naam, Token.ingetrokken_op.is_(None)).with_for_update()
    )
    if token is None:
        raise Regelfout("Er is geen actief token met deze naam.")
    token.ingetrokken_op = _nu()
    log.schrijf(actor, "token.ingetrokken", [f"token:{token.id}"], {"naam": naam})
    db.session.commit()


def _weiger(reden, token, endpoint, ip, status=401):
    actor = als_actor(token) if token else Actor("token", None, "onbekend")
    log.schrijf(actor, "api.geweigerd", [f"token:{token.id}"] if token else [],
                {"endpoint": endpoint, "reden": reden, "ip": ip}, soort="api")
    db.session.commit()
    raise Geweigerd(reden, status)


def controleer(authorization, ip, recht, endpoint):
    """Controle per aanroep in de volgorde van ADR-005. Geeft het token of gooit Geweigerd, met
    een logregel. 401 bij elke weigering behalve een ontbrekend recht (403): een token buiten de
    whitelist krijgt dus hetzelfde antwoord als een onbekend token."""
    if not current_app.config["API_INGESCHAKELD"]:
        _weiger("uit", None, endpoint, ip, 403)
    schema, _, waarde = (authorization or "").partition(" ")
    passend = TOKEN.fullmatch(waarde) if schema == "Bearer" else None
    token = passend and db.session.scalar(select(Token).where(Token.prefix == passend[1]))
    if not token or not hmac.compare_digest(token.hash, _hash(waarde)):
        _weiger("onbekend", None, endpoint, ip)
    if token.ingetrokken_op is not None:
        _weiger("ingetrokken", token, endpoint, ip)
    if _nu() >= token.verloopt_op:
        _weiger("verlopen", token, endpoint, ip)
    try:
        adres = ipaddress.ip_address(ip)
    except ValueError:
        adres = None
    if not adres or not any(adres in net for net in token.ip_whitelist):
        _weiger("buiten_whitelist", token, endpoint, ip)
    if recht and recht not in token.rechten:
        _weiger("zonder_recht", token, endpoint, ip, 403)
    return token


def gebruikt(token):
    """Een geslaagde aanroep komt niet in het log, alleen laatst_gebruikt_op (ADR-005 v1.2.0)."""
    token.laatst_gebruikt_op = _nu()
    db.session.commit()
