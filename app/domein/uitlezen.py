"""De vier leesaanroepen van de API (ADR-012 v1.6.0, BLB-032, BLB-034). De domeinlaag kiest de
velden: lidnummer en naam van de eigenaar, bij de leden ook lid sinds en opzegdatum.
Een veld zonder waarde is None. Datums als JJJJ-MM-DD. Alleen lezen."""

from sqlalchemy import select

from app.domein import boten as boten_
from app.domein import indeling
from app.domein import leden as leden_
from app.domein import wachtlijst as wachtlijst_
from app.models import Lid, db


def _datum(d):
    return d.isoformat() if d else None


def _eigenaar(lid):
    if lid is None:  # clubboot of eigenaar onbekend: beide null (#212)
        return None
    return {"lidnummer": lid.lidnummer, "naam": lid.naam}


def _boot(b):
    return {"id": b.id, "naam": b.naam} if b else None


def plaatsen():
    """In de volgorde van het overzicht: rek, dan plaats."""
    return [{"code": p.code, "rek": r.naam, "clubplaats": p.is_clubplaats,
             "bootsoorten": [s.naam for s in p.bootsoorten], "boot": _boot(p.boot)}
            for r in indeling.rekken() for p in r.plaatsen]


def boten():
    return [{"id": b.id, "naam": b.naam, "bootsoort": b.bootsoort.naam,
             "plaats": b.plaats.code if b.plaats else None,
             "eigenaar": _eigenaar(b.lid), "clubboot": b.clubboot} for b in boten_.boten()]


def leden():
    uit = []
    for lid in db.session.scalars(select(Lid).order_by(Lid.lidnummer)):
        uit.append({"lidnummer": lid.lidnummer, "naam": lid.naam, "oud_lid": leden_.is_oud_lid(lid),
                    "lid_sinds": _datum(lid.lid_sinds), "opzegdatum": _datum(lid.opzegdatum)})
    return uit


def wachtlijst():
    """Per bootsoort, de langst wachtende eerst; zonder boten van oud-leden, net als het scherm."""
    return [{"bootsoort": soort.naam, "boot": _boot(w.boot),
             "eigenaar": _eigenaar(w.boot.lid),
             "aangemeld_op": _datum(w.aangemeld_op)}
            for soort, rijen in wachtlijst_.lijsten() for w in rijen]
