# Terugblik foundation, issue #22

**Datum:** 2026-10-31
**Taak:** ADR-012, ADR-004, ADR-007, architectuur §6 en backlog vraag 21 gelijkzetten met de bouw van slice 6.

## Wat ging goed

Issue #22 noemde elke afwijking met de plaats in de code. Daardoor kon ik elk punt in een paar regels code controleren (`app/domein/leden.py`, `integratie/koppeling/__init__.py`, `docker/nginx/api.inc`, `tests/e2e/draai.sh`).

## Wat kon beter

De beheerdocumentatie van forge beschreef het uur na een fout al als vaststaand, ook voor een verzoek van een beheerder. Dat botst met BLB-006 ("binnen een minuut") en met de gevolgen in ADR-012. Die keuze lag dus al vast in code en documentatie voordat iemand er een besluit over nam.

## Wat deed je zelf goed

Alle vervangingen in één python3-script met een controle dat elke oude tekst precies één keer voorkomt. Na afloop met grep gezocht naar de oude termen en de intake met `git diff` gecontroleerd.

## Wat heb je onderweg zelf verbeterd

ADR-007 noemde de oude taaknaam in de context en bij het handmatig starten. Dat stond niet in het issue, maar ik heb het meegenomen. Daarnaast heb ik een dubbele zin in ADR-012 ("Het contract ... Het contract ...") samengevoegd.

## Wat kan structureel beter

Zet in de opdracht: "Verandert een afwijking wat een beheerder ziet of hoe lang die moet wachten, leg die dan vóór de bouw aan apex en de stakeholder voor; een melding achteraf in een issue is te laat."
