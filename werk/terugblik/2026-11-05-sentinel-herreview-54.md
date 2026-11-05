# Terugblik sentinel: herreview issue #54

**Datum:** 2026-11-05
**Taak:** herreview van de gestagede diff op `fix/54-proxyprotocol` (PROXY protocol, tweede ronde in `tests/proxy`)

## Wat ging goed

De drie herstelpunten uit de vorige review zijn goed doorgevoerd. Ruff is schoon. De controle met `drie` vangt een gedeelde teller op beide routes, en de mutant op `trustedips` faalt op vier controles met de verwachte meldingen. Het overlaypunt over een kopie uit de index maakte de mutanten snel en reproduceerbaar.

## Wat kon beter

De brief vroeg om een mutant die de teller deelt, maar noemde niet hoe. De opties (een label op `iprem`, een ander adres in `draai.sh`) moest ik zelf afwegen. Een fout in de opstart van de tweede container lag buiten de herstelpunten en kwam pas aan het licht door een stub.

## Wat deed ik zelf goed

Voor de gedeelde teller koos ik `sourcecriterion.requesthost=true` op `iprem`: dat raakt beide controles op een eigen teller in één run, zonder de testcode te wijzigen. Het foutpad van `intern_iprem` heb ik met een docker-stub geproefd in plaats van het af te leiden.

## Wat heb ik onderweg verbeterd

Mijn eerste stubproef faalde op een ongebonden variabele door `set -u`; ik heb de variabelen in de stub gezet. `sed -i ''` werkte niet (GNU-sed op deze host); ik ben overgestapt op python3, zoals de overlay voorschrijft.

## Wat kan structureel beter

Zet in de opdracht: "Een controle in `draai.sh` die een tweede container start, eist dat die container gestart is en met 0 eindigt; een lege uitkomst van `docker wait` telt als fout. Proef dat met een docker-stub waarin `run -d` faalt."
