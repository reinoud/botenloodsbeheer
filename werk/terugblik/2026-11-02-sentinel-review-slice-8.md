# Terugblik sentinel, review slice 8 (kaartjes met QR-code)

**Datum:** 2026-11-02
**Taak:** review van de gestagede diff van slice 8 (issue #46). Oordeel: akkoord.

## Wat ging goed

De brief noemde de norm per bron (issue, backlog, ADR's, overlay) en de verwachte maten uit ADR-011. Daardoor kon ik CSS en tests direct naast de getallen leggen. De mutantenlijst van forge had per mutant de diff en het commando; één mutant natrekken kostte één regel.

## Wat kon beter

Mijn eerste E2E-run met `draai.sh tests/e2e/test_kaartjes.py -k kaartjes` verzamelde 0 tests: de e2e-container draait in `tests/e2e`, dus een pad vanaf de root bestaat daar niet. Alleen `-k <testnaam>` werkt.

## Wat deed ik zelf goed

Naast de mutant van forge heb ik een eigen mutant gedraaid op het risico dat de brief noemde: een QR-code zonder `BASIS_URL` (relatieve link). De unittest ving die. Ik heb het toegangslog gecontroleerd op de querystring: `app/toegangslog.py` knipt die eraf, dus plaats- en rek-id's komen niet in het log.

## Wat heb ik onderweg zelf verbeterd

Na de lege run heb ik `draai.sh` gelezen in plaats van opnieuw te gokken, en de test met `-k test_kaartjes_kiezen` gedraaid: 1 geslaagd, 28 niet geselecteerd.

## Wat kan structureel beter

Zet in de opdracht: "Draai één E2E-test los met `tests/e2e/draai.sh -k <testnaam>`, zonder pad; de e2e-container werkt vanuit `tests/e2e`."
