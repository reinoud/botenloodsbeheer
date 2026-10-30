# ADR-007 Achtergrondtaken

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Stories:** BLB-006, BLB-026, BLB-037

## Context

Twee taken draaien buiten het webproces (overlay §6): de dagelijkse ledensynchronisatie, die ook handmatig te starten is (intake), en de dagelijkse opschoning na 5 jaar. Beide duren bij 210 leden enkele seconden. Een beheerder start de synchronisatie handmatig vanuit de webinterface. De statuspagina toont de laatste uitvoering met resultaat (BLB-037).

## Besluit

De container `worker` draait hetzelfde image als `web` met het commando `flask taken draai`. Dat is een eenvoudige lus in Python:

1. Elke 15 seconden kijken of er werk is.
2. Werk is: de synchronisatie na het ingestelde tijdstip (`SYNC_TIJDSTIP`, standaard 03:00) als die vandaag nog niet slaagde; de opschoning na `OPSCHOON_TIJDSTIP` (standaard 04:00) als die vandaag nog niet draaide; een openstaand verzoek in `taakrun`.
3. Voor elke taak een PostgreSQL advisory lock nemen, zodat de taak nooit dubbel draait, ook niet bij een tweede worker per ongeluk.
4. Start, einde, resultaat, aantallen en een foutmelding zonder geheimen vastleggen in `taakrun`.
5. Na elke ronde de heartbeat bijwerken (een rij in `taakrun` met soort `heartbeat`), voor de healthcheck en de statuspagina.

Handmatig starten: de knop in de webinterface voegt een rij met status `aangevraagd` toe aan `taakrun` en schrijft een logregel. De worker pakt die binnen 15 seconden op. De pagina toont de status van het verzoek; de beheerder ververst de pagina. Er wordt niets in het webproces uitgevoerd.

De lus vangt elke fout per taak af, legt die vast en draait door. Bij `SIGTERM` maakt de worker de lopende taak af en stopt. Tijden gelden in de tijdzone uit `TZ` (standaard `Europe/Amsterdam`).

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Celery of RQ met Redis | Extra container en broker voor twee taken per dag |
| Cron in de container (supercronic) | Lost het tijdschema op, maar niet het handmatig starten; dan alsnog een poll op de database nodig |
| APScheduler in het webproces | Draait in elke Gunicorn-worker en in het webproces, in strijd met het kader |
| Cron op de host met `docker compose exec` | Installatie-afhankelijk, niet in de compose te beschrijven |
| PostgreSQL `LISTEN/NOTIFY` voor directe start | Scheelt hooguit 15 seconden wachten |

## Gevolgen

- Er is geen extra afhankelijkheid; de worker gebruikt dezelfde domeinlaag en hetzelfde log als de webinterface.
- Draait de worker niet, dan blijft een handmatig verzoek op `aangevraagd` staan. De statuspagina toont dan een verouderde heartbeat (ADR-010).
- Valt de worker op het geplande tijdstip uit, dan draait de taak bij de eerstvolgende start nog dezelfde dag; een gemiste dag wordt niet ingehaald, de volgende run vangt alles op.
- Een nieuwe taak is een functie en een regel in de lijst van taken in `taken/`.
