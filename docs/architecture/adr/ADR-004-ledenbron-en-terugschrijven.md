# ADR-004 Interface van de ledenbron en terugschrijven

**Status:** Aanvaard, 2026-10-30; herzien 2026-10-31 (integratiecontainer, ADR-012)
**Datum:** 2026-10-30
**Versie:** v2.1.0
**Stories:** BLB-006, BLB-007, BLB-008, BLB-009, BLB-026

## Context

Leden worden niet in de applicatie beheerd maar dagelijks opgehaald uit e-boekhouden, en handmatig te starten (intake). De koppeling moet vervangbaar zijn door een andere bron. Voor nu komt er een stub; de echte koppeling volgt later. Terugschrijven van het aantal boten per bootsoort per lid wordt voorbereid maar staat uit. Een lid dat uit de bron verdwijnt, wordt oud-lid en wordt niet verwijderd. Gegevens uit de bron zijn externe invoer (overlay §8). Sinds 2026-10-31 draait de koppeling in een aparte container die alleen via de API werkt (ADR-012).

## Besluit

De interface van de bron staat in de integratiecontainer (`integratie/`), niet in de applicatie. Hij heeft twee methoden, met per bron één klasse. De omgevingsvariabele `LEDENBRON` van de integratiecontainer kiest de klasse (`stub`, later `eboekhouden`). Zonder waarde meldt de container dat er geen bron is en roept hij de API niet aan (BLB-007).

| Methode | Levert of vraagt | Gedrag |
|---------|------------------|--------|
| `haal_leden()` | Een lijst van bronrecords: lidnummer, naam, adres, telefoon, e-mail, lid_sinds, opzegdatum | Gooit `LedenbronFout` bij een storing of een onleesbaar antwoord; de container meldt dat met `POST /api/v1/leden/import-mislukt` |
| `schrijf_bootaantallen(aantallen)` | Per lidnummer het aantal boten per bootsoort | Stub en e-boekhouden gooien `NietBeschikbaar` |
| `kan_terugschrijven` (eigenschap) | Ja of nee | In deze versie altijd nee |

De bron doet alleen transport en vertaling naar het bronrecord. De container stuurt de volledige lijst met `PUT /api/v1/leden`. Validatie en opslag zitten in `domein/leden` achter de API, zodat elke bron en elke vervangende container dezelfde regels krijgt. Inloggegevens van de bron staan alleen in de omgeving van de integratiecontainer; de applicatie kent ze niet.

De synchronisatie in `domein/leden` werkt in deze stappen, bij elke aanroep van `PUT /api/v1/leden`:

1. De lijst uit het verzoek nemen. Is het geen lijst, of zijn er meer dan 5000 records: 422, niets wijzigen. Een gemelde fout van de bron komt in `taakrun`, met een reden uit een vaste lijst (BLB-006).
2. Elk record valideren: lidnummer verplicht, tekstvelden ingekort tot een maximumlengte, datums geldig, e-mail op vorm. Een ongeldig record wordt overgeslagen en geteld, zonder de inhoud te loggen.
3. Veiligheidsgrens: komen er minder dan de helft van het huidige aantal actieve leden terug, dan breekt de synchronisatie af met 409. Een kapotte bron of een container die een halve lijst stuurt, maakt zo niet alle leden oud-lid.
4. Records met een opzegdatum van meer dan 5 jaar geleden die lokaal niet bestaan, worden overgeslagen. Anders zou de synchronisatie een opgeschoond oud-lid opnieuw aanmaken.
5. In één transactie: nieuwe leden aanmaken, gewijzigde bijwerken, leden die ontbreken krijgen `uit_bron_op` met de datum van vandaag. Boten van leden die oud-lid worden, gaan van de wachtlijst (BLB-008).
6. Wijzigingen in leden komen niet in het log; de aantallen staan in `taakrun`. Een mutatie in de botenadministratie die de import veroorzaakt, krijgt wel een logregel met het robottoken als actor (BLB-024, besluit stakeholder 2026-10-31).

De stub in de integratiecontainer leest leden uit een JSON-bestand (`LEDENBRON_STUB_BESTAND`). De tests van de applicatie sturen het fixturebestand `tests/fixtures/leden.json` rechtstreeks naar `PUT /api/v1/leden`; dat is de nepbron.

Terugschrijven: de domeinlaag berekent de aantallen per lid per bootsoort; de lijst per lid toont ze en `GET /api/v1/bootaantallen` levert ze (BLB-009). De instelling "terugschrijven" in de applicatie vervalt. In de integratiecontainer gooit `schrijf_bootaantallen` `NietBeschikbaar` en draait geen taak die terugschrijft.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Plug-insysteem met entry points | Eén vereniging per installatie; een eigen container of een keuze in de omgeving volstaat |
| Bron schrijft direct in de database | Validatie en log per bron dubbel; een fout in een bron raakt de gegevens |
| Leden die verdwijnen verwijderen | In strijd met de intake |
| Terugschrijven nu al bouwen achter een vlag | Code zonder gebruiker en zonder test tegen het echte systeem; de interface en de berekening volstaan |

## Gevolgen

- Een nieuwe bron is één klasse en een waarde voor `LEDENBRON` in de integratiecontainer, of een eigen container met de aanroepen uit ADR-012. Aegis beoordeelt de echte e-boekhoudenkoppeling vóór de commit.
- De oud-ledenstatus is afgeleid uit opzegdatum en `uit_bron_op`; verdwijnt een lid zonder opzegdatum uit de bron, dan telt de datum waarop de synchronisatie het lid niet meer vond als opzegdatum (besloten door de stakeholder, 2026-10-30, architectuur §9 besluit 4).
- De veiligheidsgrens kan een echte massale opzegging tegenhouden. Bij 210 leden is dat onwaarschijnlijk; de beheerder ziet de afbreking op de statuspagina.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v2.1.0 | 2026-10-31 | Geen logregels voor wijzigingen in leden; een gemelde fout alleen in `taakrun` | Besluit stakeholder 2026-10-31 (backlog vraag 20) |
| v2.0.0 | 2026-10-31 | De bron draait in de integratiecontainer; de synchronisatie start met `PUT /api/v1/leden`; instelling "terugschrijven" vervalt | Besluiten stakeholder 2026-10-31, ADR-012 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
