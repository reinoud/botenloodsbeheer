# Terugblik Sentinel, review #32 en #40

**Datum:** 2026-11-03
**Taak:** review van de gestagede diff voor #32 (ruff ISC004) en #40 (draai.sh stopt bij mislukte tokenaanmaak). Oordeel: niet akkoord.

## Wat ging goed

De opdracht noemde precies de plekken waar `set -e` kon falen: binnen `$(...)` in een arraytoewijzing en in `e2e()`. Daardoor kon ik gericht proeven, zonder de gedeelde stack aan te raken.

## Wat kon beter

De proef van de regie toetste `robot` los, niet in de contexten waarin het script de functie aanroept. Juist daar zitten de twee gaten: een arraytoewijzing met meer dan één `$(...)` en een functie die met `|| status=1` wordt aangeroepen.

## Wat deed je zelf goed

Ik heb elke context nagebootst met een stub in de scratchpad, in de bash van macOS (3.2) en in bash 5.3, en het gedrag aangetoond in plaats van beredeneerd.

## Wat heb je onderweg zelf verbeterd

Eerst ging ik ervan uit dat een arraytoewijzing net als `x=$(false)` stopt. De proef liet zien dat alleen de laatste `$(...)` telt; dat heb ik als bevinding opgenomen.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Proef een foutpad in bash in elke aanroepcontext uit het script (arraytoewijzing met meerdere `$(...)`, functie achter `||` of in `if`), niet alleen de functie los."
