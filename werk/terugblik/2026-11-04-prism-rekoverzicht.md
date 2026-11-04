# Terugblik prism, Rekoverzicht (issue #87)

Datum: 2026-11-04. Taak: pagina Rekoverzicht met plaatjes per plaats bouwen, testen en documenteren.

## Wat ging goed
- De brief gaf de besluiten, de stand van de stack en de testcommando's. Ik hoefde niets te zoeken of te vragen.
- Alle zeven mutanten op `plaatje()` en de mutant op het menu-item vielen op een eigen assert. Eén e2e-mutant (klasse voor de gestippelde rand weg) viel op het aantal `a.rek-vak-club`.

## Wat kon beter
- De brief zei niet dat `plaats.bootsoorten` op id staat gesorteerd. "Eerste soort" is dus de laagste id, niet de volgorde van aanvinken. Mijn eerste test ging daarvan uit en faalde.
- `plaats()` uit `tests/unit/hulp.py` weigert een lege soortenlijst. Een plaats zonder bootsoort ontstaat alleen via `rek_aanmaken`. Dat zocht ik uit.

## Wat deed je zelf goed
- Geen inline style: de CSP laat alleen `style-src 'self'` toe, dus vaste CSS-klassen met 12 kolommen.
- Gebruikersdocumentatie en twee ADR's (002, 006) in dezelfde ronde bijgewerkt, na zoeken op de menutekst en het logoverzicht.

## Wat heb je onderweg verbeterd
- Het voorbeeldrek op de schermafbeelding: eerst rek A (alleen clubplaatsen), daarna rek F met bezette en vrije ledenplaatsen. Het script is aangepast en opnieuw gedraaid.
- `rek-wijzigen.png` is teruggezet met `git checkout`: het scherm veranderde niet.

## Wat kan structureel beter
- Rekken in de seed zijn zuiver: A is helemaal clubplaats, de rest helemaal niet. Een schermafbeelding met beide kan alleen met een eigen rek in het script.

## Regel voor de volgende opdracht
- Zet in de opdracht: "Bij een nieuwe webroute noem je het menu-item, de handleidingtabel van routes (`test_handleiding_noemt_elke_webroute`) en de e2e-uitnodigingssoort in `tests/e2e/draai.sh` als vaste afwerklijst."
