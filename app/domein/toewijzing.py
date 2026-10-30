"""Een boot een plaats geven (BLB-010) en een plaats vrijgeven (BLB-011), ADR-003."""

from sqlalchemy import select

from app.domein import Regelfout, leden, log
from app.models import Boot, Plaats, db


def toewijzen(plaats_id, boot_id, actor):
    """Controleert en wijst toe in één transactie. De plaats wordt eerst vergrendeld en dan de
    boot, zodat twee beheerders niet tegelijk dezelfde plaats of boot toewijzen."""
    try:
        p = db.session.get(Plaats, plaats_id, with_for_update=True)
        b = db.session.get(Boot, boot_id, with_for_update=True) if boot_id else None
        if p is None or b is None:
            raise Regelfout("Kies een bestaande plaats en boot.")
        if p.boot_id is not None:
            raise Regelfout(f"Plaats {p.code} is al bezet.")
        andere = db.session.scalar(select(Plaats).where(Plaats.boot_id == b.id))
        if andere is not None:
            raise Regelfout(f"Boot {b.naam} heeft al een plaats: {andere.code}.")
        if p.is_clubplaats and b.lid_id is not None:
            raise Regelfout(f"Plaats {p.code} is een clubplaats en alleen voor clubboten.")
        if not p.is_clubplaats and b.lid_id is None:
            raise Regelfout(f"Boot {b.naam} is een clubboot en hoort op een clubplaats.")
        if b.bootsoort not in p.bootsoorten:
            raise Regelfout(f"Plaats {p.code} is niet geschikt voor een {b.bootsoort.naam.lower()}.")
        if b.lid is not None and leden.is_oud_lid(b.lid):
            raise Regelfout(f"De eigenaar van boot {b.naam} is oud-lid. De boot krijgt geen plaats.")
    except Regelfout:
        db.session.rollback()
        raise
    p.boot = b
    log.schrijf(actor, "plaats.toegewezen", [f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}",
                                             *([f"lid:{b.lid_id}"] if b.lid_id else [])],
                {"plaats": p.code, "boot": b.naam})
    db.session.commit()


def vrijgeven(plaats_id, actor):
    """De boot blijft bestaan, zonder plaats. De plaats wordt eerst vergrendeld, zodat twee
    beheerders niet tegelijk dezelfde plaats vrijgeven en het log één regel krijgt. De
    applicatie wijst de vrije plaats niet zelf toe (BLB-011)."""
    p = db.session.get(Plaats, plaats_id, with_for_update=True)
    if p is None or p.boot is None:
        db.session.rollback()
        raise Regelfout("Deze plaats is al vrij." if p else "Deze plaats bestaat niet.")
    b = p.boot
    p.boot = None
    log.schrijf(actor, "plaats.vrijgegeven", [f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}",
                                              *([f"lid:{b.lid_id}"] if b.lid_id else [])],
                {"plaats": p.code, "boot": b.naam})
    db.session.commit()
