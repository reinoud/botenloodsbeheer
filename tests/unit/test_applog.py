"""Applicatielog van web en api als JSON op stdout, met traceback bij een uitzondering (#137)."""

import json

import pytest

from tests.unit.conftest import API, WEB


def foutregel(capsys, monkeypatch, dienst, view):
    """De ERROR-regel na een uitzondering in een view, en de overige regels."""
    from app import create_app

    monkeypatch.setenv("DIENST", dienst)
    # Na capsys aanmaken: de handler bewaart sys.stdout bij create_app. De rol volgt uit de
    # dienst en is geen parameter: pytest toont parameters, en de URL bevat het wachtwoord.
    app = create_app({"SQLALCHEMY_DATABASE_URI": API if dienst == "api" else WEB})
    app.add_url_rule("/kapot", view_func=view)
    with app.app_context():
        assert app.test_client().get("/kapot").status_code == 500
    regels = [json.loads(r) for r in capsys.readouterr().out.splitlines()]
    fout = next(r for r in regels if r["niveau"] == "ERROR")
    return fout, [r for r in regels if r is not fout]


@pytest.mark.parametrize("dienst", ["web", "api"])
def test_uitzondering_in_een_view_staat_met_traceback_in_de_log(database, monkeypatch, capsys,
                                                                dienst):
    def kapot():
        raise RuntimeError("proef-137")

    fout, rest = foutregel(capsys, monkeypatch, dienst, kapot)
    assert "Traceback" in fout["traceback"] and "RuntimeError: proef-137" in fout["traceback"]
    assert all("traceback" not in r for r in rest)


def test_databasefout_zonder_persoonsgegevens_in_de_log(database, monkeypatch, capsys):
    """De rol api mag leden schrijven; zowel de parameters als de DETAIL van PostgreSQL
    (Failing row contains ...) bevatten het lid, ook na een regelovergang in een veld."""
    from app.models import Lid, db

    def kapot():
        db.session.add(Lid(lidnummer="9999", naam=None, adres="Dorpsstraat 1\nGeheimstad",
                           telefoon="0612345678", email="geheim@example.org"))
        db.session.commit()

    fout, _ = foutregel(capsys, monkeypatch, "api", kapot)
    assert "NotNullViolation" in fout["traceback"] and "DETAIL:  [weggelaten]" in fout["traceback"]
    for waarde in ("geheim@example.org", "Dorpsstraat", "Geheimstad", "0612345678"):
        assert waarde not in json.dumps(fout)
