# ADR-008 Opslag van foto's en logo

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.1.0
**Stories:** BLB-005, BLB-012, BLB-020, BLB-021, BLB-026, BLB-027

## Context

Een boot heeft hooguit één foto (backlog §8); de vereniging heeft één logo. De foto staat op de openbare pagina, het logo op elke pagina en op elk kaartje. Ongeldige bestanden worden geweigerd en de vorige afbeelding blijft staan (BLB-005). Sinds 2026-10-31 staat het logo in de installatie (docker-compose), niet in de applicatie; wijzigen is geen mutatie en wordt niet gelogd (intake). Bij het opschonen van een oud-lid verdwijnen ook de foto's (ADR-006). Foundation bepaalt grootte en bestandstypen.

Bij 180 boten en een foto van rond 250 kB na verkleinen gaat het om ongeveer 45 MB. Foto's van een telefoon bevatten vaak EXIF-gegevens met de GPS-locatie, bijvoorbeeld van het huis van het lid.

## Besluit

Foto's staan in PostgreSQL, in de tabel `afbeelding` als `bytea`.

**Logo.** Het logo is een bestand in de installatie. Compose koppelt de map `./huisstijl` alleen-lezen aan `web` op `/huisstijl`; `LOGO_BESTAND` (standaard `/huisstijl/logo.png`) wijst het bestand aan. `web` verwerkt het bij het starten met dezelfde regels als een upload (JPEG, PNG of WebP, hooguit 800 pixels, als PNG zonder metadata) en houdt het resultaat in het geheugen. Ontbreekt het bestand of is het ongeldig, dan meldt `web` dat in de containerlog en toont alleen de naam. Een nieuw logo vraagt een herstart van `web`. De route `/logo/<hash>` levert het, met een hash van de inhoud in de URL en een lange cache-header. Er is geen uploadscherm en geen logregel.

**Uploaden.** Nginx weigert verzoeken boven 10 MB. De applicatie opent het bestand met Pillow en accepteert alleen JPEG, PNG en WebP, op basis van de inhoud en niet van de bestandsnaam. Pillow verkleint foto's tot hooguit 1600 pixels aan de lange zijde, draait volgens de EXIF-oriëntatie en slaat opnieuw op als JPEG zonder metadata. `Image.MAX_IMAGE_PIXELS` begrenst decompressiebommen. Pas na een geslaagde verwerking vervangt de nieuwe afbeelding de oude, in één transactie met de logregel.

**SVG.** Wordt geweigerd. Een SVG kan script bevatten en is lastig veilig te maken.

**Uitleveren.** De route `/afbeelding/<sleutel>` levert de afbeelding met het opgeslagen mime-type, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff` en een lange cache-header. De sleutel is willekeurig (16 tekens) en wijzigt bij elke nieuwe upload, zodat caches nooit een oude foto tonen. Foto's van boten op een plaats zijn openbaar zichtbaar (intake: leden stemden in); de sleutel voorkomt dat iemand alle foto's ophaalt door te tellen. Nginx cachet de route kort om de applicatie te ontlasten.

## Alternatieven

| Optie | Voordelen | Nadelen |
|-------|-----------|---------|
| Bestanden op een Docker-volume | Kleinere database, Nginx levert direct | Tweede plek voor back-up; bestandsrechten voor een container zonder root; verwijderen bij opschonen niet in dezelfde transactie; wezen bij een fout |
| Objectopslag (S3-compatibel) | Schaalt ver | Extra dienst en inloggegevens per installatie, voor 45 MB |
| PostgreSQL `bytea` (gekozen) | Eén back-up, transactioneel met de rest, opschonen is één `DELETE`, geen volume of rechten | Database groeit met ongeveer 45 MB; elke afbeelding gaat door Flask |

## Gevolgen

- De back-up van de database bevat alle foto's. Het logo hoort bij de bestanden van de installatie, naast `docker-compose.yml` en `.env`.
- De rij `logo` in `instelling`, het logo in `afbeelding`, de route `/instellingen/logo` en de Nginx-locatie daarvoor verdwijnen; een migratie verwijdert ze.
- Een foto ophalen kost een databasequery; met de cache-header en de korte cache in Nginx is dat bij deze omvang geen probleem.
- Kaartjes printen voor 160 plaatsen laadt het logo één keer, dankzij dezelfde URL.
- Groeit een installatie ver boven 1000 foto's, dan is overstappen naar een volume een beperkte wijziging in `domein/afbeeldingen` en de route. Dat staat als `shortcut:`-opmerking in de code.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.1.0 | 2026-10-31 | Logo uit de installatie (`LOGO_BESTAND`), geen upload en geen logregel | Besluit stakeholder 2026-10-31 (issue #17) |
| v1.0.0 | 2026-10-30 | Eerste versie | |
