# Terugblik sentinel, review #372

Datum: 2026-11-23. Taak: review vóór de commit van #372 (een 404 van Traefik telt niet als fout van de API).

## Wat ging goed

De mutanten van de bouwer hadden elk een eigen map met de hele `integratie/`, zodat ze als één bind mount over `/app/integratie` draaiden. Alle vier vielen op een benoemde assert. De volledige unitsuite draaide in 6,5 minuut met een eigen `TEST_DB` naast de mutantruns op een tweede `TEST_DB`, zonder botsing: 1792 geslaagd, 0 gefaald, 0 overgeslagen.

## Wat kon beter

De brief zegt dat het besluit van de stakeholder in het laatste commentaar van het issue staat. Het issue heeft geen commentaar. Het besluit kwam alleen uit de brief zelf ("elke minuut opnieuw, tot vijf keer"). Daarnaast miste `mutanten.sh` van de bouwer `-p botenloods`, terwijl de worktreeregel in de overlay dat vraagt.

## Wat deed ik zelf goed

De brief vroeg of een andere 404 de telling terugzet. Ik heb daar een eigen mutant voor gemaakt (`else self.traefik_404`); die overleeft. Ook een mutant op de andere kant van de grens (`<= TRAEFIK_HERHALINGEN + 1`) heb ik gedraaid; die valt. Ik heb na een wijziging in de ADR-tekst het hele project op de oude formulering doorzocht en zo de verouderde opmerking in `docker-compose.yml:224` gevonden.

## Wat heb ik onderweg zelf verbeterd

Ik gebruikte voor de mutantruns een tweede testdatabase (`botenloods_test_s372m`), zodat ze tegelijk met de volledige suite konden draaien.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Wijzigt de bouw een teller of grens die op meer manieren terugspringt (geslaagde aanroep, andere fout), lever dan per manier van terugzetten een mutant, met de test die erop valt." En: "Verwijs in de brief alleen naar een besluit in het issue als het commentaar er staat; staat het er niet, zet dan de tekst van het besluit in de brief en zet het besluit vóór de review in het issue."
