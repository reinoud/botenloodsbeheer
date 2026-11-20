# Beveiligingsbeleid

## Een lek melden

Meld een beveiligingslek privé, niet in een openbaar issue. Gebruik op GitHub het tabblad Security en daar de knop "Report a vulnerability". Alleen de beheerder van de repository ziet die melding.

Beschrijf in de melding:

- welk onderdeel het raakt (webapplicatie, API, integratiecontainer of configuratie);
- hoe het lek te reproduceren is, met synthetische gegevens;
- wat een aanvaller ermee kan.

Test niet op een installatie van een vereniging, maar op een eigen lokale omgeving (zie de [README](README.md)).

## Wat je kunt verwachten

De beheerder bevestigt de melding binnen een week en houdt je op de hoogte in dezelfde melding. Een bevestigd lek wordt hersteld in een nieuwe release; daarna volgt een openbaar advies op GitHub. Wil je bij naam genoemd worden, zeg dat dan in de melding.

## Ondersteunde versies

Alleen de laatste release krijgt beveiligingsupdates. Werk bij volgens `documentatie/beheer/bijwerken.md`.
