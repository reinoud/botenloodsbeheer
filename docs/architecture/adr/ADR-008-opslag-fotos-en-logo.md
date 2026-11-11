# ADR-008 Opslag van foto's en logo

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Versie:** v1.4.1
**Stories:** BLB-005, BLB-012, BLB-020, BLB-021, BLB-026, BLB-027

## Context

Een boot heeft hooguit één foto (backlog §8); de vereniging heeft één logo. De foto staat op de openbare pagina, het logo op elke pagina en op elk kaartje. Ongeldige bestanden worden geweigerd en de vorige afbeelding blijft staan (BLB-005). Sinds 2026-11-08 uploadt een beheerder het logo in de applicatie (issue #186); tussen 2026-10-31 en 2026-11-08 stond het in de installatie. Bij het opschonen van een oud-lid verdwijnen ook de foto's (ADR-006). Foundation bepaalt grootte en bestandstypen.

Bij 180 boten en een foto van rond 250 kB na verkleinen gaat het om ongeveer 45 MB. Foto's van een telefoon bevatten vaak EXIF-gegevens met de GPS-locatie, bijvoorbeeld van het huis van het lid.

## Besluit

Foto's staan in PostgreSQL, in de tabel `afbeelding` als `bytea`.

**Logo.** Het logo is een afbeelding van soort `logo` in dezelfde tabel; de rij `logo` in `instelling` wijst ernaar en wordt bij elke wijziging vergrendeld, zodat er één logo is. Een beheerder uploadt, vervangt en verwijdert het op Instellingen, met een inlog van hooguit 10 minuten oud. De verwerking is die van een foto, behalve: hooguit 800 pixels aan de lange zijde en opnieuw opgeslagen als PNG zonder metadata. Elke worker van `web` leest het uit de database, dus een wijziging is direct overal zichtbaar. De route `/logo/<sleutel>` levert het, met de sleutel van de afbeelding in de URL (nieuw bij elke upload) en een lange cache-header; een sleutel van een foto geeft 404. Zonder logo toont de kopbalk alleen de naam. Uploaden en verwijderen staan in het technische log (`instelling.logo_toegevoegd`, `instelling.logo_vervangen`, `instelling.logo_verwijderd`), met de afmetingen en zonder inhoud. De applicatie begrenst het op 10 MB (`UPLOAD_MAX`); Traefik heeft op `/instellingen/logo` 25 MB als buitengrens (ADR-013).

**Uploaden.** De applicatie weigert een bestand boven 10 MB (`UPLOAD_MAX`) en stuurt de beheerder met de melding "Dit bestand is groter dan 10 MB. Kies een kleiner bestand." terug naar het formulier, met het blok open (logo, Foto vervangen, nieuwe boot). Traefik weigert verzoeken boven 25 MB (ADR-013) met een 413 zonder uitleg. De applicatie opent het bestand met Pillow en accepteert alleen JPEG, PNG en WebP, op basis van de inhoud en niet van de bestandsnaam. Een JPEG met meer beelden (MPO, zoals sommige telefoons die maken) telt als JPEG; alleen het eerste beeld wordt verwerkt. Pillow verkleint foto's tot hooguit 1600 pixels aan de lange zijde, draait volgens de EXIF-oriëntatie en slaat opnieuw op als JPEG zonder metadata. `Image.MAX_IMAGE_PIXELS` begrenst decompressiebommen. Pas na een geslaagde verwerking vervangt de nieuwe afbeelding de oude, in één transactie met de logregel. Een ongeldig bestand geeft één melding met de tekst uit `afbeeldingen.verwerk`, zonder bestandsnaam. Zowel bij een ongeldig als bij een te groot bestand staat erachter "De vorige blijft staan.", maar alleen als er al een logo of foto is.

**SVG.** Wordt geweigerd. Een SVG kan script bevatten en is lastig veilig te maken.

**Uitleveren.** De route `/afbeelding/<sleutel>` levert de afbeelding met het opgeslagen mime-type, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff` en een lange cache-header. De sleutel is willekeurig (16 tekens) en wijzigt bij elke nieuwe upload, zodat caches nooit een oude foto tonen. Foto's van boten op een plaats zijn openbaar zichtbaar (intake: leden stemden in); de sleutel voorkomt dat iemand alle foto's ophaalt door te tellen.

## Alternatieven

| Optie | Voordelen | Nadelen |
|-------|-----------|---------|
| Bestanden op een Docker-volume | Kleinere database, de proxy levert direct | Tweede plek voor back-up; bestandsrechten voor een container zonder root; verwijderen bij opschonen niet in dezelfde transactie; wezen bij een fout |
| Objectopslag (S3-compatibel) | Schaalt ver | Extra dienst en inloggegevens per installatie, voor 45 MB |
| PostgreSQL `bytea` (gekozen) | Eén back-up, transactioneel met de rest, opschonen is één `DELETE`, geen volume of rechten | Database groeit met ongeveer 45 MB; elke afbeelding gaat door Flask |

## Gevolgen

- De back-up van de database bevat alle foto's en het logo. `LOGO_BESTAND` en de map `./huisstijl` bestaan niet meer; een logo uit de installatie wordt niet overgenomen en moet één keer worden geüpload.
- Migratie 0017 laat in `afbeelding` weer de soort `logo` toe. De downgrade verwijdert het logo.
- Een foto ophalen kost een databasequery; met de cache-header is dat bij deze omvang geen probleem.
- Kaartjes printen voor 229 plaatsen laadt het logo één keer, dankzij dezelfde URL.
- Groeit een installatie ver boven 1000 foto's, dan is overstappen naar een volume een beperkte wijziging in `domein/afbeeldingen` en de route. Dat staat als `shortcut:`-opmerking in de code.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.4.1 | 2026-11-11 | Omvang 229 plaatsen volgens de echte indeling | Issue #236 |
| v1.4.0 | 2026-11-10 | Grens van 10 MB in de applicatie met een melding; Traefik heeft 25 MB als buitengrens; "De vorige blijft staan." alleen met een vorige | Besluit stakeholder 2026-11-10, issue #190 |
| v1.3.0 | 2026-11-08 | Logo weer in de database, uploaden en verwijderen op Instellingen met logregel; `LOGO_BESTAND` en `./huisstijl` vervallen; migratie 0017 | Besluit stakeholder 2026-11-08, issue #186 |
| v1.2.1 | 2026-11-04 | MPO telt als JPEG, alleen het eerste beeld | Issue #70 |
| v1.2.0 | 2026-10-31 | Grens van 10 MB in Traefik; geen korte cache in de proxy (Traefik heeft er geen, en hij was niet gebouwd) | Besluit stakeholder 2026-10-31, issue #29 (ADR-013) |
| v1.1.0 | 2026-10-31 | Logo uit de installatie (`LOGO_BESTAND`), geen upload en geen logregel | Besluit stakeholder 2026-10-31 (issue #17) |
| v1.0.0 | 2026-10-30 | Eerste versie | |
