"""Mutatielog (ADR-006). Schrijven gebeurt in de transactie van de mutatie."""

from sqlalchemy import or_, select

from app.models import Logregel, db

# Velden waarvan de waarde nooit in het log komt; alleen "gewijzigd".
VERBODEN = frozenset(
    {"wachtwoord", "wachtwoordhash", "totp_geheim", "code", "tokenwaarde", "adres", "telefoon",
     "email"}
)

# Twee logs (BLB-043): elke handeling hoort bij precies één; tests/unit/test_log.py bewaakt dat.
BOOTMUTATIES = frozenset(
    {"boot.aangemaakt", "boot.gewijzigd", "boot.foto_toegevoegd", "boot.foto_vervangen", "boot.verwijderd",
     "plaats.toegewezen", "plaats.vrijgegeven", "wachtlijst.toegevoegd", "wachtlijst.verwijderd"}
)
TECHNISCH = frozenset(
    {"token.gemaakt", "token.rechten_gewijzigd", "token.ingetrokken", "api.geweigerd", "instelling.gewijzigd",
     "leden.import_aangevraagd", "rek.aangemaakt", "rek.gewijzigd", "rek.verwijderd",
     "plaats.aangemaakt", "plaats.gewijzigd", "plaats.verwijderd", "bootsoort.toegevoegd",
     "bootsoort.hernoemd", "bootsoort.verwijderd", "beheerder.uitgenodigd",
     "beheerder.methode_ingesteld", "beheerder.methode_toegevoegd", "beheerder.methode_ingetrokken",
     "beheerder.vergrendeld", "beheerder.ingelogd", "beheerder.uitgelogd", "beheerder.geblokkeerd",
     "beheerder.gedeblokkeerd", "beheerder.verwijderd", "beheerder.hersteld",
     "opschoning.uitgevoerd"}
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


def regels(verwijzingen=None, acties=None, limiet=50, technisch=False, overslaan=0):
    """Nieuwste regels eerst, uit één logboek: standaard de bootmutaties, zodat geen overzicht
    technische regels toont. Het technische log toont alles wat geen bootmutatie is, ook oude
    soorten die de code niet meer schrijft. Filtert op regels met minstens één van de verwijzingen (zoals
    'plaats:12') en op acties die beginnen met een van de voorvoegsels (zoals 'boot.')."""
    soort = Logregel.actie.not_in(BOOTMUTATIES) if technisch else Logregel.actie.in_(BOOTMUTATIES)
    q = (select(Logregel).where(soort)
         .order_by(Logregel.tijdstip.desc(), Logregel.id.desc()).limit(limiet).offset(overslaan))
    if verwijzingen is not None:
        q = q.where(Logregel.verwijzingen.overlap(list(verwijzingen)))
    if acties:
        q = q.where(or_(*(Logregel.actie.startswith(a, autoescape=True) for a in acties)))
    return db.session.scalars(q).all()
