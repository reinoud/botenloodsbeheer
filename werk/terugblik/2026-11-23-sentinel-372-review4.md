# Terugblik sentinel, vierde review #372

**Datum:** 2026-11-23
**Taak:** systematische proef op het aantal keren dat de bron wordt opgehaald, en de volledige unitsuite, vóór de commit van #372.

## Wat ging goed

De proef (`scratchpad/sentinel-372d/proef.py`) draait buiten Docker op een kopie van de gestagede module en van de module uit `HEAD`. Alle 1554 patronen van lengte 1 tot en met 4, maal drie verzoekstanden, kostten 17 seconden per versie. Daardoor kon ik oud en nieuw naast elkaar leggen en zien welke overschrijdingen nieuw zijn. De suite gaf 1796 geslaagd, 0 gefaald en 0 overgeslagen.

## Wat kon beter

De opdracht zei "met open verzoek" zonder te zeggen wanneer het verzoek dichtgaat. Ik heb drie standen gemodelleerd: geen verzoek, een verzoek dat de API sluit zoals in `app/domein/leden.py` (na een geslaagde PUT, na `import-mislukt` en na de 409 van de veiligheidsgrens), en een verzoek dat altijd open staat. Die laatste stand betekent dat een beheerder elke minuut opnieuw aanvraagt. Alleen in die stand gaat de telling boven de 6, en ook de oude code komt daar tot 60 per uur. Die stand had ik vooraf als bovengrens moeten benoemen, zodat de telling meteen te duiden was.

## Wat deed ik zelf goed

Ik heb de nieuwe overschrijdingen apart gezet van de overschrijdingen die er al waren. Zo blijkt dat #372 geen nieuw automatisch patroon toevoegt: elke nieuwe overschrijding vraagt een verzoek dat na een bronfout of 409 meteen weer openstaat.

## Wat heb ik onderweg verbeterd

De eerste telling rekende ook geslaagde imports mee. Ik heb de maat aangepast naar het aantal mislukte ophalingen in een venster van 60 minuten sinds de laatste geslaagde import, zoals de eis vraagt.

## Wat kan structureel beter

Zet in de opdracht: "Bij een proef met een open verzoek: het verzoek sluit zoals de API het sluit; een verzoek dat een beheerder telkens opnieuw opent, is een aparte bovengrens en vergelijk die met de code uit HEAD."
