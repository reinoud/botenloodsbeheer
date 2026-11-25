# Terugblik Sentinel, review #418 deel 2 (vangnet)

Datum: 2026-11-25. Taak: review van de gestagede diff op `feature/418-vangnet`, met unit, E2E (twee keer), mutanten en de foutpaden van de trap.

## Wat ging goed

De brief noemde de commando's, de bekende uitzondering (#440) en wat buiten de review viel. De unit- en E2E-runs waren daardoor direct te draaien. Het script herstelde de stack in elk foutpad dat ik probeerde, ook na een SIGTERM terwijl `web` stil lag.

## Wat kon beter

De brief vroeg of de unittest de prioriteitseis bewijst, niet of het acceptatiecriterium "het vangnet beantwoordt geen enkel verzoek" klopt. Die twee verschillen: de prioriteit klopt, maar het vangnet vult een gat dat de app openlaat (`/api/` op het publieke entrypoint). Dat vond ik pas met een losse curl, niet via een test in de diff.

## Wat deed ik zelf goed

Ik heb elke claim gemeten in plaats van gelezen: twee unitmutanten, een E2E-mutant zonder vangnet, drie foutpaden van de trap en de projectnaam met `docker compose config`. Het gedrag van `down` in een gedeeld project heb ik in een wegwerpproject nagespeeld voordat ik er iets over schreef.

## Wat heb ik onderweg zelf verbeterd

Een container `aegis418-vangnet` draaide tegelijk. Ik heb eerst de labels en het netwerk bekeken (geen Traefik-labels, alleen `bridge`) voordat ik de E2E startte, zodat een tweede vangnetrouter de uitkomst niet kon vertekenen.

## Wat kan structureel beter

Zet in de opdracht: bij een nieuwe router met lage prioriteit toetst de reviewer naast de prioriteit ook welke verzoeken zonder router van de app nu bij de nieuwe router uitkomen, met een curl per entrypoint terwijl de app draait.
