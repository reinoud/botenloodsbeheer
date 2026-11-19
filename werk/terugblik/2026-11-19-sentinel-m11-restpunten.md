# Terugblik Sentinel, review restpunten milestone 11

Datum: 2026-11-19
Taak: review vóór commit van #346, #342, #291 en #333

## Wat ging goed

De opdracht noemde per issue de werkmap, het testbestand, de mutanten die de regie al had gedraaid en het runcommando. Daardoor kon ik gericht steekproeven nemen en hoefde ik de volledige suite niet te draaien. De vier testbestanden slaagden na elkaar: 24, 19, 10 en 50 tests, geen overgeslagen.

## Wat kon beter

De patches stonden in de scratchpad, maar de issueteksten moest ik apart ophalen. Een regel met de acceptatiecriteria per issue in de opdracht had een stap gescheeld.

## Wat deed ik zelf goed

Ik heb de regex van #291 los getoetst op zes schrijfwijzen in plaats van te redeneren. Zo werd duidelijk welke schrijfwijzen luid falen (spatie vóór het sluithaakje, `?#iefix`, `url(#id)`) en welke stil wegvallen (`URL(` in hoofdletters).

## Wat heb ik onderweg zelf verbeterd

Een inline Python-regel met drie soorten aanhalingstekens brak in bash. Ik heb het script als bestand in de scratchpad gezet en met `python3 -I` gedraaid.

## Wat kan structureel beter

Zet in de opdracht: "Plak per issue de acceptatiecriteria letterlijk onder de diff, zodat de reviewer `gh issue view` niet hoeft te draaien."
