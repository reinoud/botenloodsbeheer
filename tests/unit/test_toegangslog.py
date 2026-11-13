"""Toegangslog van Gunicorn in het formaat zonder_code (ADR-013, #5, #14)."""

import re
from datetime import timedelta
from types import SimpleNamespace

import pytest
from gunicorn.config import Config

from app.toegangslog import Toegangslog

REGEL = re.compile(r'^(\S+) \[\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d [+-]\d{4}\] "(\w+) (\S+)" (\d{3}) (\d+)$')


def log(capsys, raw_uri, xff=True, methode="GET"):
    cfg = Config()
    cfg.set("accesslog", "-")
    environ = {"RAW_URI": raw_uri, "REQUEST_METHOD": methode, "REMOTE_ADDR": "10.203.0.5"}
    if xff:
        environ["HTTP_X_FORWARDED_FOR"] = "10.203.0.5"
    Toegangslog(cfg).access(SimpleNamespace(status="200 OK", sent=42), None, environ,
                            timedelta(milliseconds=3))
    return capsys.readouterr().out.splitlines()


@pytest.mark.parametrize("raw_uri,pad", [
    ("/leden?zoek=Jansen", "/leden"),
    ("/zoeken?q=Jansen", "/zoeken"),
    ("/uitnodiging/GEHEIMECODE", "/uitnodiging/..."),
    ("/uitnodiging/GEHEIMECODE/wachtwoord?x=1", "/uitnodiging/..."),
    ("/boten/%0a12", "/boten/..."),
    ("/%2Fuitnodiging/GEHEIMECODE", "/..."),
    ("/uit%6Eodiging/GEHEIMECODE", "/uit..."),
    ("/health/live", "/health/live"),
])
def test_een_regel_zonder_querystring_en_code(capsys, raw_uri, pad):
    regels = log(capsys, raw_uri)
    assert len(regels) == 1
    assert REGEL.match(regels[0]).groups() == ("10.203.0.5", "GET", pad, "200", "42")
    assert "Jansen" not in regels[0] and "GEHEIM" not in regels[0]


def test_eigen_healthcheck_niet_in_de_log(capsys):
    """De healthcheck van Docker komt zonder proxy en dus zonder X-Forwarded-For."""
    assert log(capsys, "/health/live", xff=False) == []
    assert len(log(capsys, "/leden", xff=False)) == 1


def test_zonder_accesslog_geen_regels(capsys):
    environ = {"RAW_URI": "/leden", "REQUEST_METHOD": "GET"}
    Toegangslog(Config()).access(SimpleNamespace(status="200 OK", sent=1), None, environ,
                                 timedelta(0))
    assert capsys.readouterr().out == ""
