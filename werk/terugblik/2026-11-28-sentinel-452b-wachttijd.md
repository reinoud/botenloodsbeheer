# Terugblik sentinel, 2026-11-28

Taak: tweede review vóór commit van #452 (wachttijd van de integratie in UTC), na herstel van de commentaarregel en een extra test voor de overgang naar zomertijd.

## Wat ging goed

De brief noemde de mutant, het testcommando, de Python-versie en wat de eerste review al akkoord gaf. Daardoor bleef de review klein: de patchkopie vergelijken met `git diff --cached`, de regellengte tellen, de suite en de mutant draaien. Met de mutant vallen beide nieuwe tests en verder niets (2 gefaald, 71 geslaagd); de gestagede code geeft 73 geslaagd, 0 overgeslagen, ruff schoon.

## Wat kon beter

De regel uit de overlay noemt `awk 'length>100'`. Die telt op macOS bytes, dus een regel met "één" of "ë" lijkt langer dan hij is. Ik heb in tekens nageteld met Python. Verder staat in `integratie/koppeling/__init__.py:177`, vlak boven de diff, een commentaarregel van 124 tekens uit #440. Die valt buiten deze diff en blokkeert niet, maar de regel uit #440 is daar zelf niet gevolgd.

## Wat deed je zelf goed

Ik bouwde de mutant uit de gestagede boom (`git archive` van `git write-tree`) in een verse map in de scratchpad en mountte die als volume. De werkmap bleef ongewijzigd. Ik controleerde ook de andere plekken die `fout_op` lezen: de vergelijkingen met `OCHTEND` in de tests blijven kloppen, omdat datetimes met een tijdzone over zones heen gelijk vergelijken.

## Wat heb je onderweg zelf verbeterd

`sed -i ''` faalde, omdat `sed` op deze machine GNU-sed is. Ik ben overgestapt op een kort Python-script met een controle dat de vervangen tekst precies één keer voorkomt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Tel regellengte in tekens met `python3 -c` of `awk` in een UTF-8-locale, niet met de standaard-awk van macOS; die telt bytes." Zet in de opdracht ook: "Bewerk bestanden met python3; `sed` op deze machine is GNU-sed, dus `sed -i ''` werkt niet."
