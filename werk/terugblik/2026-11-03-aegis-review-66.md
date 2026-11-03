# Terugblik Aegis, securityreview issue #66

Datum: 2026-11-03. Taak: securityreview van de gestagede diff voor #66 (JPEG-commentaar in de openbare foto).

## Wat ging goed

De opdracht noemde diff, issue, bron, norm, Pillow-versie en scratchpad. Daardoor kon ik direct in de container toetsen, zonder zoekwerk.

## Wat kon beter

De vraag naar MPO stond in de opdracht als metadatavraag. In de praktijk wijst `verwerk` een MPO-bron af, omdat `img.format` dan `MPO` is. Dat is geen lek, wel een vraag over bruikbaarheid die buiten #66 valt.

## Wat deed ik zelf goed

Eerst een positieve controle gedraaid: zonder `comment=b""` staat het commentaar wel in de uitvoer. Daarmee is aangetoond dat de toets het lek kan zien, en dat de schone uitkomst niet toevallig is.

## Wat heb ik onderweg verbeterd

Naast tekst ook de JPEG-segmenten en PNG-chunks van de uitvoer opgesomd. Zo telt alleen wat er staat, ook metadata zonder herkenbare tekst.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij elke bronsoort die je laat toetsen ook het verwachte gedrag (opslaan of afwijzen), zodat een afwijzing niet als lek of als geslaagde toets wordt gelezen."
