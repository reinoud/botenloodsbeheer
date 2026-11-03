# Terugblik Aegis: securityreview restpunten

Datum: 2026-11-03
Taak: securityreview van de gestagede diff voor #59, #61, #62, #67, #68, #69 en #72.

## Wat ging goed

De issues hadden heldere acceptatiecriteria en de stack draaide met de gestagede code (volume op `./app`). Daardoor kon ik 404, 405, 400 en de grens van 2147483647 direct via de proxy en het koppelnet nalopen, zonder de suite te draaien.

## Wat kon beter

De opdracht noemde de cooldown naast `exclude-newer`, maar niet dat `exclude-newer` een vaste datum is die de regie met de hand ophoogt. Dat moest ik uit `pyproject.toml` en de overlay halen. Het is precies het punt waarop de review afkeurt.

## Wat deed ik zelf goed

Ik heb niet alleen de diff gelezen, maar ook de invoer erachter: de JSON-import van leden (`_tekst` laat een NUL-teken door) en de integers in querystring en formulier. Die vallen buiten de criteria van #67 en heb ik als restpunt gemeld, niet als blokkade.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik de dubbele build in de workflow zwaar wegen. Na nalezen is het verschil tussen het gescande en het gepushte image klein (zelfde builder, zelfde cache), dus ik heb het als laag gemeld.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Noem bij een supply-chainwijziging hoe `exclude-newer` wordt bijgehouden (vaste datum of relatieve duur) en of Dependabot daarbinnen nog voorstellen kan doen."
