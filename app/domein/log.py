"""Mutatielog (ADR-006). Schrijven gebeurt in de transactie van de mutatie."""

from sqlalchemy import or_, select

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


def regels(verwijzingen=None, acties=None, limiet=50):
    """Nieuwste regels eerst. Filtert op regels met minstens één van de verwijzingen (zoals
    'plaats:12') en op acties die beginnen met een van de voorvoegsels (zoals 'boot.')."""
    q = select(Logregel).order_by(Logregel.tijdstip.desc(), Logregel.id.desc()).limit(limiet)
    if verwijzingen is not None:
        q = q.where(Logregel.verwijzingen.overlap(list(verwijzingen)))
    if acties:
        q = q.where(or_(*(Logregel.actie.startswith(a, autoescape=True) for a in acties)))
    return db.session.scalars(q).all()
