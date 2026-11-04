# Terugblik sentinel, review issue #81

Datum: 2026-11-04. Taak: review van de nieuwe test op de volgorde rek, verdieping, vak.

## Wat ging goed
De mutanten waren klaar en elk week op één regel af van de werkmap. Daardoor kostte het controleren weinig tijd.

## Wat kon beter
Het acceptatiecriterium noemt twee mutanten. Een mutant die vak weglaat of Rek.volgorde weglaat, blijft leven. Dat valt buiten het criterium, maar het criterium zegt dat niet.

## Wat deed ik zelf goed
Suite, ruff en vier mutanten in één run, en zelf twee extra mutanten beredeneerd.

## Wat heb ik onderweg verbeterd
Ik filterde de pytest-uitvoer op de regel "At index", zodat per mutant de falende plek direct zichtbaar is.

## Wat kan structureel beter
Zet in de opdracht: noem bij een volgordetest elke sorteersleutel en zeg per sleutel of een mutant die hem weglaat moet vallen.
