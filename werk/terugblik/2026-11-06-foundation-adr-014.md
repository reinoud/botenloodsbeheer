# Terugblik foundation, ADR-014

**Datum:** 2026-11-06
**Taak:** ADR-014 voor de CSV-import en -export van rekindeling (#157) en bezetting (#158)

## Wat ging goed

De issues waren scherp: besluiten, formaatvoorstel en open punten stonden apart. De code (`toewijzing`, `indeling`, `boten`, migraties) liet snel zien welke validatie en welke vergrendelvolgorde al bestaan, zodat de ADR vooral hergebruik voorschrijft.

## Wat kon beter

De opdracht noemde ADR-005 als web en CSRF, ADR-006 als rollen en rechten en ADR-007 als bewaartermijnen. In de repository is ADR-005 het tokenontwerp, ADR-006 mutatielog en opschonen, ADR-007 achtergrondtaken. Ik heb de bestanden zelf gekozen. De eerste versie telde 1947 woorden; inkorten tot 1496 kostte drie rondes.

## Wat deed ik zelf goed

Ik zag dat de bestaande domeinfuncties zelf committen en rollbacken, wat één transactie voor de import onmogelijk maakt, en schreef de kern zonder commit voor. Ik zag ook dat een bootsoortnaam `/` mag bevatten, wat botst met `/` als scheidingsteken, en dat het kader "imports in de integratiecontainer" uit overlay §6 en de intake schuurt met een upload in `web`.

## Wat heb ik onderweg verbeterd

Commentaar herkennen op de eerste cel na het inlezen in plaats van op het eerste teken van de regel, omdat Excel een cel met een puntkomma tussen aanhalingstekens zet. Een rondgang blijft neutraal doordat de import precies de `'` van de formulebescherming weghaalt.

## Wat kan structureel beter

Zet in de opdracht: noem een ADR bij nummer en bestandsnaam zoals `ls docs/architecture/adr/` die toont, niet bij een omschrijving uit het hoofd.
