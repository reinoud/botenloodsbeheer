# Bijdragen aan botenloodsbeheer

Bijdragen zijn welkom, als issue en als pull request. Iedereen die meedoet, volgt de [gedragscode](CODE_OF_CONDUCT.md). Een beveiligingslek meld je niet in een issue, maar volgens [SECURITY.md](SECURITY.md).

## Een issue melden

Open een issue met een van de sjablonen: feature, bug of taak. Beschrijf wat je ziet of wilt, voor wie het is en hoe iemand het kan nalopen. Zet geen wachtwoorden, tokens, serverpaden of persoonsgegevens van leden in een issue.

## Een pull request maken

Begin met een issue, zodat vooraf duidelijk is of de wijziging past. Daarna:

1. Maak een branch van `main`: `feature/<issue>-<kort>` of `fix/<issue>-<kort>`.
2. Schrijf of pas tests aan bij elke codewijziging.
3. Draai de unit- en integratietests: `docker compose -f docker-compose.yml -f compose.dev.yml run --rm test`. Raakt de wijziging een scherm, draai dan ook de E2E-tests met `tests/e2e/draai.sh` (de stack moet draaien, zie de [README](README.md)).
4. Open een pull request naar `main`. De beschrijving noemt het issue (`Closes #<nr>`) en de testuitkomst.

Elke codewijziging krijgt een review voordat hij in `main` komt. Een wijziging aan inloggen, autorisatie, tokens of databaserechten krijgt daarnaast een securityreview. Een databasemigratie houdt één head en heeft een downgrade die werkt.

## Afspraken over code en tekst

- Teksten, schermen en documentatie zijn in het Nederlands.
- Besluiten over de architectuur staan in `docs/architecture/adr/`. Wijkt een wijziging daarvan af, pas dan ook de ADR aan.
- De projectregels staan in `docs/PROJECT-OVERLAY.md`.
- Gebruik alleen synthetische testgegevens, nooit gegevens van echte leden.

## Licentie

Door bij te dragen ga je ermee akkoord dat je bijdrage onder de [EUPL-1.2](LICENSE) valt, net als de rest van het project.
