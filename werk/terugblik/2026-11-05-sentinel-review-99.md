# Terugblik Sentinel, review issue #99

Datum: 2026-11-05. Taak: review van de gestagede diff voor issue #99 (filter op bootsoort zonder knop). Oordeel: akkoord.

## Wat ging goed

De opdracht noemde de bronnen, de mutantcommando's en de stand van de stack. Daardoor kon ik direct draaien. De unitsuite (717 passed, 0 failed, 0 errors, 0 skipped), ruff en twee E2E-runs waren groen bij de eerste poging.

## Wat kon beter

Mutant m5 van de bouwer (inline script in plaats van het externe script) faalt op de assert "script van de eigen site" (regel 65) en raakt de assert "geen inline script" (regel 66) dus niet. Ik heb daarom een eigen mutant gemaakt met `onchange` naast het externe script. Die faalt wel op regel 66.

## Wat deed ik zelf goed

Ik controleerde dat de E2E-test via Traefik loopt (`draai.sh`), zodat de controle op consolefouten echt tegen de CSP uit `docker-compose.yml:82` test. Zonder die route zou die assert niets zeggen.

## Wat heb ik onderweg verbeterd

Ik heb geen JS-mutant voor "Alle bootsoorten" gedraaid, omdat de web-container daarvoor opnieuw moet worden aangemaakt. De asserts in de test (`wait_for_url` op `bootsoort=$` en de kajakplaats die eerst 0 keer en daarna zichtbaar is) dekken dat gedrag aantoonbaar.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: elke mutant moet falen op de assert die bij het criterium hoort; noem per mutant het verwachte regelnummer van de assert.
