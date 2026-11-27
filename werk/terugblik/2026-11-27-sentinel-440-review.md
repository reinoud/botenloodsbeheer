# Terugblik sentinel, review #440 (vangnet-503 in de integratiecontainer)

Datum: 2026-11-27. Taak: review vóór commit van `fix/440-vangnet-503`, met de vraag of de wachttijd na een 503 langer dan een uur kan worden.

## Wat ging goed

De diff was klein en de opdracht noemde de regels van de wachtlogica, de grep op de app en het testcommando. De tests draaiden in één keer vanuit de worktree (71 geslaagd, 0 overgeslagen); een grep in de container bevestigde dat de bestanden uit de worktree kwamen.

## Wat kon beter

De opdracht noemde alleen `installatie.md` als document. Het contract van de container staat in `documentatie/beheer/integratiecontainer.md` (regel 11); dat bleef op de 404 van Traefik staan en heb ik zelf moeten vinden.

## Wat deed je zelf goed

De waarneming van 2026-11-25 nagelopen tegen de code in plaats van tegen de logtekst: na het uur vraagt de lus elke minuut alleen het importverzoek op (het token wordt gebruikt) en logt niets zolang er geen verzoek is en de geplande import van die dag al geslaagd is. "Import mislukt" logt hij ook als alleen die vraag mislukte. Daarbij de bewering in `installatie.md` over "een nieuw verzoek van een beheerder" getoetst tegen regel 155-156 en onjuist bevonden.

## Wat heb je onderweg verbeterd

Eerst nagegaan of `test_integratie.py` de database gebruikt (nee, geen autouse-fixture); daarom geen eigen `TEST_DB` nodig en niets op te ruimen. Ook de DST-rand van de wachttijd gevonden (aftrekken binnen dezelfde zone negeert `fold`).

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Wijzigt het gedrag van de integratiecontainer, laat de bouwer en de reviewer dan ook `documentatie/beheer/integratiecontainer.md` en de docstring van `integratie/koppeling/__init__.py` nalopen, niet alleen het document uit het issue."
