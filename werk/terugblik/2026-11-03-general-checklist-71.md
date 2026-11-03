# Terugblik: briefingchecklist opschonen (#71)

**Datum:** 2026-11-03
**Taak:** briefingchecklist in `docs/PROJECT-OVERLAY.md` §4 groeperen en samenvoegen, overlay v0.4.0.

## Wat ging goed

De opdracht noemde de groepen, de grens (geen inhoud weg, niet afzwakken) en het verliesscript. Daardoor was er geen twijfel over wat samenvoegen mocht. Het script vond na de eerste versie geen ontbrekend token of getal.

## Wat kon beter

De winst in woorden is klein: 3416 naar 3352. De meeste regels waren al kort en uniek; samenvoegen spaart alleen een herhaald onderwerp. Een grotere inkorting vraagt herschrijven, en dat stond de opdracht niet toe. De groep "documentatie" kreeg ook de regels over backlog, criteria en ADR's, omdat de opdracht geen groep voor ontwerp noemde.

## Wat deed ik zelf goed

Eerst het verliesscript geschreven en pas daarna de tekst, zodat elke trimronde direct te controleren was. Issue #45 opgezocht om zeker te zijn dat "het issue daarover" en #45 hetzelfde issue zijn voordat ik de twee regels samenvoegde.

## Wat heb ik onderweg zelf verbeterd

Na de eerste telling (3374) nog drie herhalingen geschrapt die door het samenvoegen naast elkaar kwamen te staan, zoals de dubbele zin over uitzonderingen in de ADR en in het criterium, en de dubbele zin over het nachtvenster van de E2E-run.

## Wat kan structureel beter

Zet in de opdracht: "Mag een regel korter geformuleerd worden zonder inhoud te verliezen, of alleen samengevoegd? Noem het doel in woorden (bijvoorbeeld 25 procent korter)." En: "Noem een groep voor ontwerpregels (apex, foundation) als die regels niet onder documentatie horen."
