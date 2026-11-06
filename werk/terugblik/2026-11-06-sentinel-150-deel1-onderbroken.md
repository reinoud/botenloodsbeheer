# Terugblik Sentinel, review issue #150 deel 1

**Datum:** 2026-11-06
**Taak:** review van de gestagede diff op `feature/150-dajaks-basis` (Dajaks-basis 0.3.0, kleuren weg, migratie 0015)

## Wat ging goed

De brief noemde per toetspunt het verwachte gedrag en de commando's, zodat elke controle direct te draaien was. De migratie en de nieuwe tests op de stylesheets en de kleurkiezers vingen elk hun mutant op een eigen assert.

## Wat kon beter

De brief vroeg om de conformiteitstest uit `basis/afname.py` of een test in botenloods. Botenloods heeft geen eigen test op het manifest, en `controleer_product.py` in designsystem keurt de afname af omdat `dj-components.css` in dezelfde map staat als de afname maar niet in het manifest. Dat had de bouw vooraf kunnen zien.

## Wat deed ik zelf goed

Ik heb de hashes in het manifest zelf nagerekend tegen de bestanden en tegen commit 609c915, naast de controle van designsystem. Zo is duidelijk dat de inhoud klopt en alleen de mapindeling afwijkt.

## Wat heb ik onderweg verbeterd

`controleer_product.py` draait niet met `python3 -I`, omdat het `afname` uit de eigen map importeert. Ik heb het zonder `-I` gedraaid; het is eigen code uit de designsystem-repo, geen gedownload bestand.

## Wat kan structureel beter

Zet in de opdracht: draai na een afname `python3 basis/controleer_product.py <repo> --doel app/web/static/ds --ref main` in designsystem en zet bestanden die niet uit de afname komen (zoals `dj-components.css`) buiten de doelmap van de afname.

Zet in de opdracht: een nieuwe macro of een gewijzigd sjabloon dat gebruikersinvoer toont, krijgt een unittest met een waarde als `<b>x</b>` die de geëscapete vorm toetst, en de mutant met `|safe` op dat veld moet falen.
