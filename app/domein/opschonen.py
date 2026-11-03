"""Bewaartermijn van 5 jaar (BLB-026, ADR-006): logregels, en oud-leden van wie geen boot een
plaats heeft, met hun boten en foto's. Draait dagelijks in de worker als botenloods_taken, de
enige rol die logregels mag verwijderen (ADR-007).

Kopieën: een lid staat in het log alleen als `lid:<id>`, zonder naam; foto's staan in de database
(ADR-008), niet op schijf; de wachtlijst volgt de boot via de cascade; de import maakt een
opgeschoond oud-lid niet opnieuw aan (leden.synchroniseer, ADR-004 stap 4). Back-ups vallen
buiten de applicatie (besluit stakeholder 2026-10-30).
"""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import delete, func, select

from app.domein import Actor, log, vandaag
from app.domein.leden import BEWAARJAREN, jaren_terug
from app.models import Afbeelding, Boot, Lid, Logregel, Taakrun, db

TAAK = "opschoning"
SLOT = 2  # sleutel van de advisory lock; 1 is de import
ACTOR = Actor("taak", None, TAAK)


def opschonen(dag):
    """Verwijdert in de lopende transactie en geeft de aantallen; de aanroeper commit.

    Begin van de termijn: de opzegdatum, of uit_bron_op als die ontbreekt (architectuur §9
    besluit 4). Alleen een boot met een plaats houdt het opschonen tegen (besluit 2026-10-30).
    """
    grens = jaren_terug(dag, BEWAARJAREN)
    logregels = db.session.execute(
        delete(Logregel).where(Logregel.tijdstip < jaren_terug(datetime.now(UTC), BEWAARJAREN))
    ).rowcount
    op_een_plaats = select(Boot.lid_id).join(Boot.plaats).where(Boot.lid_id.is_not(None))
    ids = db.session.scalars(select(Lid.id).where(
        func.coalesce(Lid.opzegdatum, Lid.uit_bron_op) < grens, Lid.id.not_in(op_een_plaats))
    ).all()
    # Een boot die intussen een andere eigenaar kreeg, valt hier buiten: DELETE leest de rij
    # opnieuw na het slot. Een oud-lid krijgt geen nieuwe boot of plaats (BLB-005, BLB-008).
    boten = db.session.scalars(
        delete(Boot).where(Boot.lid_id.in_(ids)).returning(Boot.afbeelding_id)
        .execution_options(synchronize_session=False)).all()
    fotos = [f for f in boten if f is not None]
    db.session.execute(delete(Afbeelding).where(Afbeelding.id.in_(fotos))
                       .execution_options(synchronize_session=False))
    db.session.execute(delete(Lid).where(Lid.id.in_(ids))
                       .execution_options(synchronize_session=False))
    return {"logregels": logregels, "leden": len(ids), "boten": len(boten), "fotos": len(fotos)}


def gedraaid_op(dag):
    begin = datetime.combine(dag, time(), ZoneInfo(current_app.config["TZ"]))
    return db.session.scalar(
        select(Taakrun.id).where(Taakrun.taak == TAAK, Taakrun.gestart_op >= begin).limit(1)
    ) is not None


def draai(dag=None):
    """Eén keer per dag, ook na een fout: dan volgt de volgende dag een nieuwe poging (ADR-007).
    Nooit twee tegelijk. Geeft de aantallen, of None als er niets te doen was."""
    dag = dag or vandaag()
    if not db.session.scalar(select(func.pg_try_advisory_xact_lock(SLOT))) or gedraaid_op(dag):
        db.session.rollback()
        return None
    gestart = datetime.now(UTC)
    try:
        aantallen = opschonen(dag)
        run = Taakrun(taak=TAAK, status="geslaagd", gestart_op=gestart,
                      beeindigd_op=datetime.now(UTC), aantallen=aantallen)
        db.session.add(run)
        db.session.flush()
        log.schrijf(ACTOR, "opschoning.uitgevoerd", [f"taakrun:{run.id}"], aantallen)
        db.session.commit()
    except Exception as fout:
        db.session.rollback()
        # Alleen de foutklasse: een exceptietekst kan gegevens bevatten (ADR-010).
        db.session.add(Taakrun(taak=TAAK, status="mislukt", gestart_op=gestart,
                               beeindigd_op=datetime.now(UTC),
                               foutmelding=f"{type(fout).__name__}: de opschoning is mislukt. "
                                           "Morgen volgt een nieuwe poging."))
        db.session.commit()
        raise
    return aantallen
