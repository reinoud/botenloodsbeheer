# ADR-003 Datamodel van plaatsen met stabiele identiteit

**Status:** Besloten door Foundation (indeling: issue #80, #83)
**Datum:** 2026-11-05
**Versie:** v2.3.0
**Stories:** BLB-001 tot en met BLB-003, BLB-010, BLB-011, BLB-020, BLB-021, BLB-044

## Context

De loods bestaat uit rekken met een naam, verdiepingen 1 tot en met 5 en vakken 1 tot en met 12. Elk vak is een plaats met de aanduiding `<rek>/<verdieping>/<vak>`, zoals `A/1/1` (issue #80). Elk vak staat aan of uit, maar een verdieping heeft geen gaten: haar vakken zijn altijd 1 tot en met n (issue #94). Een verdieping zonder plaatsen onder de hoogste mag wel. Een geprint kaartje met QR-code moet na een hernoeming van het rek nog steeds naar dezelfde plaats leiden (overlay §5, contract plaatsnamen). De openbare pagina toont zonder inloggen de naam van de eigenaar en de foto van de boot (BLB-020). Een plaats heeft ten hoogste één boot, en een boot ten hoogste één plaats (backlog §8). Clubplaatsen zijn alleen voor clubboten (BLB-003).

Als de aanduiding in de URL van de QR-code staat, breekt elke hernoeming van een rek de kaartjes. Als een volgnummer in de URL staat, kan iedereen met een lus alle 229 pagina's ophalen en zo een lijst van alle eigenaren met foto maken. De leden stemden in met het tonen van hun naam per plaats, niet met een downloadbare ledenlijst.

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
| `verdieping_bootsoort` | Nieuw: `rek_id`, `verdieping` (smallint), `bootsoort_id` (issue #83) | Primaire sleutel `(rek_id, verdieping)`; check `verdieping BETWEEN 1 AND 5`; `rek_id` en `bootsoort_id` met `ON DELETE CASCADE` |

`code` is afgeleid en wordt niet opgeslagen. Het is een `column_property` op `Plaats`, een subquery met `rek.naam || '/' || verdieping || '/' || vak`. Zo houden API, export en logregels het veld `code`. De aanduiding is uniek zonder hoofdletters, omdat de reknaam dat is, een reknaam geen `/` bevat en verdieping en vak uniek zijn per rek. Volgorde in elke lijst: `rek.volgorde`, `rek.id`, `verdieping`, `vak`.

De domeinfunctie `indeling_instellen(rek, vakken)` krijgt de verzameling paren `(verdieping, vak)` die aan staan, zoals het raster op het scherm ze toont. Ze maakt de plaatsen die ontbreken en verwijdert de plaatsen die niet in de verzameling staan. De functie vergrendelt eerst het rek en daarna alle plaatsen van dat rek (`FOR UPDATE`). Heeft één daarvan een boot, dan weigert ze met de melding van BLB-001. `toewijzen` vergrendelt boot en plaats en nooit het rek, dus er ontstaat geen deadlock. Een nieuwe plaats krijgt een publieke sleutel en is geen clubplaats. Ze krijgt de bootsoort van haar verdieping, als die er is; bestaande plaatsen blijven (vraag 26).

De toewijzing is het veld `plaats.boot_id`, nullable, met een unieke constraint. Leeg betekent vrij. Een aparte toewijzingstabel met historie is niet nodig: de historie staat in het mutatielog (ADR-006).

Clubplaats is een boolean op de plaats. Een clubboot is een boot zonder lid. De domeinfunctie `toewijzen` controleert in één transactie, met `SELECT ... FOR UPDATE` op de plaats: plaats vrij, bootsoort past, clubplaats hoort bij clubboot en omgekeerd, eigenaar is geen oud-lid, boot heeft nog geen plaats. Na toewijzen verdwijnt de boot van de wachtlijst.

Verwijderen van een rek of een geschikte bootsoort met een toegewezen boot weigert de domeinlaag (BLB-001, BLB-002). Een rek verwijderen verwijdert alleen lege plaatsen. Een plaats verdwijnt alleen via `indeling_instellen`, als haar vak in het raster uit gaat. `plaats_verwijderen` en de route `POST /plaatsen/<id>/verwijderen` vervallen (BLB-044, issue #83).

### Bootsoort per verdieping

`verdieping_bootsoort` onthoudt per verdieping hooguit één bootsoort. Welke verdiepingen bestaan, volgt uit de plaatsen. Zonder keuze is er geen rij. De rij blijft als de verdieping leeg raakt.

`rek_aanmaken` krijgt per verdieping een optionele bootsoort-id en leest die met `FOR KEY SHARE`, zoals `_soorten`. Een onbekende of ongeldige id weigert het hele rek. Een keuze bij een verdieping zonder vak valt weg. In het technische log (ADR-006) krijgen `rek.aangemaakt` en `plaats.aangemaakt` de naam van de bootsoort.

Wordt de bootsoort verwijderd, dan verdwijnt de rij via de cascade; `bootsoort.verwijderd` dekt het log. Weigeren maakt de soort onverwijderbaar, want geen scherm wist de keuze.

De omschrijving van het rek, zoals "Grote botenloods stelling links", staat op de indeling, het kaartje en de openbare pagina. Ze hoort niet in de aanduiding. De grens is 60 tekens; de langste in de aangeleverde indeling is 52. Rek A is helemaal clubplaats: dat is `is_clubplaats` op elke plaats van A, zonder veld op het rek.

### Seed

`flask seed` bouwt de echte indeling op uit `app/seed_rekken.csv` (rek, omschrijving) en `app/seed_indeling.csv` (rek, verdieping, vak, bootsoort, clubplaats): 11 rekken, 229 plaatsen, waarvan 30 clubplaatsen (heel rek A). Een bootsoort die nog niet bestaat, zoals Wildwaterkano, voegt de seed toe zoals BLB-028 dat doet. Leden en boten blijven verzonnen. Een echte installatie vult de beheerder met de hand; er komt geen import van de indeling.

### Migratie

Migratie `0011` volgt op de huidige head `0010` (`0010_rechten_botenloods_taken.py`) en blijft de enige head. Upgrade: verwijder alle plaatsen en rekken (besluit 2 van #80; `plaats_bootsoort` gaat mee via `ON DELETE CASCADE`, boten verliezen alleen hun plaats), verkort `rek.naam`, voeg `rek.omschrijving`, index en checks toe, voeg `verdieping` en `vak` toe en verwijder `code`, `volgorde` en `uq_plaats_code`. Downgrade: voeg `code` (`String(20)`) en `volgorde` weer toe, vul `code` met de aanduiding en `volgorde` met `(verdieping - 1) * 12 + vak`, zet `uq_plaats_code` terug en verwijder de nieuwe kolommen (ook `omschrijving`), checks en index. De downgrade verliest geen plaatsen. Rechten: de rol `botenloods_taken` krijgt INSERT op `bootsoort` en USAGE op `bootsoort_id_seq`, omdat `flask seed` als die rol Wildwaterkano toevoegt; de downgrade trekt beide in.

Migratie `0012` volgt op `0011` en is de enige head. Upgrade: maak `verdieping_bootsoort`, met SELECT, INSERT en DELETE voor `botenloods_web`; bestaande rekken krijgen geen rijen. Downgrade: verwijder de tabel; plaatsen houden hun bootsoorten.

Migratie `0013` volgt op `0012` en is de enige head. Upgrade: trek DELETE op `verdieping_bootsoort` in voor `botenloods_web`. Geen code verwijdert rijen uit die tabel; de cascades vanuit `rek` en `bootsoort` draaien als eigenaar van de tabel (issue #85). Downgrade: geef het recht terug.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Code in de URL, met een doorverwijzing van oude codes | Vraagt een tabel met oude codes; een oude code kan later aan een andere plaats worden gegeven, en dan wijst een oud kaartje naar de verkeerde plaats |
| Volgnummer (`id`) in de URL | Breekt niet bij hernoemen, maar maakt alle eigenaren in één lus op te halen |
| UUID in de URL | Werkt, maar geeft een dichtere, grotere QR-code; 10 tekens volstaan |
| Aparte tabel `toewijzing` met begin- en einddatum | Historie dubbel bijhouden naast het log; meer joins in elk overzicht |
| Tabel `verdieping` (rek, nummer, aantal_vakken) of een kolom `rek.vakken integer[]` naast de plaatsen | Legt de indeling twee keer vast; telling en plaatsen kunnen uit elkaar lopen |
| Kolom `rek.bootsoorten` (JSON of array) | Geen verwijzende sleutel: een verwijderde bootsoort laat een dode id achter |
| Vijf kolommen `bootsoort_v1` tot en met `bootsoort_v5` op `rek` | Vijf keer dezelfde regel; de grens 5 op twee plekken |
| Afleiden uit de plaatsen van de verdieping | Onduidelijk bij gemengde soorten; vraag 26b vraagt dat het rek onthoudt |
| `code` opslaan en bijwerken bij een hernoeming van het rek | Een gegenereerde kolom kan in PostgreSQL geen andere tabel lezen; bijwerken in de domeinlaag is een tweede plek voor dezelfde waarheid |

## Gevolgen

- BLB-004 (plaatscode wijzigen) vervalt. Hernoemen van een rek verandert de aanduiding van alle plaatsen in dat rek en geeft één logregel voor het rek. Kaartjes blijven werken; alleen de tekst op het kaartje is dan verouderd.
- Een vak of verdieping uitzetten verandert de aanduiding van andere plaatsen niet. Een vak mag alleen uit als de vakken erboven op die verdieping ook uit gaan: `_vakken` in `app/domein/indeling.py` weigert een verdieping met een gat, bij aanmaken en bij `indeling_instellen`, met een melding die verdieping en eerste ontbrekend vak noemt. De database dwingt dit niet af; een bestaande installatie met een gat kan de indeling van dat rek pas opslaan als het gat is gevuld.
- Het rekoverzicht (BLB-044) toont per rek zoveel kolommen als het hoogste vaknummer en zoveel verdiepingen als de hoogste verdieping met een plaats. De CSP staat geen inline `style` toe, dus het aantal kolommen is een CSS-klasse (`raster-rek-1` tot en met `raster-rek-12`).
- Een bezoeker kan een plaats niet op aanduiding opzoeken. Dat is besloten: de openbare pagina is alleen via de QR-link te openen (intake, besluit stakeholder 2026-10-30).
- Een publieke sleutel opnieuw genereren is bewust geen functie. Is een sleutel ooit ongewenst bekend, dan is dat geen probleem: de pagina is openbaar.
- De openbare pagina gebruikt een eigen leesfunctie die alleen de aanduiding, de omschrijving van het rek, bootnaam, foto-URL, naam van de eigenaar (of de naam van de vereniging bij een clubboot) en de vlag clubplaats ophaalt. De E2E-test controleert het volledige antwoord op afwezigheid van adres, telefoon, e-mail en lidnummer.
- Foto's op de openbare pagina hebben een eigen willekeurige sleutel (ADR-008), zodat ze ook niet op te tellen zijn.

## Wijzigingslog

| Versie | Datum | Wijziging | Reden |
|--------|-------|-----------|-------|
| v2.3.0 | 2026-11-05 | Een verdieping heeft geen gaten (validatie in het domein, geen migratie); seed aangevuld tot 229 plaatsen en 30 clubplaatsen; rekoverzicht zonder lege kolommen en verdiepingen | Besluiten stakeholder 2026-11-05, issue #94 |
| v2.2.1 | 2026-11-04 | `botenloods_web` houdt SELECT en INSERT op `verdieping_bootsoort`; DELETE vervalt in migratie 0013 | Restpunt uit de reviews van #83, issue #85 |
| v2.2.0 | 2026-11-04 | Tabel `verdieping_bootsoort`; nieuwe plaats krijgt de bootsoort van haar verdieping; `plaats_verwijderen` vervalt; migratie 0012 | Besluiten stakeholder, vraag 26 en issue #83 |
| v2.1.1 | 2026-11-04 | `indeling_instellen` vergrendelt alle plaatsen van het rek; migratie 0011 geeft `botenloods_taken` INSERT op `bootsoort` en USAGE op de reeks | Afwijkingen gemeld bij de bouw van slice 12, issue #80 |
| v2.1.0 | 2026-11-03 | Vak 1 tot en met 12, elk vak los aan of uit; `rek.omschrijving`; `indeling_instellen` met paren; seed uit de twee CSV-bestanden | Nieuwe besluiten stakeholder, issue #80 |
| v2.0.0 | 2026-11-03 | Indeling in rek, verdieping en vak; `code` afgeleid in plaats van vrij en te wijzigen; BLB-004 vervalt; migratie 0011 | Besluiten stakeholder en standaardkeuzes regie, issue #80 |
| v1.0.0 | 2026-10-30 | Eerste versie | |
