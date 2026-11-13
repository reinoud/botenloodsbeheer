# Terugblik Sentinel, nareview issue #206 "Boot verplaatsen"

Datum: 2026-11-13. Taak: nareview van de herstelpunten na de eerste review (ruff, ADR-006, handleiding).

## Wat ging goed

De opdracht gaf de tree van de eerste review en het commando voor alleen het nieuwe deel. Daardoor was de toets klein: drie bestanden, ruff schoon, 36 geslaagd.

## Wat kon beter

De opdracht noemde de ruff-codes, maar niet waar F811 vandaan kwam. Een `# noqa: F811` op een testfunctie kan een dubbele testnaam verbergen, en dan draait een test stil niet. Dat moest ik zelf uitzoeken.

## Wat deed ik zelf goed

Ik controleerde dat F811 komt van de fixture `ingelogd` als parameter (import op regel 12) en dat geen testnaam dubbel voorkomt. Ook liep ik na dat de overzichten van (gaan) opzeggen op `plaats:<id>` filteren, zodat de handleiding daar klopt.

## Wat heb ik onderweg verbeterd

Ik draaide pytest met `-rs`, zodat overgeslagen tests zichtbaar zouden zijn. Er waren er geen.

## Wat kan structureel beter

Zet in de opdracht: "Staat er een `# noqa: F811` op een testfunctie, controleer dan met `grep -o '^def test_[a-z_0-9]*' <bestand> | sort | uniq -d` dat geen testnaam dubbel voorkomt."
