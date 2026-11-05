# Terugblik Bedrock, 2026-11-05, issue #94 (rekoverzicht compact, geen gaten)

## Wat ging goed
- Het issue was volledig en de ontwerppunten (CSS-klassen voor de CSP, gatcontrole in `_vakken`) lieten geen open keuzes.
- De eerste volledige unitrun gaf direct de lijst van 24 tests die een gat gebruikten; zo was de omvang van het testwerk meteen bekend.
- Zes mutanten (gatcheck weg, gat op vak 1 niet gezien, alleen eerste verdieping gecontroleerd, kolommen vast 12, verdiepingen vast 5, CSS-klasse 7 weg) werden allemaal gevangen.

## Wat kon beter
- De E2E-test voor kolommen is niet met een eigen mutant gedraaid; alleen de unittests zijn gemuteerd.
- Een `sed -i ''` met `\?` (GNU-syntaxis) faalde stil in een `&&`-keten en liet bestanden onbewerkt; ik zag het pas bij de diff.

## Wat deed je zelf goed
- Alle tekstwijzigingen met python3 en `assert count == 1`, zodat een gemiste vervanging direct faalt.
- Oude tellingen (224/27) en de oude gat-uitleg gezocht in code, tests, ADR, backlog, architectuur en handleiding.

## Wat heb je onderweg verbeterd
- Eerste versie van de gatcontrole gaf een StopIteration bij een volle verdieping van 12 vakken; vervangen door een verzamelingsverschil met `min(..., default=None)`.
- Testverwachtingen voor lege vakken in het rekoverzicht waren fout (hoekvak heeft `aria-hidden`); gecorrigeerd na de eerste run.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: "Noem bij elke nieuwe E2E-assertie de mutant die hij moet vangen, of zeg dat de E2E-test niet gemuteerd wordt."
- Zet in de opdracht: "Een wijziging van een validatieregel in het domein raakt alle tests en E2E-helpers die met de oude regel data maken; laat het agent eerst de volledige unitsuite draaien voor de lijst met te herstellen tests."
- Zet in de afspraken: "Tekstwijzigingen op macOS met python3, niet met `sed -i ''` en GNU-patronen."
