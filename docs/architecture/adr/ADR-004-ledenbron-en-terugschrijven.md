# ADR-004 Interface van de ledenbron en terugschrijven

**Status:** Aanvaard, 2026-10-30
**Datum:** 2026-10-30
**Stories:** BLB-006, BLB-007, BLB-008, BLB-009, BLB-026

## Context

Leden worden niet in de applicatie beheerd maar dagelijks opgehaald uit e-boekhouden, en handmatig te starten (intake). De koppeling moet vervangbaar zijn door een andere bron. Voor nu komt er een stub; de echte koppeling volgt later. Terugschrijven van het aantal boten per bootsoort per lid wordt voorbereid maar staat uit. Een lid dat uit de bron verdwijnt, wordt oud-lid en wordt niet verwijderd. Gegevens uit de bron zijn externe invoer (overlay §8).

## Besluit

De module `ledenbron` heeft één interface met twee methoden, en per bron één klasse. De omgevingsvariabele `LEDENBRON` kiest de klasse (`stub`, later `eboekhouden`). Zonder waarde meldt de synchronisatie dat er geen bron is en wijzigt niets (BLB-007).

| Methode | Levert of vraagt | Gedrag |
|---------|------------------|--------|
| `haal_leden()` | Een lijst van bronrecords: lidnummer, naam, adres, telefoon, e-mail, lid_sinds, opzegdatum | Gooit `LedenbronFout` bij een storing of een onleesbaar antwoord |
| `schrijf_bootaantallen(aantallen)` | Per lidnummer het aantal boten per bootsoort | Stub en e-boekhouden gooien `NietBeschikbaar` |
| `kan_terugschrijven` (eigenschap) | Ja of nee | In deze versie altijd nee |

De bron doet alleen transport en vertaling naar het bronrecord. Validatie en opslag zitten in `domein/leden`, zodat elke bron dezelfde regels krijgt. Inloggegevens leest de bronklasse zelf uit de omgeving; ze gaan niet door de rest van de applicatie.

De synchronisatie in `domein/leden` werkt in deze stappen:

1. Alle records ophalen. Bij `LedenbronFout`: afbreken, niets wijzigen, fout in `taakrun` en log (BLB-006).
2. Elk record valideren: lidnummer verplicht, tekstvelden ingekort tot een maximumlengte, datums geldig, e-mail op vorm. Een ongeldig record wordt overgeslagen en geteld, zonder de inhoud te loggen.
3. Veiligheidsgrens: komen er minder dan de helft van het huidige aantal actieve leden terug, dan breekt de synchronisatie af. Een kapotte bron maakt zo niet alle leden oud-lid.
4. Records met een opzegdatum van meer dan 5 jaar geleden die lokaal niet bestaan, worden overgeslagen. Anders zou de synchronisatie een opgeschoond oud-lid opnieuw aanmaken.
5. In één transactie: nieuwe leden aanmaken, gewijzigde bijwerken, leden die ontbreken krijgen `uit_bron_op` met de datum van vandaag. Boten van leden die oud-lid worden, gaan van de wachtlijst (BLB-008).
6. Per gewijzigd lid één logregel met de namen van de gewijzigde velden, zonder de waarden van adres, telefoon of e-mail (BLB-024).

De stub leest leden uit een JSON-bestand (`LEDENBRON_STUB_BESTAND`, standaard `tests/fixtures/leden.json`). Dezelfde stub is de nepbron in de tests.

Terugschrijven: de domeinlaag kan de aantallen per lid per bootsoort berekenen; die toont de lijst per lid (BLB-009). De instelling "terugschrijven" bestaat in de applicatie, maar opslaan als aan geeft de melding dat het in deze versie niet beschikbaar is, zolang `kan_terugschrijven` nee is. Er draait geen taak die terugschrijft.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Plug-insysteem met entry points | Eén vereniging per installatie en twee bronnen; een keuze in de omgeving volstaat |
| Bron schrijft direct in de database | Validatie en log per bron dubbel; een fout in een bron raakt de gegevens |
| Leden die verdwijnen verwijderen | In strijd met de intake |
| Terugschrijven nu al bouwen achter een vlag | Code zonder gebruiker en zonder test tegen het echte systeem; de interface en de berekening volstaan |

## Gevolgen

- Een nieuwe bron is één klasse en een waarde voor `LEDENBRON`. Aegis beoordeelt de echte e-boekhoudenkoppeling vóór de commit.
- De oud-ledenstatus is afgeleid uit opzegdatum en `uit_bron_op`; verdwijnt een lid zonder opzegdatum uit de bron, dan telt de datum waarop de synchronisatie het lid niet meer vond als opzegdatum (besloten door de stakeholder, 2026-10-30, architectuur §9 besluit 4).
- De veiligheidsgrens kan een echte massale opzegging tegenhouden. Bij 210 leden is dat onwaarschijnlijk; de beheerder ziet de afbreking op de statuspagina.
