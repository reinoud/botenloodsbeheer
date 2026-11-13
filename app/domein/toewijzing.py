"""Een boot een plaats geven (BLB-010, BLB-014), een plaats vrijgeven (BLB-011) en een boot verplaatsen (#206), ADR-003."""

from sqlalchemy import select

from app.domein import Regelfout, leden, log, wachtlijst
from app.models import Boot, Plaats, db


def controleer_past(p, bootnaam, bootsoort, clubboot):
    """Weigert een boot die niet bij de plaats past; gedeeld met boten.boot_wijzigen. Een boot met
    een lid of een onbekende eigenaar hoort op een gewone plaats (#204); een clubboot mag op beide (#205)."""
    if p.is_clubplaats and not clubboot:
        raise Regelfout(f"Plaats {p.code} is een clubplaats en alleen voor clubboten.")
    if bootsoort not in p.bootsoorten:
        raise Regelfout(f"Plaats {p.code} is niet geschikt voor een {bootsoort.naam.lower()}.")


def past(p, b):
    """Voor een keuzelijst: dezelfde regels als toewijzen, zonder te weigeren (#131)."""
    try:
        controleer_past(p, b.naam, b.bootsoort, b.clubboot)
    except Regelfout:
        return False
    return b.lid is None or not leden.is_oud_lid(b.lid)


def toewijzen(plaats_id, boot_id, actor):
    """Controleert en wijst toe in één transactie. De boot wordt eerst vergrendeld en dan de
    plaats, zodat twee beheerders niet tegelijk dezelfde plaats of boot toewijzen. Dezelfde
    volgorde als boten.boot_wijzigen, anders kunnen die twee elkaar laten vastlopen."""
    try:
        b = db.session.get(Boot, boot_id, with_for_update=True) if boot_id else None
        p = db.session.get(Plaats, plaats_id, with_for_update=True)
        if p is None or b is None:
            raise Regelfout("Kies een bestaande plaats en boot.")
        _toewijzen(p, b, actor)
    except Regelfout:
        db.session.rollback()
        raise
    db.session.commit()


def _toewijzen(p, b, actor):
    """Kern van toewijzen op een vergrendelde plaats en boot, zonder commit en rollback; de
    bezettingsimport (ADR-014 §3) doet er meer in één transactie."""
    if p.boot_id is not None:
        raise Regelfout(f"Plaats {p.code} is al bezet.")
    andere = db.session.scalar(select(Plaats).where(Plaats.boot_id == b.id))
    if andere is not None:
        raise Regelfout(f"Boot {b.naam} heeft al een plaats: {andere.code}.")
    controleer_past(p, b.naam, b.bootsoort, b.clubboot)
    if b.lid is not None and leden.is_oud_lid(b.lid):
        raise Regelfout(f"De eigenaar van boot {b.naam} is oud-lid. De boot krijgt geen plaats.")
    p.boot = b
    log.schrijf(actor, "plaats.toegewezen", [f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}",
                                             *([f"lid:{b.lid_id}"] if b.lid_id else [])],
                {"plaats": p.code, "boot": b.naam})
    wachtlijst.na_toewijzen(b, actor)


def vrijgeven(plaats_id, actor):
    """De boot blijft bestaan, zonder plaats. De plaats wordt eerst vergrendeld, zodat twee
    beheerders niet tegelijk dezelfde plaats vrijgeven en het log één regel krijgt. De
    applicatie wijst de vrije plaats niet zelf toe (BLB-011)."""
    p = db.session.get(Plaats, plaats_id, with_for_update=True)
    if p is None or p.boot is None:
        db.session.rollback()
        raise Regelfout("Deze plaats is al vrij." if p else "Deze plaats bestaat niet.")
    _vrijgeven(p, actor)
    db.session.commit()


def _vrijgeven(p, actor):
    """Kern van vrijgeven op een vergrendelde plaats met een boot, zonder commit."""
    b = p.boot
    p.boot = None
    log.schrijf(actor, "plaats.vrijgegeven", [f"plaats:{p.id}", f"rek:{p.rek_id}", f"boot:{b.id}",
                                              *([f"lid:{b.lid_id}"] if b.lid_id else [])],
                {"plaats": p.code, "boot": b.naam})


def verplaatsen(boot_id, plaats_id, actor):
    """Geeft de oude plaats vrij en wijst de nieuwe toe in één transactie, met dezelfde controles
    als toewijzen (#206). Eerst de boot, dan beide plaatsen op volgorde van id: twee verplaatsingen
    in tegengestelde richting vergrendelen zo in dezelfde volgorde. Een weigering laat de boot
    liggen, ook op de wachtlijst verandert niets. Eén logregel, onder beide plaatsen en de boot.
    Geeft de code van de nieuwe plaats."""
    try:
        b = db.session.get(Boot, boot_id, with_for_update=True)
        if b is None:
            raise Regelfout("Deze boot bestaat niet.")
        if plaats_id is None:
            raise Regelfout("Kies een vrije plaats.")
        oud = db.session.scalar(select(Plaats).where(Plaats.boot_id == b.id))
        if oud is None:
            raise Regelfout(f"Boot {b.naam} heeft geen plaats.")
        vergrendeld = {p.id: p for p in db.session.scalars(
            select(Plaats).where(Plaats.id.in_([oud.id, plaats_id])).order_by(Plaats.id)
            .with_for_update().execution_options(populate_existing=True))}
        oud, nieuw = vergrendeld[oud.id], vergrendeld.get(plaats_id)
        if oud.boot_id != b.id:  # intussen vrijgegeven door een andere beheerder
            raise Regelfout(f"Boot {b.naam} heeft geen plaats.")
        if nieuw is None:
            raise Regelfout("Kies een bestaande plaats.")
        blijft = f" De boot blijft op {oud.code}."
        if nieuw is oud:
            raise Regelfout(f"Boot {b.naam} ligt al op plaats {oud.code}.")
        if nieuw.boot_id is not None:
            raise Regelfout(f"Plaats {nieuw.code} is niet meer vrij." + blijft)
        try:
            controleer_past(nieuw, b.naam, b.bootsoort, b.clubboot)
        except Regelfout as fout:
            raise Regelfout(str(fout) + blijft) from None
        if b.lid is not None and leden.is_oud_lid(b.lid):
            raise Regelfout(f"De eigenaar van boot {b.naam} is oud-lid. De boot krijgt geen plaats." + blijft)
        oud.boot = None
        db.session.flush()  # boot_id is uniek: eerst vrij, dan toewijzen
        nieuw.boot = b
        log.schrijf(actor, "boot.verplaatst",
                    [f"plaats:{oud.id}", f"plaats:{nieuw.id}", *dict.fromkeys([f"rek:{oud.rek_id}", f"rek:{nieuw.rek_id}"]),
                     f"boot:{b.id}", *([f"lid:{b.lid_id}"] if b.lid_id else [])],
                    {"van": oud.code, "naar": nieuw.code, "boot": b.naam})
        code = nieuw.code
    except Regelfout:
        db.session.rollback()
        raise
    db.session.commit()
    return code
