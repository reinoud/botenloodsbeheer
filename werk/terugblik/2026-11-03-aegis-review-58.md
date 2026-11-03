# Terugblik aegis, securityreview issue #58

Datum: 2026-11-03. Taak: securityreview van de gestagede diff voor issue #58 (Pillow 13.0.0, `formats` bij `Image.open`, pytest 9.0.3 in e2e).

## Wat ging goed
De opdracht noemde precies wat ik moest toetsen en wat ik niet mocht aanraken (suite, `draai.sh`, `botenloods-dast`). Daardoor kon ik in een losse container werken zonder Sentinel te storen.

## Wat kon beter
De lokale `.venv` start niet op de host (abort). Ik moest Pillow 13.0.0 in een container installeren om het gedrag te proberen. Dat kostte een image-pull.

## Wat deed je zelf goed
Ik heb de 55 hashes in `uv.lock` één voor één tegen PyPI vergeleken met een script, en het gedrag van `formats` met negen formaten geprobeerd, in plaats van op de test in de diff te vertrouwen. Ook de grens op pixels en het strippen van exif heb ik met Pillow 13 nagelopen.

## Wat heb je onderweg zelf verbeterd
Ik controleerde ook of er tussen 16 en 20 oktober een nieuwere Pillow 13 uitkwam die door de ruimere datum mee zou kunnen komen. Die is er niet.

## Wat kan structureel beter
Zet in de opdracht: "Geef een `exclude-newer-package`-uitzondering een einddatum in het commentaar en verwijder hem zodra `exclude-newer` die datum passeert."
