# Terugblik forge: herstelpunten slice 1b (issue #9)

**Datum:** 2026-10-30
**Taak:** de acht lage reviewpunten uit issue #9 oplossen, met migratie 0003.

## Wat ging goed

Het issue had per punt een bestand, een regel en een acceptatiecriterium. Daardoor kon ik zonder vragen beginnen. De unitsuite en de E2E-suite draaiden direct tegen de bestaande stack.

## Wat kon beter

Punt 1 raakte meer dan het issue liet zien. De unittests draaien als webrol en maakten leden direct aan; na de rechtenwijziging zouden ze allemaal falen. Punt 7 botste met de seed, die boten voor oud-leden via `boot_aanmaken` maakte. Beide stonden niet in het issue. Ook stond in architectuur §6.2 stap 1 dat `LEDENBRON=stub` standaard aanstaat; dat klopt na punt 3 niet meer, buiten de twee regels die de opdracht noemde.

## Wat deed ik zelf goed

De race-test heb ik bewezen: zonder `with_for_update` op de plaats faalt hij. De dubbele plaatscode controleert nu alleen de database. Dat weghalen van de controle in Python maakt het pad dat een gelijktijdige aanvraag neemt, het gewone pad, en dat dekt de bestaande test.

## Wat heb ik onderweg verbeterd

De tests kregen een marker `worker`: zulke tests draaien als `botenloods_taken`. De hulpfunctie `lid()` schrijft via de taakrol. Zo toetsen de tests de echte rechten, in plaats van dat de webrol meer mag om de tests te laten slagen.

## Wat kan structureel beter

Zet in de opdracht: "Wijzig je databaserechten, zoek dan eerst welke tests en seedcode als die rol schrijven, en noem in je antwoord welke tests je daarvoor hebt aangepast."
Zet in de opdracht: "`sed` in deze omgeving is GNU sed; gebruik python3 voor tekstwijzigingen."
