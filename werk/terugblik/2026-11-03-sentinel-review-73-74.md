# Terugblik sentinel, review #73 en #74

Datum: 2026-11-03. Taak: review vóór commit van de gestagede diff voor #73 (control socket van Gunicorn) en #74 (NUL-teken in de JSON-import, te groot getal in querystring en formulier).

## Wat ging goed

De brief noemde de bewuste keuze bij #74 met de bron (BLB-006 criterium 4, integratiecontainer.md:76). Daardoor kon ik die keuze direct toetsen en hoefde ik de afwijking van het issuecriterium (422) niet als fout te melden. De mutanten van de regie stonden klaar met `commando.txt`.

## Wat kon beter

De twee mutanten van de regie haalden de controle centraal weg. Dat bewijst de grens, maar niet dat elke aanroep `getal` gebruikt. Pas met een mutant per aanroep bleek dat drie aanroepen die de database bereiken geen test hebben.

## Wat deed ik zelf goed

Per aanroep een mutant gemaakt (12 stuks) en de overlevers met een losse proef in de scratchpad getoetst op een echte 500, zodat ik gelijkwaardige mutanten (kaartjes, intrekken, dagen) kon scheiden van echte gaten. In de log van web en api de ERROR-regels uitgezocht in plaats van alleen te tellen.

## Wat heb ik onderweg verbeterd

De eerste telling gaf zes ERROR-regels. Die kwamen van een herlaadactie om 16:24 tijdens het bewerken (ImportError op een half bewerkt bestand) en een herstart van de container. Ik heb de log vanaf de herstart apart geteld (0) en de opstart van 16:21 na `up --build` nagelopen (geen regel over de control server).

## Wat kan structureel beter

Zet in de opdracht: "Vervang je een aanroep op meer plekken door een gedeelde functie, draai dan per aanroep een mutant die de oude aanroep terugzet, en noem per aanroep de test die valt of waarom de mutant gelijkwaardig is."
Zet in de opdracht: "Bewerk geen Python-bestanden in de werkmap terwijl web en api met `--reload` draaien vlak voor een logcontrole; noem het tijdstip van de laatste `up --build` in de brief."
