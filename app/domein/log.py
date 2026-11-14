"""Mutatielog (ADR-006). Schrijven gebeurt in de transactie van de mutatie."""

from sqlalchemy import or_, select

from app import INT_MAX
from app.models import Beheerder, Boot, Bootsoort, Lid, Logregel, Plaats, Rek, Token, db

# Velden waarvan de waarde nooit in het log komt; alleen "gewijzigd".
VERBODEN = frozenset(
    {"wachtwoord", "wachtwoordhash", "totp_geheim", "code", "tokenwaarde", "adres", "telefoon",
     "email"}
)

# Twee logs (BLB-043): elke handeling hoort bij precies één; tests/unit/test_log.py bewaakt dat.
BOOTMUTATIES = frozenset(
    {"boot.aangemaakt", "boot.gewijzigd", "boot.foto_toegevoegd", "boot.foto_vervangen", "boot.verwijderd",
     "boot.verplaatst", "plaats.toegewezen", "plaats.vrijgegeven", "wachtlijst.toegevoegd", "wachtlijst.verwijderd"}
)
TECHNISCH = frozenset(
    {"token.gemaakt", "token.rechten_gewijzigd", "token.ingetrokken", "api.geweigerd", "instelling.gewijzigd",
     "instelling.logo_toegevoegd", "instelling.logo_vervangen", "instelling.logo_verwijderd",
     "leden.import_aangevraagd", "rek.aangemaakt", "rek.gewijzigd", "rek.verwijderd",
     "plaats.aangemaakt", "plaats.gewijzigd", "plaats.verwijderd", "bootsoort.toegevoegd",
     "bootsoort.hernoemd", "bootsoort.verwijderd", "beheerder.uitgenodigd",
     "beheerder.methode_ingesteld", "beheerder.methode_toegevoegd", "beheerder.methode_ingetrokken",
     "beheerder.vergrendeld", "beheerder.ingelogd", "beheerder.uitgelogd", "beheerder.geblokkeerd",
     "beheerder.gedeblokkeerd", "beheerder.verwijderd", "beheerder.hersteld",
     "opschoning.uitgevoerd", "indeling.geimporteerd", "bezetting.geimporteerd",
     "naamkoppeling.verwijderd"}
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


# Leesbaar log (BV-82, #174): de opgeslagen actie en verwijzing blijven zoals ze zijn (ADR-006),
# alleen het tonen vertaalt.


def actietekst(actie):
    """'plaats.toegewezen' wordt 'plaats toegewezen'; een onbekende actie blijft zoals opgeslagen."""
    if actie not in BOOTMUTATIES | TECHNISCH:
        return actie
    return actie.replace(".", " ").replace("_", " ")


def _rek(naam):
    return naam if naam.lower() == "rek" or naam.lower().startswith("rek ") else f"Rek {naam}"


# soort -> (kolommen na id, tekst uit die kolommen)
_SOORTEN = {
    "plaats": ((Plaats.code,), lambda code: f"Plaats {code}"),
    "boot": ((Boot.naam,), lambda naam: f"Boot {naam}"),
    "lid": ((Lid.naam, Lid.lidnummer), lambda naam, nummer: f"Lid {naam} ({nummer})"),
    "rek": ((Rek.naam,), _rek),
    "bootsoort": ((Bootsoort.naam,), lambda naam: f"Bootsoort {naam}"),
    "beheerder": ((Beheerder.naam,), lambda naam: f"Beheerder {naam}"),
    "token": ((Token.naam,), lambda naam: f"Token {naam}"),
}


def namen(regels):
    """Verwijzing -> leesbare tekst voor alle regels, met één query per soort (geen N+1). Een
    verwijzing zonder object of van een andere soort ontbreekt; betreft() toont die zoals opgeslagen."""
    ids = {soort: set() for soort in _SOORTEN}
    for r in regels:
        for v in r.verwijzingen:
            soort, _, nr = v.partition(":")
            if soort in ids and nr.isdecimal() and int(nr) <= INT_MAX:
                ids[soort].add(int(nr))
    uit = {}
    for soort, nrs in ids.items():
        if not nrs:
            continue
        kolommen, tekst = _SOORTEN[soort]
        model = kolommen[0].class_
        for id_, *rest in db.session.execute(select(model.id, *kolommen).where(model.id.in_(nrs))):
            uit[f"{soort}:{id_}"] = tekst(*rest)
    return uit


def betreft(verwijzingen, namen):
    return ", ".join(namen.get(v, v) for v in verwijzingen)
