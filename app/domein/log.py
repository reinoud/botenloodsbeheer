"""Mutatielog (ADR-006). Schrijven gebeurt in de transactie van de mutatie."""

from sqlalchemy import select

from app.models import Logregel, db

# Velden waarvan de waarde nooit in het log komt; alleen "gewijzigd".
VERBODEN = frozenset(
    {"wachtwoord", "wachtwoordhash", "totp_geheim", "code", "tokenwaarde", "adres", "telefoon",
     "email"}
)


def schrijf(actor, actie, verwijzingen, gegevens=None, soort="mutatie"):
    """Voegt een logregel toe aan de lopende sessie; de aanroeper commit."""
    gegevens = {k: "gewijzigd" if k in VERBODEN else v for k, v in (gegevens or {}).items()}
    db.session.add(
        Logregel(
            soort=soort,
            actor_soort=actor.soort,
            actor_id=actor.id,
            actor_naam=actor.naam,
            actie=actie,
            verwijzingen=list(verwijzingen),
            gegevens=gegevens,
        )
    )


def regels(verwijzing=None, limiet=50):
    """Nieuwste regels eerst, optioneel gefilterd op één verwijzing zoals 'beheerder:3'."""
    q = select(Logregel).order_by(Logregel.tijdstip.desc(), Logregel.id.desc()).limit(limiet)
    if verwijzing:
        q = q.where(Logregel.verwijzingen.contains([verwijzing]))
    return db.session.scalars(q).all()
