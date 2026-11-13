# Terugblik Sentinel, review #154 (zoeken vanuit de kop)

Datum: 2026-11-13. Taak: de gestagede diff van #154 reviewen, met unitsuite, mutantsteekproef en E2E-runs.

## Wat ging goed
- De brief noemde per toetspunt het commando, de leidende bron en wie draait. Ik hoefde niets na te vragen.
- De mutanten van de bouwer stonden per naam in een eigen map met `commando.txt`. Een diff tegen `git show :<pad>` per mutant was genoeg om te zien wat hij verandert.
- De unitsuite (1341 geslaagd) en de vier E2E-runs liepen zonder storing van andere agents.

## Wat kon beter
- `-k boot_vastleggen` selecteert niets: het is een hulpfunctie in `test_loods.py`, geen testnaam. Ik heb `-k test_loods` gedraaid (vijf tests die de hulpfunctie gebruiken).
- `-k zoeken` selecteert ook `test_lid_zoeken_en_plaatsen_van_opgezegde_leden` uit `test_overzichten.py`. Dat was hier nuttig, maar de brief noemde het niet.
- `commando.txt` gebruikt `-x`; daarmee zie je alleen de eerste falende assert. Ik heb zonder `-x` gedraaid om per mutant de assert van het criterium te vinden.

## Wat deed ik zelf goed
- De claim dat `sleutel-plaats-vak` gelijkwaardig is, heb ik niet overgenomen. Op een tijdelijke kopie van `plaats` in de devdatabase (in een transactie met ROLLBACK) kwam de volgorde zonder `Plaats.vak` door elkaar, en een proeftest met `ANALYZE` na de UPDATEs vangt de mutant. De productcode is goed; de test en zijn commentaar niet.

## Wat heb ik onderweg verbeterd
- Na de eerste mutantrun ben ik overgestapt op `--tb=line` met een filter op `^/app|^FAILED`, zodat elke falende assert als bestand:regel in één regel staat.

## Wat kan structureel beter in de opdracht of de afspraken
- Zet in de opdracht: noem bij `draai.sh -k` een deel van een testnaam dat met `grep -rn "def test_" tests/e2e` te vinden is; een hulpfunctie selecteert niets.
- Zet in de opdracht voor de bouwer: een mutant op een sorteersleutel die alleen overleeft omdat de planner een index kiest, is niet gelijkwaardig; draai `ANALYZE` op de tabellen in de test, zodat de planner sorteert zoals in productie.
