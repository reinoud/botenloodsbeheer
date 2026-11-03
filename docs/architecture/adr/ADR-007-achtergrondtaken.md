# ADR-007 Achtergrondtaken

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.4.0
**Stories:** BLB-006, BLB-026, BLB-037

## Context

De dagelijkse opschoning na 5 jaar draait buiten het webproces (overlay §6) en duurt bij 210 leden enkele seconden. De ledenimport draait sinds 2026-10-31 in de integratiecontainer (ADR-012); een beheerder kan hem nog steeds handmatig aanvragen vanuit de webinterface. De statuspagina toont de laatste uitvoering met resultaat (BLB-037).

## Besluit

De container `worker` draait hetzelfde image als `web` met het commando `flask taken draai`. Dat is een eenvoudige lus in Python:

1. Elke 15 seconden kijken of er werk is.
2. Werk is: de opschoning na `OPSCHOON_TIJDSTIP` (standaard 04:00) als die vandaag nog niet draaide. Na een fout volgt de volgende dag een nieuwe poging: elke run van vandaag telt, ook een mislukte. `OPSCHOON_TIJDSTIP` staat alleen in de omgeving van `worker`.
3. Voor elke taak een PostgreSQL advisory lock nemen (sleutel 1 de import, 2 de opschoning), zodat de taak nooit dubbel draait, ook niet bij een tweede worker per ongeluk.
4. Start, einde, resultaat, aantallen en een foutmelding zonder geheimen vastleggen in `taakrun`.
5. Na elke ronde de heartbeat bijwerken (een rij in `taakrun` met soort `heartbeat`), voor de healthcheck en de statuspagina.

Handmatig importeren: de knop in de webinterface voegt een rij met taak `ledenimport` en status `aangevraagd` toe aan `taakrun` en schrijft een logregel `leden.import_aangevraagd`. De integratiecontainer ziet het verzoek binnen 60 seconden via `GET /api/v1/leden/importverzoek` (ADR-012). De pagina toont de status van het verzoek; de beheerder ververst de pagina. Er wordt niets in het webproces of de worker uitgevoerd.

De lus vangt elke fout per taak af, legt die vast en draait door. Bij `SIGTERM` maakt de worker de lopende taak af en stopt. Tijden gelden in de tijdzone uit `TZ` (standaard `Europe/Amsterdam`).

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Celery of RQ met Redis | Extra container en broker voor één taak per dag |
| Cron in de container (supercronic) | Lost het tijdschema op, maar niet het handmatig starten; dan alsnog een poll op de database nodig |
| APScheduler in het webproces | Draait in elke Gunicorn-worker en in het webproces, in strijd met het kader |
| Cron op de host met `docker compose exec` | Installatie-afhankelijk, niet in de compose te beschrijven |
| PostgreSQL `LISTEN/NOTIFY` voor directe start | Scheelt hooguit 15 seconden wachten |

## Gevolgen

- Er is geen extra afhankelijkheid; de worker gebruikt dezelfde domeinlaag en hetzelfde log als de webinterface.
- Draait de integratiecontainer niet, dan blijft een handmatig verzoek op `aangevraagd` staan. Draait de worker niet, dan toont de statuspagina een verouderde heartbeat (ADR-010).
- De worker heeft geen ledenbron, geen `SYNC_TIJDSTIP` en geen recht meer om leden aan te maken of bij te werken; hij houdt het recht om op te schonen (ADR-006).
- De databaserol `botenloods_taken` heeft alleen de rechten die de worker en `flask seed` gebruiken (migratie 0010): `taakrun` lezen, aanmaken en bijwerken (hartslag); `logregel` lezen, aanmaken en verwijderen; `lid` lezen en verwijderen; `boot` alle vier; `afbeelding` lezen en verwijderen; `wachtlijst` lezen, aanmaken en verwijderen. Alleen voor seed: `rek`, `plaats_bootsoort` en `instelling` lezen en aanmaken, `plaats` lezen, aanmaken en bijwerken, `bootsoort` lezen en bijwerken (`FOR KEY SHARE` vraagt dat recht). Op `beheerder`, `passkey`, `uitnodiging` en `token` heeft de rol niets. Een nieuwe taak of een nieuwe tabel in seed vraagt om een eigen grant in de migratie van die slice.
- Valt de worker op het geplande tijdstip uit, dan draait de taak bij de eerstvolgende start nog dezelfde dag; een gemiste dag wordt niet ingehaald, de volgende run vangt alles op.
- Een nieuwe taak is een functie en een regel in de lijst van taken in `taken/`.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.4.0 | 2026-11-03 | Rechten van `botenloods_taken` beperkt tot worker en seed, per tabel beschreven | Issue #60, securityronde AEG-04 |
| v1.3.0 | 2026-11-02 | Opschoning gebouwd: sleutel van de lock, een mislukte run telt als run van die dag, `OPSCHOON_TIJDSTIP` bij `worker` | Bouw slice 9, issue #48 |
| v1.2.0 | 2026-10-31 | Termen gelijk aan de bouw: taak `ledenimport`, logactie `leden.import_aangevraagd` | Issue #22, bouw slice 6 |
| v1.1.0 | 2026-10-31 | Ledensynchronisatie uit de worker naar de integratiecontainer; de worker houdt heartbeat en opschoning | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
