# Terugblik foundation: ADR-013 Traefik vervangt Nginx

**Datum:** 2026-10-31
**Taak:** ADR-013 schrijven (issue #29), ADR's en architectuur bijwerken waar ze Nginx noemen.

## Wat ging goed

De opdracht noemde de bronnen met voorrang, de Nginx-bestanden en de raakvlakissues. Daardoor was elke controle in één ronde terug te vinden en kreeg ze een plek en een proef.

## Wat kon beter

De aanname "een extern netwerk" liet open of dat het gedeelde netwerk van Traefik is. In de gebruikelijke vorm zou dat `api:8000` voor elke dienst op de host openzetten. Ik heb gekozen voor netwerken van de installatie waar Traefik op aansluit, maar dat had een regel in de opdracht kunnen zijn.

## Wat deed ik zelf goed

Ik heb de tag van Traefik op Docker Hub nagekeken in plaats van uit het hoofd te kiezen, en de eigenschappen waarvan ik niet zeker ben (toegangslog per router, gezonde containers) als Probable gemarkeerd met een proef.

## Wat heb ik onderweg zelf verbeterd

De eerste versie van ADR-013 telde 1214 woorden; ik heb hem met `wc -w` teruggebracht naar 1170. Een vervangscript stopte op een lege vervanging zonder te schrijven; ik heb het opnieuw gedraaid en daarna met `grep` nagekeken dat geen Nginx-verwijzing buiten de wijzigingslogs over is.

## Wat kan structureel beter

Zet in de opdracht: "Gaat een proxy of netwerk gedeeld worden met andere diensten, zeg dan of `web` en `api` op het gedeelde netwerk mogen; standaard niet."
