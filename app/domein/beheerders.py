"""Beheerders: uitnodigen, inlogmethode instellen en inloggen (ADR-001)."""

import hashlib
import hmac
import re
import secrets
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy import select
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.domein import Actor, Regelfout, log
from app.models import Beheerder, Passkey, Uitnodiging, db

UITNODIGING_GELDIG = timedelta(hours=24)
MAX_POGINGEN = 5
VERGRENDELTIJD = timedelta(minutes=15)
GEBRUIKERSNAAM = re.compile(r"[a-z0-9._-]{2,50}")

_hasher = PasswordHasher()
# Bij een onbekende gebruikersnaam rekenen we deze hash door, zodat de duur niets verraadt.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def _nu():
    return datetime.now(UTC)


def _hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()


def _fernet():
    return Fernet(current_app.config["TOTP_SLEUTEL"])


def _rp():
    """(rp_id, origin) voor WebAuthn."""
    basis = urlsplit(current_app.config["BASIS_URL"])
    return current_app.config["WEBAUTHN_RP_ID"], f"{basis.scheme}://{basis.netloc}"


# Uitnodigen


def uitnodigen(gebruikersnaam, actor):
    """Maakt een beheerder zonder inlogmethode en geeft de eenmalige code terug."""
    if not GEBRUIKERSNAAM.fullmatch(gebruikersnaam):
        raise Regelfout("Gebruikersnaam: 2 tot 50 tekens, alleen a-z, cijfers, punt, - en _.")
    if db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == gebruikersnaam)):
        raise Regelfout("Deze gebruikersnaam bestaat al.")
    beheerder = Beheerder(naam=gebruikersnaam, gebruikersnaam=gebruikersnaam)
    code = secrets.token_urlsafe(32)
    verloopt_op = _nu() + UITNODIGING_GELDIG
    db.session.add(beheerder)
    db.session.flush()
    db.session.add(
        Uitnodiging(beheerder_id=beheerder.id, code_hash=_hash_code(code), verloopt_op=verloopt_op)
    )
    log.schrijf(actor, "beheerder.uitgenodigd", [f"beheerder:{beheerder.id}"],
                {"gebruikersnaam": gebruikersnaam,
                 "geldig_tot": verloopt_op.isoformat(timespec="minutes")})
    db.session.commit()
    return code


def uitnodiging(code, vergrendelen=False):
    """Geeft een geldige, ongebruikte uitnodiging, of een Regelfout."""
    q = select(Uitnodiging).where(Uitnodiging.code_hash == _hash_code(code))
    if vergrendelen:
        q = q.with_for_update()
    u = db.session.scalar(q)
    if not u or u.gebruikt_op or u.verloopt_op <= _nu() or not u.beheerder.actief:
        raise Regelfout("Deze link is ongeldig, verlopen of al gebruikt.")
    return u


# Wachtwoord en TOTP


def controleer_wachtwoord(beheerder, wachtwoord):
    if not 12 <= len(wachtwoord) <= 128:
        raise Regelfout("Het wachtwoord moet 12 tot 128 tekens lang zijn.")
    if wachtwoord.casefold() in {beheerder.gebruikersnaam.casefold(), beheerder.naam.casefold()}:
        raise Regelfout("Het wachtwoord mag niet gelijk zijn aan de gebruikersnaam of naam.")


def nieuw_totp_geheim():
    return pyotp.random_base32()


def totp_uri(geheim, gebruikersnaam):
    return pyotp.TOTP(geheim).provisioning_uri(name=gebruikersnaam, issuer_name="Botenloods")


def totp_stap(geheim, code, laatste_stap):
    """Tijdstap waarbij de code hoort (een stap marge), of None. Een stap wordt maar één keer
    geaccepteerd: alleen stappen na de laatst gebruikte tellen."""
    totp = pyotp.TOTP(geheim)
    nu = int(time.time()) // totp.interval
    for stap in (nu - 1, nu, nu + 1):
        if laatste_stap is not None and stap <= laatste_stap:
            continue
        if hmac.compare_digest(totp.at(stap * totp.interval), code.strip()):
            return stap
    return None


def wachtwoord_instellen(code, wachtwoord, totp_geheim, totp_code):
    """Activeert wachtwoord en TOTP via een uitnodiging, pas na één juiste TOTP-code."""
    u = uitnodiging(code, vergrendelen=True)
    beheerder = u.beheerder
    controleer_wachtwoord(beheerder, wachtwoord)
    stap = totp_stap(totp_geheim, totp_code, None)
    if stap is None:
        raise Regelfout("De code uit de authenticator-app klopt niet. Probeer het opnieuw.")
    u.gebruikt_op = _nu()
    beheerder.wachtwoordhash = _hasher.hash(wachtwoord)
    beheerder.totp_geheim = _fernet().encrypt(totp_geheim.encode())
    beheerder.laatste_totp_stap = stap
    log.schrijf(Actor.van(beheerder), "beheerder.methode_ingesteld",
                [f"beheerder:{beheerder.id}"], {"methode": "wachtwoord en TOTP"})
    db.session.commit()
    return beheerder


def _vergrendeld(beheerder):
    return beheerder.geblokkeerd_tot is not None and beheerder.geblokkeerd_tot > _nu()


