# Terugblik Sentinel, review issue #95 (tekstballon met aanduiding)

Datum: 2026-11-05. Taak: review van de gestagede diff voor issue #95.

## Wat ging goed
De diff is klein en raakt precies de plek uit het issue. De tests dekken alle vijf standen en de escaping.

## Wat kon beter
Niets wezenlijks. De mutant met `|safe` vraagt een kopie van `app`, omdat de werkmap niet gewijzigd mag worden.

## Wat deed ik zelf goed
De mutant gedraaid met een kopie van `app` in de scratchpad, gemount over `/app/app`; de werkmap bleef onaangeroerd.

## Wat heb ik onderweg verbeterd
Geen eigen testbestand nodig: de bestaande compose-dienst `test` met een extra volume volstond.

## Wat kan structureel beter
Zet in de opdracht: "Draai een templatemutant met `docker compose ... run --rm -v <scratchpad>/app:/app/app:ro test pytest <bestand>`."
