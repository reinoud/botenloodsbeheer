# Terugblik sentinel, review #374

**Datum:** 2026-11-23
**Taak:** review vóór de commit van `tests/e2e/draai.sh` (terugzetten van het tokenbestand na een run op de dev-stack)

## Wat ging goed

De brief noemde de foutroutes, de mode van de kopie en de release-E2E in een eigen project als toetspunten. Daardoor kon ik gericht proeven. Het bewijs van de bouwer (hash vóór en na, log van `integratie`) stond op één plek.

## Wat kon beter

Het bewijs liet niet zien of het teruggezette token ook ná `opruimen.sql` werkt: de import na de herstart viel vóór het opruimen. Een leesquery op `token.laatst_gebruikt_op` gaf dat bewijs wel (gebruikt om 09:59Z, ruim na het opruimen van 09:36Z).

Mijn eerste proefcommando bevatte `rm -f` en werd door de hook Blast Radius tegengehouden, met tien minuten wachttijd.

## Wat deed ik zelf goed

Ik proefde `opruimen()` uit de index met een stub in zes scenario's, ook een faalpad dat de bouwer niet had: het terugzetten zelf mislukt. Daar breekt `set -e` het opruimen af en blijft de kopie met het token in `$TMPDIR` staan.

## Wat heb ik onderweg zelf verbeterd

Na de geblokkeerde opdracht heb ik alles zonder `rm` gedaan en de proef in een eigen script gezet. Een tweede scenario (`exit 0` vóór de kopie) maakte het verschil zichtbaar tussen `rc` en een eventuele fout van `rm -f ""`.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Gebruik in proefcommando's geen `rm`; de hook Blast Radius houdt die tien minuten vast. Laat tijdelijke bestanden in de scratchpad staan."

Zet in de opdracht: "Bewijs voor 'ook na het opruimen' bij een token: een leesquery op `naam` en `laatst_gebruikt_op` in `token` met een tijdstip na het opruimen, niet alleen de import direct na de herstart."
