# Terugblik sentinel, review #243

**Datum:** 2026-11-12
**Taak:** review vóór de commit van issue #243, robottoken weigert een whitelistreeks breder dan /8 of /32 (branch `fix/243-whitelist-robot`)

## Wat ging goed

De brief noemde de verwachte falende ids per mutant en het exacte runcommando met de mount. Daardoor kon ik de mutanten in één lus draaien en de uitkomst direct naast de verwachting leggen. Baseline 107 geslaagd, 0 overgeslagen; mutanten `<=`, controle weg en IPv6-grens 8 vallen zoals verwacht.

## Wat kon beter

De mutant `<` naar `<=` viel ook in de schermtest op het geval `10.0.0.0/8, 2001:db8::/32-True`. Dat stond niet in de brief. Het is winst, geen fout, maar een verwachting die onvolledig is, laat een reviewer twijfelen of hij iets anders draait.

## Wat deed ik zelf goed

Ik draaide een vierde mutant die de brief niet noemde: `soort == "robot"` weg uit de nieuwe controle. Die overleeft. Geen test maakt een persoonlijk token met een brede reeks, terwijl de testcommentaar zegt dat een persoonlijk token die mag houden.

## Wat heb ik onderweg verbeterd

De mutanten maak ik met een script dat per vervanging controleert dat de bron precies één keer voorkomt en dat de mutant echt verschilt. Zo telt een vervanging die niets vervangt niet stil als overlevende.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "Noem bij een controle die alleen voor één soort geldt ook de mutant die de soortvoorwaarde weghaalt, met de test die daarop valt."
