# ADR-003 Datamodel van plaatsen met stabiele identiteit

**Status:** Besloten door Foundation
**Datum:** 2026-10-30
**Stories:** BLB-001 tot en met BLB-004, BLB-010, BLB-011, BLB-020, BLB-021

## Context

Een plaats heeft een unieke code die later te wijzigen is (intake, BLB-004). Een geprint kaartje met QR-code moet daarna nog steeds naar dezelfde plaats leiden (overlay §5, contract plaatsnamen). De openbare pagina toont zonder inloggen de naam van de eigenaar en de foto van de boot (BLB-020). Een plaats heeft ten hoogste één boot, en een boot ten hoogste één plaats (backlog §8). Clubplaatsen zijn alleen voor clubboten (BLB-003).

Als de code in de URL van de QR-code staat, breekt elke hernoeming de kaartjes. Als een volgnummer in de URL staat, kan iedereen met een lus alle 160 pagina's ophalen en zo een lijst van alle eigenaren met foto maken. De leden stemden in met het tonen van hun naam per plaats, niet met een downloadbare ledenlijst.

## Besluit

Een plaats heeft drie identiteiten met elk een eigen doel:

| Veld | Doel | Wijzigt |
|------|------|---------|
| `id` (integer) | Interne sleutel voor relaties en het log | Nooit |
| `publieke_sleutel` | URL van de openbare pagina en de QR-code: `/p/<publieke_sleutel>` | Nooit |
| `code` | Wat mensen zien en zeggen, uniek | Door de beheerder |

De publieke sleutel is een willekeurige string van 10 tekens uit een alfabet zonder verwarrende tekens (geen 0, O, 1, l), gemaakt met `secrets` bij het aanmaken van de plaats. Dat geeft ruim 10^14 mogelijkheden; raden is niet zinvol. De QR-code bevat de volledige URL met `BASIS_URL` uit de omgeving.

De toewijzing is het veld `plaats.boot_id`, nullable, met een unieke constraint. Leeg betekent vrij. Een aparte toewijzingstabel met historie is niet nodig: de historie staat in het mutatielog (ADR-006).

Clubplaats is een boolean op de plaats. Een clubboot is een boot zonder lid. De domeinfunctie `toewijzen` controleert in één transactie, met `SELECT ... FOR UPDATE` op de plaats: plaats vrij, bootsoort past, clubplaats hoort bij clubboot en omgekeerd, eigenaar is geen oud-lid, boot heeft nog geen plaats. Na toewijzen verdwijnt de boot van de wachtlijst.

Verwijderen van een rek, een plaats of een geschikte bootsoort met een toegewezen boot weigert de domeinlaag (BLB-001, BLB-002). Een rek verwijderen verwijdert alleen lege plaatsen.

## Alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Code in de URL, met een doorverwijzing van oude codes | Vraagt een tabel met oude codes; een oude code kan later aan een andere plaats worden gegeven, en dan wijst een oud kaartje naar de verkeerde plaats |
| Volgnummer (`id`) in de URL | Breekt niet bij hernoemen, maar maakt alle eigenaren in één lus op te halen |
| UUID in de URL | Werkt, maar geeft een dichtere, grotere QR-code; 10 tekens volstaan |
| Aparte tabel `toewijzing` met begin- en einddatum | Historie dubbel bijhouden naast het log; meer joins in elk overzicht |

## Gevolgen

- Hernoemen van een plaats raakt niets anders dan het veld `code` en een logregel. Kaartjes blijven werken; alleen de tekst op het kaartje is dan verouderd.
- Een bezoeker kan een plaats niet op code opzoeken. Wil apex dat toch (open vraag 3 in de architectuur), dan is het een kleine zoekfunctie die alleen exacte codes vindt.
- Een publieke sleutel opnieuw genereren is bewust geen functie. Is een sleutel ooit ongewenst bekend, dan is dat geen probleem: de pagina is openbaar.
- De openbare pagina gebruikt een eigen leesfunctie die alleen plaatscode, bootnaam, foto-URL en naam van de eigenaar (of de naam van de vereniging bij een clubboot) ophaalt. De E2E-test controleert het volledige antwoord op afwezigheid van adres, telefoon, e-mail en lidnummer.
- Foto's op de openbare pagina hebben een eigen willekeurige sleutel (ADR-008), zodat ze ook niet op te tellen zijn.
