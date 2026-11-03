# Terugblik sentinel: review slice 9

**Datum:** 2026-11-03
**Taak:** review van de gestagede diff van slice 9 (issue #48), met unit- en E2E-suite, mutanten en migratie 0008

## Wat ging goed

De brief gaf de verwachte drempels, de omweg voor issue #45 en de plek van de mutanten. Daardoor kon ik direct toetsen tegen een norm. De draaiende containers bevatten dezelfde code als de gestagede diff (gecontroleerd met `cmp`). Unit 467 geslaagd, E2E 33 geslaagd, migratie 0008 heeft één head en een werkende downgrade.

## Wat kon beter

Mutant `m9_token_32_dagen` van de bouwer bevatte twee wijzigingen: 32 dagen en het weglaten van het filter op verlopen tokens. De eerste werd gevangen, de tweede niet. Zo leek het filter getest terwijl dat niet zo was.

## Wat deed ik zelf goed

Ik heb elke mutant eerst met `diff` tegen de gestagede versie vergeleken. Zo zag ik de dubbele wijziging in m9. Mijn eigen mutant op dat filter overleefde en liet een gat zien in een expliciet criterium (BLB-037 criterium 5, "al verlopen").

## Wat heb ik onderweg verbeterd

De E2E-run viel tussen 00:00 en 03:00. Ik heb de omweg uit de brief gebruikt, ook voor de losse test met `-k`, en aegis vooraf gemeld.

## Wat kan structureel beter

Zet in de opdracht: "Elke mutant bevat precies één wijziging; controleer dat met `diff` tegen de gestagede versie voordat je hem in `lijst.txt` zet."

Zet in de opdracht: "Heeft een criterium een uitsluiting (zoals 'ingetrokken of al verlopen'), dan krijgt elke uitsluiting een eigen geval in de test."
