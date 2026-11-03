# Terugblik Sentinel, review issue #60

Datum: 2026-11-03. Taak: review van de gestagede migratie 0010 (rechten van `botenloods_taken`), met suite en mutanten.

## Wat ging goed

De opdracht noemde de leidende bronnen, de code om te lezen, het mutantcommando van de bouwer en waar de downgrade mag draaien. Daardoor kon ik direct de domeincode naast de grants leggen en de mutanten draaien zonder de gedeelde database te raken. Suite, head en ruff waren in een paar minuten gecontroleerd.

## Wat kon beter

Ruff staat niet lokaal op het pad; ik vond pas bij de tweede poging dat het in de testcontainer draait. De bouwer meldde de positieve dekking als "opschonen, hartslag en seed blijven werken", maar de hartslag met een bestaande rij (UPDATE op `taakrun`) draait nergens als de worker. Dat bleek pas uit een mutant.

## Wat deed je zelf goed

Ik heb niet één maar drie mutanten gedraaid, één per soort recht dat de worker gebruikt (INSERT en UPDATE op `taakrun`, DELETE op `lid`). Zo kwam het gat bij UPDATE boven, dat een mutant op INSERT alleen niet had laten zien. Ik heb ook de vergrendelingen in de seedpaden nagelopen (`FOR UPDATE`, `FOR KEY SHARE`), omdat die UPDATE-recht vragen.

## Wat heb je onderweg zelf verbeterd

Ik heb de mutanten met een script uit de echte migratie afgeleid en gecontroleerd dat elke vervanging iets veranderde, in plaats van ze met de hand te schrijven.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bij een rechtenwijziging: draai per recht dat de rol houdt een mutant die alleen dat recht intrekt, en noem per mutant de test die valt. Een recht zonder vallende test is niet gedekt." Zet in de opdracht ook: "ruff draait in de testcontainer: `... run --rm test ruff check --no-cache .`".
