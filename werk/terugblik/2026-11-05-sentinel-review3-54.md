# Terugblik sentinel, derde review issue #54

**Datum:** 2026-11-05
**Taak:** herreview van het herstel in `tests/proxy/draai.sh` (`intern_iprem`) en de seinmap met `chmod 1777`, plus een eigen run van `draai.sh`.

## Wat ging goed

De brief noemde het afgekeurde punt, het herstel en de stubproef van de vorige reviewer. Daardoor kon ik de proef direct op een kopie uit de index overdoen, zonder het gat zelf te zoeken.

## Wat kon beter

De stubproef van de vorige ronde dekte alleen het geval "container start niet". Of een exitcode anders dan 0 van de seincontainer ook als fout telt, moest ik er zelf bij maken.

## Wat deed je zelf goed

Ik heb de stub ook tegen de oude conditie gedraaid: die telde de fout als geslaagd. Zo is aangetoond dat de stub het gat echt raakt en dat het herstel het dicht.

## Wat heb je onderweg verbeterd

Ik heb vier varianten toegevoegd (exitcode 0, 1 en 137 van de seincontainer, en een falende eerste client). Drie daarvan falen, zoals verwacht.

## Wat kan structureel beter

Zet in de opdracht: "Lever bij een herstel van een controle een stub mee die zowel de oude als de nieuwe conditie draait, met per geval de verwachte uitkomst."
