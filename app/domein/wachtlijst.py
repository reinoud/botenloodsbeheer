"""Wachtlijst per bootsoort (BLB-013, BLB-014). De volgorde is informatie: de beheerder kiest zelf
welke boot een plaats krijgt; de applicatie wijst nooit zelf toe (backlog vraag 4)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, leden, log, vandaag
from app.models import Boot, Plaats, Wachtlijst, db


def _verwijzingen(boot):
    return [f"boot:{boot.id}", *([f"lid:{boot.lid_id}"] if boot.lid_id else [])]


def lijsten(zoek="", bootsoort_id=None):
    """Per bootsoort de boten op de lijst, de langst wachtende eerst. Een boot van een oud-lid
    telt niet mee; de eerstvolgende import haalt hem eraf (BLB-008). Met zoek alleen boten
    waarvan boot of lid de tekst bevat, met bootsoort_id alleen die soort."""
    q = select(Wachtlijst).join(Wachtlijst.boot).outerjoin(Boot.lid).where(leden.boot_of_lid_bevat(zoek))
    if bootsoort_id:
        q = q.where(Boot.bootsoort_id == bootsoort_id)
    rijen = db.session.scalars(
        q.order_by(Wachtlijst.aangemeld_op, Boot.naam, Boot.id)
        .options(selectinload(Wachtlijst.boot).selectinload(Boot.lid),
                 selectinload(Wachtlijst.boot).selectinload(Boot.bootsoort))
    ).all()
    per_soort = {}
    for w in rijen:
        if w.boot.lid is None or not leden.is_oud_lid(w.boot.lid):
            per_soort.setdefault(w.boot.bootsoort, []).append(w)
    return sorted(per_soort.items(), key=lambda item: item[0].naam)


def wachttijd(aangemeld_op, dag=None):
    """Hele jaren en maanden, of dagen onder een maand: zo leest de beheerder het direct."""
    dag = dag or vandaag()
    maanden = (dag.year - aangemeld_op.year) * 12 + dag.month - aangemeld_op.month
    maanden -= dag.day < aangemeld_op.day
    if maanden < 1:
        dagen = (dag - aangemeld_op).days
        return "1 dag" if dagen == 1 else f"{dagen} dagen"
    jaren, rest = divmod(maanden, 12)
    delen = ([f"{jaren} jaar"] if jaren else []) + (
        [f"{rest} {'maand' if rest == 1 else 'maanden'}"] if rest else [])
    return " en ".join(delen)


def _datum(waarde):
    """Leeg is vandaag; een eerdere datum mag, de toekomst niet (besluit stakeholder 2026-11-01)."""
    if waarde in (None, ""):
        return vandaag()
    try:
        dag = waarde if isinstance(waarde, date) else date.fromisoformat(waarde)
    except ValueError:
        raise Regelfout("Vul een geldige aanmelddatum in, of laat het veld leeg voor vandaag.") from None
    if dag > vandaag():
        raise Regelfout("De aanmelddatum mag niet in de toekomst liggen.")
    return dag


def erop_zetten(boot_id, aangemeld_op, actor):
    """Zet een boot van een lid zonder plaats op de lijst van zijn bootsoort. Eerst de boot
    vergrendelen, net als toewijzen: zo krijgt een boot niet tegelijk een plaats en een plek op
    de lijst, en zetten twee beheerders hem niet allebei erop."""
    try:
        dag = _datum(aangemeld_op)
        b = db.session.get(Boot, boot_id, with_for_update=True, populate_existing=True)
        if b is None:
            raise Regelfout("Deze boot bestaat niet.")
        if b.clubboot:
            raise Regelfout(f"Boot {b.naam} is een clubboot. Een clubboot kan niet op de wachtlijst.")
        if b.lid is not None and leden.is_oud_lid(b.lid):
            raise Regelfout(f"De eigenaar van boot {b.naam} is oud-lid. De boot kan niet op de "
                            "wachtlijst.")
        if db.session.scalar(select(Plaats.code).where(Plaats.boot_id == b.id)):
            raise Regelfout(f"Boot {b.naam} heeft al een plaats.")
        if db.session.get(Wachtlijst, b.id, populate_existing=True):
            raise Regelfout(f"Boot {b.naam} staat al op de wachtlijst.")
    except Regelfout:
        db.session.rollback()
        raise
    # shortcut: een import die het lid tegelijk oud-lid maakt, ziet deze regel niet; lijsten()
    # verbergt de boot en de volgende import haalt hem eraf. Een slot op het lid als dat vaker speelt.
    db.session.add(Wachtlijst(boot=b, aangemeld_op=dag))
    log.schrijf(actor, "wachtlijst.toegevoegd", _verwijzingen(b),
                {"boot": b.naam, "bootsoort": b.bootsoort.naam, "aangemeld_op": dag.isoformat()})
    db.session.commit()


def _eraf(w, actor, reden=None):
    """Haalt de boot van de lijst in de lopende transactie; de aanroeper commit."""
    b = w.boot
    db.session.delete(w)
    log.schrijf(actor, "wachtlijst.verwijderd", _verwijzingen(b),
                {"boot": b.naam, "aangemeld_op": w.aangemeld_op.isoformat()}
                | ({"reden": reden} if reden else {}))


def eraf_halen(boot_id, actor):
    db.session.get(Boot, boot_id, with_for_update=True)
    w = db.session.get(Wachtlijst, boot_id, populate_existing=True)
    if w is None:
        db.session.rollback()
        raise Regelfout("Deze boot staat niet op de wachtlijst.")
    _eraf(w, actor)
    db.session.commit()


def na_toewijzen(boot, actor):
    """BLB-014: een boot die een plaats krijgt, gaat van de lijst; in de transactie van toewijzen."""
    if boot.wachtlijst is not None:
        _eraf(boot.wachtlijst, actor, "plaats toegewezen")


def oud_leden_eraf(actor, dag):
    """BLB-008: na een import gaan de boten van oud-leden van de lijst, met het robottoken als
    actor (#27). Ook een lid dat eerder oud-lid werd, want de opzegdatum kan pas nu verstreken zijn."""
    rijen = db.session.scalars(select(Wachtlijst).options(
        selectinload(Wachtlijst.boot).selectinload(Boot.lid))).all()
    for w in rijen:
        if w.boot.lid is not None and leden.is_oud_lid(w.boot.lid, dag):
            _eraf(w, actor, "oud-lid")
