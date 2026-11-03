# ADR-003 Datamodel van plaatsen met stabiele identiteit

**Status:** Besloten door Foundation (indeling: issue #80)
**Datum:** 2026-11-03
**Versie:** v2.1.0
**Stories:** BLB-001 tot en met BLB-003, BLB-010, BLB-011, BLB-020, BLB-021, BLB-044

## Context

De loods bestaat uit rekken met een naam, verdiepingen 1 tot en met 5 en vakken 1 tot en met 12. Elk vak is een plaats met de aanduiding `<rek>/<verdieping>/<vak>`, zoals `A/1/1` (issue #80). Elk vak staat los aan of uit; gaten in de nummering mogen (A/1 heeft vak 1, 3, 4 en 6). Een geprint kaartje met QR-code moet na een hernoeming van het rek nog steeds naar dezelfde plaats leiden (overlay §5, contract plaatsnamen). De openbare pagina toont zonder inloggen de naam van de eigenaar en de foto van de boot (BLB-020). Een plaats heeft ten hoogste één boot, en een boot ten hoogste één plaats (backlog §8). Clubplaatsen zijn alleen voor clubboten (BLB-003).

Als de aanduiding in de URL van de QR-code staat, breekt elke hernoeming van een rek de kaartjes. Als een volgnummer in de URL staat, kan iedereen met een lus alle 224 pagina's ophalen en zo een lijst van alle eigenaren met foto maken. De leden stemden in met het tonen van hun naam per plaats, niet met een downloadbare ledenlijst.

## Besluit

Een plaats heeft drie identiteiten met elk een eigen doel:

| Veld | Doel | Wijzigt |
|------|------|---------|
| `id` (integer) | Interne sleutel voor relaties en het log | Nooit |
| `publieke_sleutel` | URL van de openbare pagina en de QR-code: `/p/<publieke_sleutel>` | Nooit |
| `code` | Wat mensen zien en zeggen: de aanduiding `A/1/1`, uniek | Alleen als de naam van het rek wijzigt |

De publieke sleutel is een willekeurige string van 10 tekens uit een alfabet zonder verwarrende tekens (geen 0, O, 1, l), gemaakt met `secrets` bij het aanmaken van de plaats. Dat geeft ruim 10^14 mogelijkheden; raden is niet zinvol. De QR-code bevat de volledige URL met `BASIS_URL` uit de omgeving.

### Indeling: rek, verdieping en vak

De plaatsen zelf zijn de indeling. Er komt geen kolom of tabel voor verdiepingen of vakken: welke verdiepingen en vakken een rek heeft, volgt uit de plaatsen.

| Tabel | Wijziging | Constraint |
|-------|-----------|------------|
| `rek` | `naam` wordt `String(10)` | Unieke index op `lower(naam)`; check `naam` niet leeg en zonder `/` |
| `rek` | Nieuw: `omschrijving` (`String(60)`, verplicht, standaard leeg) | |
| `plaats` | Nieuw: `verdieping` en `vak` (smallint, verplicht) | Check `verdieping BETWEEN 1 AND 5`, check `vak BETWEEN 1 AND 12`, uniek `(rek_id, verdieping, vak)` |
| `plaats` | Vervalt: `code`, `volgorde` en index `uq_plaats_code` | |

`code` is afgeleid en wordt niet opgeslagen. Het is een `column_property` op `Plaats`, een subquery met `rek.naam || '/' || verdieping || '/' || vak`. Zo houden API, export en logregels het veld `code`. De aanduiding is uniek zonder hoofdletters, omdat de reknaam dat is, een reknaam geen `/` bevat en verdieping en vak uniek zijn per rek. Volgorde in elke lijst: `rek.volgorde`, `rek.id`, `verdieping`, `vak`.

De domeinfunctie `indeling_instellen(rek, vakken)` krijgt de verzameling paren `(verdieping, vak)` die aan staan, zoals het raster op het scherm ze toont. Ze maakt de plaatsen die ontbreken en verwijdert de plaatsen die niet in de verzameling staan. De functie vergrendelt eerst het rek en daarna de plaatsen die verdwijnen (`FOR UPDATE`). Heeft één daarvan een boot, dan weigert ze met de melding van BLB-001. `toewijzen` vergrendelt boot en plaats en nooit het rek, dus er ontstaat geen deadlock. Een nieuwe plaats krijgt een publieke sleutel, geen bootsoorten en is geen clubplaats.

De toewijzing is het veld `plaats.boot_id`, nullable, met een unieke constraint. Leeg betekent vrij. Een aparte toewijzingstabel met historie is niet nodig: de historie staat in het mutatielog (ADR-006).

Clubplaats is een boolean op de plaats. Een clubboot is een boot zonder lid. De domeinfunctie `toewijzen` controleert in één transactie, met `SELECT ... FOR UPDATE` op de plaats: plaats vrij, bootsoort past, clubplaats hoort bij clubboot en omgekeerd, eigenaar is geen oud-lid, boot heeft nog geen plaats. Na toewijzen verdwijnt de boot van de wachtlijst.

Verwijderen van een rek, een plaats of een geschikte bootsoort met een toegewezen boot weigert de domeinlaag (BLB-001, BLB-002). Een rek verwijderen verwijdert alleen lege plaatsen. Een losse plaats uitzetten gaat via `indeling_instellen`.

De omschrijving van het rek, zoals "Grote botenloods stelling links", staat op de indeling, het kaartje en de openbare pagina. Ze hoort niet in de aanduiding. De grens is 60 tekens; de langste in de aangeleverde indeling is 52. Rek A is helemaal clubplaats: dat is `is_clubplaats` op elke plaats van A, zonder veld op het rek.

### Seed

`flask seed` bouwt de echte indeling op uit `app/seed_rekken.csv` (rek, omschrijving) en `app/seed_indeling.csv` (rek, verdieping, vak, bootsoort, clubplaats): 11 rekken, 224 plaatsen, waarvan 27 clubplaatsen. Een bootsoort die nog niet bestaat, zoals Wildwaterkano, voegt de seed toe zoals BLB-028 dat doet. Leden en boten blijven verzonnen. Een echte installatie vult de beheerder met de hand; er komt geen import van de indeling.

### Migratie

Migratie `0011` volgt op de huidige head `0010` (`0010_rechten_botenloods_taken.py`) en blijft de enige head. Upgrade: verwijder alle plaatsen en rekken (besluit 2 van #80; `plaats_bootsoort` gaat mee via `ON DELETE CASCADE`, boten verliezen alleen hun plaats), verkort `rek.naam`, voeg `rek.omschrijving`, index en checks toe, voeg `verdieping` en `vak` toe en verwijder `code`, `volgorde` en `uq_plaats_code`. Downgrade: voeg `code` (`String(20)`) en `volgorde` weer toe, vul `code` met de aanduiding en `volgorde` met `(verdieping - 1) * 12 + vak`, zet `uq_plaats_code` terug en verwijder de nieuwe kolommen (ook `omschrijving`), checks en index. De downgrade verliest geen plaatsen. Rechten veranderen niet.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Code in de URL, met een doorverwijzing van oude codes | Vraagt een tabel met oude codes; een oude code kan later aan een andere plaats worden gegeven, en dan wijst een oud kaartje naar de verkeerde plaats |
| Volgnummer (`id`) in de URL | Breekt niet bij hernoemen, maar maakt alle eigenaren in één lus op te halen |
| UUID in de URL | Werkt, maar geeft een dichtere, grotere QR-code; 10 tekens volstaan |
| Aparte tabel `toewijzing` met begin- en einddatum | Historie dubbel bijhouden naast het log; meer joins in elk overzicht |
| Tabel `verdieping` (rek, nummer, aantal_vakken) of een kolom `rek.vakken integer[]` naast de plaatsen | Legt de indeling twee keer vast; telling en plaatsen kunnen uit elkaar lopen |
| `code` opslaan en bijwerken bij een hernoeming van het rek | Een gegenereerde kolom kan in PostgreSQL geen andere tabel lezen; bijwerken in de domeinlaag is een tweede plek voor dezelfde waarheid |

## Gevolgen

- BLB-004 (plaatscode wijzigen) vervalt. Hernoemen van een rek verandert de aanduiding van alle plaatsen in dat rek en geeft één logregel voor het rek. Kaartjes blijven werken; alleen de tekst op het kaartje is dan verouderd.
- Een vak of verdieping uitzetten verandert de aanduiding van andere plaatsen niet; er blijft een gat.
- Een bezoeker kan een plaats niet op aanduiding opzoeken. Dat is besloten: de openbare pagina is alleen via de QR-link te openen (intake, besluit stakeholder 2026-10-30).
- Een publieke sleutel opnieuw genereren is bewust geen functie. Is een sleutel ooit ongewenst bekend, dan is dat geen probleem: de pagina is openbaar.
- De openbare pagina gebruikt een eigen leesfunctie die alleen de aanduiding, de omschrijving van het rek, bootnaam, foto-URL en naam van de eigenaar (of de naam van de vereniging bij een clubboot) ophaalt. De E2E-test controleert het volledige antwoord op afwezigheid van adres, telefoon, e-mail en lidnummer.
- Foto's op de openbare pagina hebben een eigen willekeurige sleutel (ADR-008), zodat ze ook niet op te tellen zijn.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v2.1.0 | 2026-11-03 | Vak 1 tot en met 12, elk vak los aan of uit; `rek.omschrijving`; `indeling_instellen` met paren; seed uit de twee CSV-bestanden | Nieuwe besluiten stakeholder, issue #80 |
| v2.0.0 | 2026-11-03 | Indeling in rek, verdieping en vak; `code` afgeleid in plaats van vrij en te wijzigen; BLB-004 vervalt; migratie 0011 | Besluiten stakeholder en standaardkeuzes regie, issue #80 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
