# Terugblik Sentinel bij de review van de testissues #153, #149, #161 en #209

Datum: 2026-11-15. Taak: review van de gestagede tests in branch `fix/tests-153-149-161-209`.

## Wat ging goed

- De brief noemde per issue de mutant, de uitvoer van de bouwer en het aantal herstarts van `web`. Daardoor kon ik elke bewering van de bouwer gericht nalopen.
- Het script `draai-mutant.sh` en de overrides van de bouwer maakten duidelijk hoe een mutant in `web` komt. Ik kon dezelfde aanpak volgen zonder te zoeken.
- De stack was schoon: geen lopende `draai.sh`, en `web` draaide de gestagede code.

## Wat kon beter

- Mijn eerste mutant voor #153 verving met `str.replace` twee regels in plaats van één (`app/domein/indeling.py:337` en `:409`). De `grep -c` in de container toonde `2` en verraadde dat. Ik heb de mutant opnieuw gemaakt met een assert op precies één treffer.
- De brief vroeg of #209 de herkomst van elke statuscode toetst, maar zei niet hoe je dat bewijst. Mijn gecombineerde mutant (label en weglezen weg) liet zien dat de applicatie op een kale kop helemaal niet antwoordt. Het deel `"location" not in koppen` in `tests/e2e/test_uploadgrens.py:79` is daarmee in de praktijk niet te raken.

## Wat deed je zelf goed

- Naast de mutant van de bouwer op `kaartjes()` heb ik een tweede sorteersleutel gemuteerd: `order_by=Bootsoort.naam` in `app/models.py:207`. Ook die valt op `tests/unit/test_kaartjes.py`.
- Bij #161 heb ik de 30 errors herleid tot de sessiefixture `database` (`tests/unit/conftest.py:59`, `command.upgrade(..., "head")`), over 18 tests. Alleen de eigen test faalt op een assert.
- Na elke mutant in `web` heb ik met `grep -c` en `docker inspect` op de labels gecontroleerd dat de mutant actief was en daarna weer weg.

## Wat heb je onderweg verbeterd

- Na de dubbele vervanging gebruik ik bij elke mutant een assert op `s.count(o) == 1`, en geen gewone `replace` meer.
- Voor de vraag naar de herkomst van de 413 heb ik een extra gecombineerde mutant gedraaid in plaats van op de docstring te vertrouwen.

## Wat kan structureel beter in de opdracht

- Zet in de opdracht: "Een mutant via `str.replace` heeft een assert op precies één treffer (`s.count(o) == 1`), en de `grep -c` in de container moet `1` tonen."
- Zet in de opdracht: "Vraag je om de herkomst van een statuscode, noem dan de mutant die het andere antwoord oplevert (zoals label en weglezen samen weg), en zeg of de reviewer die mag draaien met een extra herstart van `web`."
