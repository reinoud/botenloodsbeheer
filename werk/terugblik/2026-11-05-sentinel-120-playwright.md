# Terugblik Sentinel, review issue #120 (Playwright 1.64.1)

Datum: 2026-11-05. Taak: review vóór de commit van branch `fix/120-playwright-1.64`.

## Wat ging goed

De brief noemde per punt het bewijs dat nodig was, de compose-bestanden en het pad van de log van de regie. Alle vijf punten waren met losse commando's te toetsen, zonder de werkmap te raken.

## Wat kon beter

De brief noemde `test_openbare` als voorbeeld, maar die test bestaat niet. Ik koos `test_inloggen.py -k test_passkey`. Het pad van de log van de regie lag in `scratchpad/e2e/`, niet in `sentinel-120/`; dat kostte één extra aanroep.

## Wat deed ik zelf goed

Ik heb naast `pip list` ook de browserrevisies in `browsers.json` van het pakket vergeleken met `/ms-playwright` in het image (chromium 1248, firefox 1555, webkit 2370). Dat is het echte risico uit het issue, niet alleen het versienummer. De digest heb ik tegen het register gecontroleerd met `imagetools inspect`. De optelling van de log van de regie (13 bestanden, 38 geslaagd) heb ik nagerekend.

## Wat heb ik onderweg zelf verbeterd

`gh issue list --search "1.55"` gaf niets terug, terwijl #120 zelf `1.55` noemt. Ik heb daarom alle open issues opgehaald en lokaal gefilterd met `jq`.

## Wat kan structureel beter

Zet in de opdracht: noem als voorbeeldtest een naam die `grep -n "def test_" tests/e2e/` oplevert, en zoek in issues met `gh issue list --json title,body --jq` in plaats van `--search`, omdat de zoekfunctie van GitHub versienummers met een punt niet betrouwbaar vindt.
