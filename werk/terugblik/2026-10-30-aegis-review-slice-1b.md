# Terugblik Aegis: securityreview slice 1b

Datum: 2026-10-30
Taak: securityreview van de gestagede diff voor issue #8 (met #3 en #7).

## Wat ging goed

De opdracht noemde de verwachte waarden als getallen (10 MB, 40 miljoen pixels, sleutellengtes, veldlengtes). Daardoor kon ik elke waarde direct naast de code leggen. De draaiende stack maakte het mogelijk om de headers van `/p/<sleutel>` en `/afbeelding/<sleutel>`, de grants op `lid` en het weghalen van EXIF echt te controleren in plaats van alleen te lezen.

## Wat kon beter

De lokale `.venv` crashte bij het starten van Python, dus de metadatatest liep in de webcontainer. Dat werkte, maar de opdracht zei niet welke Python-omgeving bedoeld was voor losse controles.

## Wat deed ik zelf goed

Ik heb eerst een positieve controle gedaan voordat ik iets als geblokkeerd telde: een echte openbare pagina met eigenaar en foto, en een echte afbeelding. De POST-routes zonder CSRF-token gaven 400. Dat is de CSRF-laag, die vóór de inlogcontrole draait; de decorator staat aantoonbaar op elke beheerroute.

## Wat heb ik onderweg verbeterd

Ik controleerde of het productie-image de stubfixtures bevat, nadat ik zag dat `.env.example` `LEDENBRON=stub` zet. Het image bevat ze niet, dus de bevinding bleef bij een opmerking en werd geen datalekrisico.

## Wat kan structureel beter

Zet in de opdracht: "Losse controles in Python draai je met `docker compose exec -T web python -c ...`; de lokale `.venv` is daar niet voor."
