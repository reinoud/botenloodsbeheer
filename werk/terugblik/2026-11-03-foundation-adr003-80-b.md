# Terugblik: ADR-003 bijwerken na nieuwe besluiten in issue #80

**Datum:** 2026-11-03
**Taak:** ADR-003 v2.1.0 en architectuur v0.6.0 bijwerken (vak 1 tot en met 12 met gaten, omschrijving van het rek, seed uit CSV)

## Wat ging goed

De opdracht noemde de leidende bron, de volgorde van gezag en de oude termen om op te zoeken. Daardoor kon ik in één ronde alle plekken vinden, ook "160 pagina's", "vier velden" en de downgradeformule `* 6`.

## Wat kon beter

De opdracht noemde niet dat `app/models.py` en migratie `0011` (nog niet gecommit) al de oude grens van 6 vakken bevatten. Dat vond ik zelf; het is nu een ontwerppunt voor de bouw.

## Wat deed ik zelf goed

Ik heb de grenzen uit de data gemeten met een script (omschrijving 52 tekens, vak 12, 27 clubplaatsen) en gecontroleerd dat de worker al INSERT op `bootsoort` heeft, zodat de seed Wildwaterkano zonder nieuwe rechten kan toevoegen.

## Wat heb ik onderweg zelf verbeterd

De zin "het aantal verdiepingen is de hoogste verdieping" klopte niet meer met gaten; die heb ik bij een tweede zoekronde gevonden en herschreven.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Noem welke ongecommitte bestanden (models, migraties) de oude besluiten al bevatten, zodat het agent die als ontwerppunt voor de bouw kan melden."
