# Terugblik Sentinel, review #262 (menu in vier groepen, pagina Import/export)

Datum: 2026-11-12 tot 2026-11-13. Taak: review van de gestagede diff voor #262, met de volle E2E- en unitsuite.

## Wat ging goed

De diff was klein en volgde het issue en BV-76 precies. Elke redirect naar Import/export had al een test, op één na in de unitsuite (annuleren), en die zat in de E2E. De codereview was binnen een kwartier klaar.

## Wat kon beter

De volle E2E-run duurde ruim 15 uur. De Mac lag met dichte klep op batterij en viel steeds in slaap. Twee tests faalden daardoor op "Je inlog is ouder dan 10 minuten": de klok sprong door de slaap heen. Los herhaald slaagden ze.

## Wat deed ik zelf goed

Ik heb de oorzaak van de twee fouten uit de aria-snapshot en `pmset -g log` gehaald, voordat ik ze als omgevingsfout aanmerkte, en ze daarna los herhaald. Ik heb de regie halverwege gemeld dat de run vertraagd was.

## Wat heb ik onderweg verbeterd

Mijn eerste wachtlus gebruikte `pgrep -f "tests/e2e/draai.sh"`, en die vond zichzelf: de lus eindigde nooit en hield de andere lussen vast. Daarna heb ik `pgrep -f "[d]raai.sh"` gebruikt.

## Wat kan structureel beter

Zet in de opdracht: "Controleer vóór een E2E-run met `ioreg -r -k AppleClamshellState -d 1` en `pmset -g batt` of de Mac open ligt of aan netstroom hangt; zo niet, meld dat eerst aan de regie in plaats van de run te starten."

Zet in de opdracht: "Wacht op een proces met `pgrep -f '[d]raai.sh'`, niet met het letterlijke pad, anders vindt de wachtlus zichzelf."
