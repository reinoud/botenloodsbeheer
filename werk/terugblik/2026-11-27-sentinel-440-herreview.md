# Terugblik Sentinel, herreview #440 (vangnet 503)

Datum: 2026-11-27. Taak: herreview van vier herstelpunten in documentatie en commentaar vóór de commit.

## Wat ging goed

De opdracht noemde de vier punten met bestand en regel, en zei welke delen al akkoord waren. Zo bleef de review klein: diff lezen, `ronde` en `_fout` naast de tekst leggen, ankers en `Retry-After` in `app/` nagaan.

## Wat kon beter

De opdracht noemde de regellengte niet. De herwerkte commentaarregels zijn langer dan `line-length = 100` uit `pyproject.toml` (regels 8, 104, 105 en 177), terwijl het bestand op `main` geen enkele regel boven 100 had. Ruff staat niet in CI en E501 staat niet aan, dus ik heb het als opmerking gemeld en niet als blokkade.

## Wat deed ik zelf goed

Ik heb de bewering "alleen een nieuw token heft dat op" getoetst aan de code (`wachten and self.fout_van_api` geeft direct `return`) en nagegaan dat de app nergens anders een 503 of een `Retry-After` zet. De 429 met `Retry-After` staat ook in `openapi.yaml` als antwoord van Traefik.

## Wat heb ik onderweg verbeterd

Ik heb met `git diff --cached -w --word-diff` gecontroleerd dat in `integratie/` alleen commentaar en docstring afwijken; de code op regel 103 tot 106 is gelijk aan de eerder gereviewde versie.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Houd commentaar en docstrings binnen `line-length` uit `pyproject.toml` (100) en controleer dat met `awk 'length>100' <bestand>` vóór de review."
