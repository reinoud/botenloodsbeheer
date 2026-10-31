"""De gebruikershandleiding noemt elke webroute van de dienst web (issue #30)."""

import re
from pathlib import Path

HANDLEIDING = Path("documentatie/gebruikers/handleiding.md")


def webroutes(app):
    """GET-routes van web, zonder static, health en API; `<id>` en `{nummer}` tellen als `{}`."""
    return {re.sub(r"<[^>]+>", "{}", r.rule) for r in app.url_map.iter_rules()
            if "GET" in r.methods and r.endpoint != "static"
            and not r.rule.startswith(("/health", "/api"))}


def ontbrekend(app, tekst):
    genoemd = {re.sub(r"\{[^}]*\}", "{}", t) for t in re.findall(r"`([^`]+)`", tekst)}
    return webroutes(app) - genoemd


def test_handleiding_noemt_elke_webroute(app):
    assert not ontbrekend(app, HANDLEIDING.read_text(encoding="utf-8"))


def test_mutant_route_uit_de_handleiding_faalt(app):
    tekst = HANDLEIDING.read_text(encoding="utf-8").replace("`/vrij`", "")
    assert ontbrekend(app, tekst) == {"/vrij"}
