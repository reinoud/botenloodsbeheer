# Terugblik Sentinel, review issue #142

Datum: 2026-11-06. Taak: review vóór commit van het opruimen na de E2E-run (draai.sh, conftest.py, opruimen.sql).

## Wat ging goed
De opdracht noemde diff, issue, bewijsbestanden en de grenzen (geen nieuwe run zonder reden). Daardoor was de review in drie stappen klaar.

## Wat kon beter
De opdracht zei niet of de bootsoorten van test_bootsoorten.py in de volledige run zaten. "0 bootsoorten" moest ik zelf verklaren uit de test en de database.

## Wat deed ik zelf goed
Ik controleerde de restanten in de dev-database zelf (rekken, boten, bootsoorten, foto's) in plaats van alleen het bewijs van de regie te volgen, en las de verwijzingen in app/models.py na voor de cascades.

## Wat heb ik onderweg zelf verbeterd
Ik liet een nieuwe E2E-run achterwege: de database en het bewijs gaven genoeg uitsluitsel.

## Wat kan structureel beter in de opdracht of de afspraken
Zet in de opdracht: noem bij een telling met de waarde 0 in het bewijs of die 0 verwacht is, en waarom.