def _mislukt(beheerder):
    beheerder.mislukte_pogingen += 1
    if beheerder.mislukte_pogingen >= MAX_POGINGEN:
        beheerder.mislukte_pogingen = 0
        beheerder.geblokkeerd_tot = _nu() + VERGRENDELTIJD
        log.schrijf(Actor.van(beheerder), "beheerder.vergrendeld", [f"beheerder:{beheerder.id}"],
                    {"minuten": int(VERGRENDELTIJD.total_seconds() // 60)})
    db.session.commit()


def wachtwoord_controleren(gebruikersnaam, wachtwoord):
    """Stap 1 van inloggen met wachtwoord. Geeft de beheerder als het wachtwoord klopt;
    de teller gaat pas terug naar nul na een juiste TOTP-code."""
    beheerder = db.session.scalar(
        select(Beheerder).where(Beheerder.gebruikersnaam == gebruikersnaam).with_for_update()
    )
    hash_ = beheerder.wachtwoordhash if beheerder and beheerder.wachtwoordhash else _DUMMY_HASH
    try:
        juist = _hasher.verify(hash_, wachtwoord)
    except (VerificationError, InvalidHashError):
        juist = False
    if not beheerder or not beheerder.wachtwoordhash or not beheerder.actief:
        db.session.rollback()
        return None
    if _vergrendeld(beheerder):
        db.session.rollback()
        return None
    if not juist:
        _mislukt(beheerder)
        return None
    if _hasher.check_needs_rehash(beheerder.wachtwoordhash):
        beheerder.wachtwoordhash = _hasher.hash(wachtwoord)
    db.session.commit()
    return beheerder


def totp_controleren(beheerder_id, code):
    """Stap 2 van inloggen met wachtwoord."""
    beheerder = db.session.get(Beheerder, beheerder_id, with_for_update=True)
    if not beheerder or not beheerder.actief or not beheerder.totp_geheim:
        db.session.rollback()
        return None
    if _vergrendeld(beheerder):
        db.session.rollback()
        return None
    geheim = _fernet().decrypt(beheerder.totp_geheim).decode()
    stap = totp_stap(geheim, code, beheerder.laatste_totp_stap)
    if stap is None:
        _mislukt(beheerder)
        return None
    beheerder.laatste_totp_stap = stap
    beheerder.mislukte_pogingen = 0
    log.schrijf(Actor.van(beheerder), "beheerder.ingelogd", [f"beheerder:{beheerder.id}"],
                {"methode": "wachtwoord en TOTP"})
    db.session.commit()
    return beheerder


# Passkeys


def passkey_registratieopties(code):
    """(options-JSON, challenge) voor het registreren van een passkey via een uitnodiging."""
    beheerder = uitnodiging(code).beheerder
    rp_id, _ = _rp()
    opties = generate_registration_options(
        rp_id=rp_id,
        rp_name="Botenloods",
        user_name=beheerder.gebruikersnaam,
        user_id=str(beheerder.id).encode(),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=p.credential_id) for p in beheerder.passkeys
        ],
    )
    return options_to_json(opties), opties.challenge


def passkey_registreren(code, credential, challenge, naam="Passkey"):
    u = uitnodiging(code, vergrendelen=True)
    beheerder = u.beheerder
    rp_id, origin = _rp()
    try:
        r = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
    except WebAuthnException:
        db.session.rollback()
        raise Regelfout("De passkey kon niet worden geregistreerd. Probeer het opnieuw.") from None
    u.gebruikt_op = _nu()
    db.session.add(
        Passkey(
            beheerder_id=beheerder.id,
            credential_id=r.credential_id,
            publieke_sleutel=r.credential_public_key,
            teller=r.sign_count,
            naam=naam[:100],
        )
    )
    log.schrijf(Actor.van(beheerder), "beheerder.methode_ingesteld",
                [f"beheerder:{beheerder.id}"], {"methode": "passkey", "naam": naam[:100]})
    db.session.commit()
    return beheerder


def passkey_inlogopties():
    rp_id, _ = _rp()
    opties = generate_authentication_options(
        rp_id=rp_id, user_verification=UserVerificationRequirement.REQUIRED
    )
    return options_to_json(opties), opties.challenge


def passkey_inloggen(credential, challenge):
    """Geeft de beheerder bij een geldige assertion, anders None. De wachtwoordteller
    speelt hier geen rol, zodat een vergrendeling een passkeygebruiker niet buitensluit."""
    try:
        credential_id = base64url_to_bytes(credential["rawId"])
    except (KeyError, TypeError, ValueError):
        return None
    passkey = db.session.scalar(
        select(Passkey).where(Passkey.credential_id == credential_id).with_for_update()
    )
    if not passkey or not passkey.beheerder.actief:
        db.session.rollback()
        return None
    rp_id, origin = _rp()
    try:
        r = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=passkey.publieke_sleutel,
            credential_current_sign_count=passkey.teller,
            require_user_verification=True,
        )
    except WebAuthnException:
        db.session.rollback()
        return None
    passkey.teller = r.new_sign_count
    passkey.laatst_gebruikt_op = _nu()
    beheerder = passkey.beheerder
    log.schrijf(Actor.van(beheerder), "beheerder.ingelogd", [f"beheerder:{beheerder.id}"],
                {"methode": "passkey"})
    db.session.commit()
    return beheerder


# Sessie


def uitloggen(beheerder):
    """Hoogt de sessieversie op, zodat ook een gekopieerde sessiecookie ongeldig wordt."""
    beheerder.sessieversie += 1
    log.schrijf(Actor.van(beheerder), "beheerder.uitgelogd", [f"beheerder:{beheerder.id}"])
    db.session.commit()
