# Terugblik Aegis, securityreview herstel issue #28

Datum: 2026-10-31
Taak: securityreview van de gestagede diff voor issue #28 (verzoek van een beheerder wacht het uur na een fout niet af).

## Wat ging goed
De opdracht noemde de toetspunten (stroom van PUT's, rate limit, log, lus bij 409). Daardoor kon ik gericht de paden in `app/domein/leden.py` en `app/api/__init__.py` nalopen.

## Wat kon beter
De opdracht zei niet of een geslaagde GET in het log van de API komt. Dat moest ik zelf in `app/api/__init__.py` opzoeken.

## Wat deed je zelf goed
Ik heb elk foutpad gekoppeld aan de vraag of het open verzoek gesloten wordt. Een 409 door `ImportLoopt` sluit het verzoek niet; dat heb ik als laag restpunt benoemd.

## Wat heb je onderweg zelf verbeterd
Ik heb eerst aangenomen dat elke 409 het verzoek sluit. Dat klopt alleen voor `Veiligheidsgrens`; ik heb het oordeel bijgesteld.

## Wat kan structureel beter
Zet in de opdracht: noem bij een review van herhaalgedrag welke aanroepen de API in het log schrijft (geslaagd, geweigerd of allebei).
