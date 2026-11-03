# Terugblik sentinel, review issue #66

Datum: 2026-11-03
Taak: review van de gestagede diff voor issue #66 (JPEG-commentaar in de openbare foto), mutant en unitsuite draaien.

## Wat ging goed

De opdracht noemde de diff, het issue, de norm en het mutantcommando. De mutant (`git show HEAD:app/domein/afbeeldingen.py` als bind mount) faalde op de nieuwe assert in `tests/unit/test_indeling_en_toewijzing.py:141`. De suite gaf 550 passed en 1 failed (#64), zonder errors en zonder overgeslagen tests.

## Wat kon beter

De overlay (§4, regel 91) vraagt een bronbestand met EXIF, tekstblokken en ICC. De fototest heeft geen ICC in de bron, en het issue vroeg dat ook niet. Dat heb ik met een losse proef afgedekt; de test zelf dekt het nog niet.

## Wat deed ik zelf goed

Ik heb naast de mutant een losse proef gedraaid met bronnen in JPEG, PNG en WebP, elk met EXIF, ICC en XMP of PNG-tekstblokken, voor foto en logo. Er lekte niets. De mutant controleerde ik met `cmp` en `diff` tegen de werkmap.

## Wat heb ik onderweg zelf verbeterd

Ik heb de proef breder gemaakt dan het issue (XMP, iTXt, WebP), omdat Pillow per formaat andere metadata terugschrijft.

## Wat kan structureel beter

Zet in de opdracht: controleer of het acceptatiecriterium van een metadata-issue alle drie de soorten uit overlay §4 noemt (EXIF, tekstblokken, ICC); zo niet, vul het criterium aan vóór de bouw.
