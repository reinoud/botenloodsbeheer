"""API-tokens (ADR-005, ADR-012): robottokens en persoonlijke tokens maken, rechten wijzigen en
intrekken, de controle per aanroep en de logregel van elke weigering."""

import base64
import hashlib
import hmac
import ipaddress
import re
import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domein import Actor, Regelfout, log
from app.models import Beheerder, Token, db

# Vaste lijst in code (ADR-005, ADR-009).
RECHTEN = ("plaatsen:lezen", "boten:lezen", "leden:lezen", "wachtlijst:lezen",
           "persoonsgegevens", "leden:importeren", "bootaantallen:lezen")
CLI_RECHT = "leden:importeren"  # alleen met de CLI te geven (besluit stakeholder 2026-11-03, #52)
WEBRECHTEN = tuple(r for r in RECHTEN if r != CLI_RECHT)
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


def _rechten(rechten, soort):
    rechten = list(dict.fromkeys(rechten))
    if not rechten:
        raise Regelfout("Kies minstens één recht.")
    if onbekend := [r for r in rechten if r not in RECHTEN]:
        raise Regelfout(f"Onbekend recht: {', '.join(onbekend)}. Kies uit: {', '.join(RECHTEN)}.")
    if soort == "persoonlijk" and "leden:importeren" in rechten:
        # Een import hoort bij de integratiecontainer, niet bij een persoon (ADR-005).
        raise Regelfout("Het recht leden:importeren kan alleen bij een robottoken.")
    return rechten


def maken(soort, naam, rechten, whitelist, dagen, actor):
    """Maakt een token en geeft de waarde terug; die is daarna nergens meer te zien. Een
    persoonlijk token hoort bij de beheerder die het maakt; een lege whitelist betekent dan elk
    adres. Een robottoken heeft een whitelist nodig. Zonder dagen 365."""
    if soort not in ("persoonlijk", "robot"):
        raise Regelfout("Kies persoonlijk of robot.")
    if soort == "persoonlijk" and actor.soort != "beheerder":
        raise Regelfout("Een persoonlijk token maakt een beheerder in de webinterface.")
    if not NAAM.fullmatch(naam):
        raise Regelfout("Naam: 2 tot 50 tekens, alleen a-z, cijfers, punt, - en _.")
    rechten = _rechten(rechten, soort)
    if actor.soort != "systeem" and CLI_RECHT in rechten:
        raise Regelfout(f"Het recht {CLI_RECHT} geef je alleen met de CLI (flask token robot).")
    netten = whitelist_lezen(whitelist)
    if soort == "robot" and not netten:
        raise Regelfout("Een robottoken heeft een whitelist nodig.")
    dagen = STANDAARD_DAGEN if dagen is None else dagen
    if not 1 <= dagen <= MAX_DAGEN:
        raise Regelfout(f"Geldigheid: 1 tot en met {MAX_DAGEN} dagen (3 jaar).")
    if db.session.scalar(select(Token.id).where(Token.naam == naam)):
        raise Regelfout("Er is al een token met deze naam.")

    prefix = _b32(5)
    waarde = f"{VOORVOEGSEL}{prefix}{_b32(32)}"
    token = Token(naam=naam, soort=soort, prefix=prefix, hash=_hash(waarde), rechten=rechten,
                  ip_whitelist=netten, verloopt_op=_nu() + timedelta(days=dagen),
                  beheerder_id=actor.id if soort == "persoonlijk" else None,
                  gemaakt_door=actor.naam)
    db.session.add(token)
    db.session.flush()
    log.schrijf(actor, "token.gemaakt", [f"token:{token.id}"],
                {"naam": naam, "soort": soort, "rechten": rechten,
                 "whitelist": [str(n) for n in netten],
                 "verloopt_op": token.verloopt_op.isoformat(timespec="minutes"),
                 **({"eigenaar": actor.naam} if soort == "persoonlijk" else {})})
    db.session.commit()
    return waarde


def robot_maken(naam, rechten, whitelist, dagen, actor):
    """De CLI (ADR-012): zonder whitelist het netwerk van de integratiecontainer (KOPPELNET)."""
    return maken("robot", naam, rechten, whitelist or [current_app.config["KOPPELNET"]], dagen,
                 actor)


def alle():
    """Voor het overzicht (BLB-035): actieve tokens eerst, dan op naam. Geen waarde of hash."""
    return db.session.scalars(
        select(Token).options(selectinload(Token.beheerder))
        .order_by(Token.ingetrokken_op.is_not(None), Token.naam)).all()


def _actief(sleutel):
    """Vergrendelt een actief token op id (webinterface) of naam (CLI)."""
    gelijk = Token.id == sleutel if isinstance(sleutel, int) else Token.naam == sleutel
    return db.session.scalar(
        select(Token).where(gelijk, Token.ingetrokken_op.is_(None))
        .with_for_update().execution_options(populate_existing=True))


def rechten_wijzigen(token_id, rechten, actor):
    """Nieuwe rechten gelden vanaf de volgende aanroep (BLB-032 criterium 4)."""
    token = _actief(token_id)
    if token is None:
        db.session.rollback()
        raise Regelfout("Er is geen actief token met dit nummer.")
    oud = list(token.rechten)
    try:
        if actor.soort != "systeem":
            # Alleen de CLI geeft of neemt het CLI-recht; voor elke andere actor blijft het zo (#55).
            if CLI_RECHT in rechten and CLI_RECHT not in oud:
                raise Regelfout(f"Het recht {CLI_RECHT} geef je alleen met de CLI "
                                "(flask token robot).")
            rechten = [r for r in rechten if r != CLI_RECHT] + [r for r in oud if r == CLI_RECHT]
        nieuw = _rechten(rechten, token.soort)
    except Regelfout:
        db.session.rollback()  # het slot niet vasthouden tot het einde van het verzoek
        raise
    if set(nieuw) != set(oud):
        token.rechten = nieuw
        log.schrijf(actor, "token.rechten_gewijzigd", [f"token:{token.id}"],
                    {"naam": token.naam, "oud": oud, "nieuw": nieuw})
    db.session.commit()


def intrekken(sleutel, actor):
    """Trekt een token in, ook van een andere beheerder; de volgende aanroep wordt geweigerd
    (ADR-012 v1.1.0, BLB-035). sleutel: id uit de webinterface of naam uit de CLI."""
    token = _actief(sleutel)
    if token is None:
        db.session.rollback()
        raise Regelfout("Er is geen actief token met deze naam.")
    token.ingetrokken_op = _nu()
    log.schrijf(actor, "token.ingetrokken", [f"token:{token.id}"], {"naam": token.naam})
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
    if token.beheerder_id is not None and not db.session.scalar(
            select(Beheerder.actief).where(Beheerder.id == token.beheerder_id)):
        _weiger("eigenaar_inactief", token, endpoint, ip)
    try:
        adres = ipaddress.ip_address(ip)
    except ValueError:
        adres = None
    # Een lege whitelist (alleen bij een persoonlijk token) betekent elk adres (ADR-005).
    if token.ip_whitelist and (not adres or not any(adres in net for net in token.ip_whitelist)):
        _weiger("buiten_whitelist", token, endpoint, ip)
    if recht and recht not in token.rechten:
        _weiger("zonder_recht", token, endpoint, ip, 403)
    return token


def gebruikt(token):
    """Een geslaagde aanroep komt niet in het log, alleen laatst_gebruikt_op (ADR-005 v1.2.0)."""
    token.laatst_gebruikt_op = _nu()
    db.session.commit()
