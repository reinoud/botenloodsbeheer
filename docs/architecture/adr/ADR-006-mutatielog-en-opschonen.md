# ADR-006 Mutatielog en opschonen

**Status:** Aanvaard, 2026-10-30
**Datum:** 2026-10-30
**Versie:** v1.0.0
**Stories:** BLB-024, BLB-025, BLB-026, BLB-033, BLB-034

## Context

Elke mutatie wordt gelogd en onder elk overzicht staat het log dat erbij hoort (intake, overlay §5). Het log bevat tijdstip, wie of wat de wijziging deed, wat er veranderde en waar relevant oud en nieuw, maar geen wachtwoorden, tokenwaarden, adressen, telefoonnummers of e-mailadressen (BLB-024). Beheerders kunnen het log niet wijzigen. Logregels worden na 5 jaar verwijderd, gerekend vanaf de mutatie. Gegevens van een oud-lid worden 5 jaar na de opzegdatum verwijderd, maar niet zolang het oud-lid nog een boot of plaats in de loods heeft. Geweigerde API-aanroepen komen ook in het log (BLB-033, BLB-034). Geslaagde aanroepen en wijzigingen in leden door de import komen er niet in; mutaties aan boten wel, ook als een import ze veroorzaakt (besluit stakeholder 2026-10-31).

## Besluit

Er is één tabel `logregel`, alleen voor toevoegen.

| Veld | Inhoud |
|------|--------|
| tijdstip | Tijdstip met tijdzone |
| soort | `mutatie` of `api` |
| actor_soort, actor_id, actor_naam | Beheerder, token of taak; de naam wordt bij schrijven vastgelegd zodat hij blijft na het verwijderen van een account of token |
| actie | Vaste code, bijvoorbeeld `plaats.toegewezen`, `lid.bijgewerkt`, `token.geweigerd` |
| verwijzingen | Array van tekst als `plaats:12`, `rek:3`, `boot:40`, `lid:7` |
| gegevens | JSON met oud en nieuw, alleen voor velden die er mogen staan |

**Schrijven.** Alleen `domein/log` schrijft, aangeroepen vanuit elke wijzigende domeinfunctie in dezelfde transactie. Een lijst met verboden velden (adres, telefoon, e-mail, tokenwaarde) wordt bij schrijven gecontroleerd; bij die velden komt alleen "gewijzigd" in het log. Een lid staat in het log als verwijzing (`lid:7`), niet met naam: de naam wordt bij het tonen opgehaald. Na het opschonen van het lid toont het log "verwijderd lid". Zo blijft na opschonen geen naam achter in logregels die nog niet 5 jaar oud zijn.

**Afscherming.** De applicatie heeft geen functie om logregels te wijzigen of te verwijderen. De database-gebruiker van de applicatie heeft op `logregel` alleen `INSERT` en `SELECT`. De opschoning draait in de worker met een aparte database-gebruiker die ook `DELETE` mag. Een fout in de webcode kan het log zo niet aantasten.

**Tonen.** Elk overzicht heeft een vaste filter op het log: het plaatsdetail toont regels met `plaats:<id>` en de boot erop, een rek toont regels van zijn plaatsen, het overzicht vrije plaatsen toont toewijzen en vrijgeven, de wachtlijst toont wachtlijstacties, het tokenoverzicht toont regels van soort `api`. Een GIN-index op `verwijzingen` en een index op `tijdstip` houden dit snel. Elk log toont de nieuwste 50 regels met een link naar meer.

**Opschonen.** Een dagelijkse taak (ADR-007) doet in één transactie:

1. Logregels met een tijdstip van meer dan 5 jaar geleden verwijderen.
2. Oud-leden zoeken waarvan de startdatum (opzegdatum, of `uit_bron_op` als die ontbreekt, besloten door de stakeholder op 2026-10-30, architectuur §9 besluit 4) meer dan 5 jaar geleden ligt en waarvan geen boot een plaats heeft (besloten, besluit 3). De boten en foto's van het oud-lid gaan mee.
3. Van die oud-leden de boten, foto's en het lid zelf verwijderen.
4. Aantallen vastleggen in `taakrun` en één logregel `opschoning.uitgevoerd` met alleen de aantallen (BLB-026).

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Logtabel per entiteit of SQLAlchemy-historie | Meer tabellen, geen gedeelde weergave onder overzichten |
| Databasetriggers die het log schrijven | Weten niet wie de actor is zonder sessievariabelen; regels voor verboden velden in SQL |
| Naam van het lid in de logregel | Blijft na opschonen van het lid nog jaren staan |
| API-aanroepen alleen naar stdout | Beheerders hebben geen serverrol en zouden geweigerde pogingen niet zien |
| Logregels pseudonimiseren in plaats van verwijderen | Termijn van 5 jaar is een besluit; verwijderen is eenvoudiger en volgt het besluit |

## Gevolgen

- Een nieuwe wijzigende functie zonder logregel valt op in de review en in een test die per domeinfunctie controleert dat er een regel bijkomt.
- Een robot die elke minuut vraagt, geeft geen logregels; alleen weigeringen tellen mee.
- Back-ups bevatten verwijderde gegevens langer dan 5 jaar, tenzij hun bewaartermijn is afgestemd (architectuur §10, open vraag 1).

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v1.0.0 | 2026-10-31 | Geslaagde API-aanroepen en wijzigingen in leden door de import niet in het log; versie en wijzigingslog toegevoegd | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
