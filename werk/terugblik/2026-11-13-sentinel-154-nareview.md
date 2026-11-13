# Terugblik Sentinel, nareview #154 (zoeken vanuit de kop)

Datum: 2026-11-13
Taak: nareview van de gestagede testwijziging na `357224e` (drie testbestanden).

## Wat ging goed

De opdracht gaf per toetspunt het commando, de mutant als exacte tekstvervanging en de verwachte falende assert. Daardoor waren mutant, controle en E2E in een paar losse runs klaar. De stack draaide al en niemand anders gebruikte hem.

## Wat kon beter

De opdracht noemde `tests/unit/test_zoeken.py:157` als falende regel; de assert staat op regel 158. Het ging wel om dezelfde assert, dus het oordeel verandert niet.

## Wat deed ik zelf goed

Naast de mutant draaide ik een controlerun: dezelfde mutant tegen de testversie uit `HEAD` (zonder `ANALYZE`). Die slaagde, dus de mutant overleefde daar. Zo is aangetoond dat juist de twee `ANALYZE`-regels de mutant doden, en niet iets anders in de staging. De mutantrun heb ik herhaald om te zien of de uitkomst stabiel is.

## Wat heb ik onderweg zelf verbeterd

Ik heb het regelnummer uit de opdracht niet overgenomen, maar gecontroleerd met `grep -n` voordat ik het in het oordeel zette.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Noem bij een verwachte falende assert de testnaam en de assert-tekst; het regelnummer alleen als controle." Een regelnummer verschuift bij elke kleine wijziging in de staging.

Zet in de opdracht: "Laat bij een test die een mutant pas doodt door een extra stap (zoals `ANALYZE`) ook een controlerun zonder die stap draaien." Dan blijkt dat de stap het werk doet.
