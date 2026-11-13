# Terugblik Bedrock, overname bouw #154 (zoeken vanuit de kop)

Datum: 2026-11-13. Taak: een gestopte bouw nalopen, afmaken en opleveren (zonder commit).

## Wat ging goed
- De teststand in de opdracht, met het pad van de uitvoer, maakte het nalopen snel: één bekende rode test, de rest was af.
- De volledige unitsuite liet precies de twee handleidingtests zien die nog ontbraken (routetabel). Geen verrassingen.
- Mutanten in een map met tijdstempel, met een assert dat elke kopie verschilt, en een runner die per mutant één regel schrijft.

## Wat kon beter
- De vorige bouwer liet een compose-stack (`botenloods-doc`) half draaien. Ik heb die met hetzelfde projectnaam en `down -v` moeten opruimen voordat ik iets kon doen.
- De mutant op `Plaats.vak` in de sortering is niet te vangen: de unieke index (rek_id, verdieping, vak) levert de rijen al in die volgorde. Dat wist ik vooraf niet en kostte een testherziening.
- De opdracht noemde geen woordbudget voor de handleidingalinea.

## Wat deed je zelf goed
- Alle E2E-botsingen met het nieuwe kopveld gezocht op deel van de tekst, niet alleen op het woord Eigenaar.
- De openbare pagina heeft een eigen mutant (blok `menu` weghalen) en een E2E-assert (`header input` telt 0 na uitloggen) die al bestond.
- Na elke E2E-mutant `web` teruggezet en gecontroleerd dat het origineel draait.

## Wat heb je onderweg zelf verbeterd
- Vier ruff-meldingen in `tests/unit/test_zoeken.py` (ongebruikte variabele, twee f-strings zonder veld, ongebruikte uitpakvariabele).
- De volgordetest op vak zet de rijen nu fysiek van vak 10 naar 1; hij bleef de mutant toch missen (zie boven), maar het uitgangspunt is nu eerlijker.
- De handleiding kreeg een eigen kopje en de routerij; de documentatietest slaagt weer.

## Structureel beter (letterlijk bruikbaar in een volgende opdracht)
- Zet in de opdracht: "Een mutant die een sorteersleutel weglaat waarvoor een unieke index al dezelfde volgorde geeft, noem je gelijkwaardig in plaats van hem te forceren."
- Zet in de opdracht: "Een script dat een eigen compose-project start, ruimt de bouwer zelf op met `down -v` en controleert met `docker ps -a`; noem het projectnaam in de brief."
- Zet in de opdracht: "Parse in een runner geen `naam:sleutel:pad` met een dubbele punt als de sleutel een dubbele punt kan bevatten; gebruik `|`." (Hier gaf dat een mislukte `grep`-controle bij één E2E-mutant.)
