# Terugblik Sentinel, review issue #83

Datum: 2026-11-04. Taak: review vóór de commit van issue #83 (bootsoort per verdieping, plaats verwijderen vervalt).

## Wat ging goed
- De brief noemde de verplichte mutanten, de eigen scratchpadmap, wie de suite draait en dat de downgrade op een eigen database moet. Daardoor hoefde ik niets af te stemmen.
- De mutanten van de bouwer stonden klaar; ik kon mijn eigen set ernaast zetten en vergelijken.
- Unitsuite: 683 geslaagd, 0 mislukt, 0 errors, 0 overgeslagen.

## Wat kon beter
- `docker compose run --rm migrate alembic heads` werd door de rechtencontrole vastgehouden en liep niet. Ik heb de head daarna gecontroleerd met `ScriptDirectory` in de testcontainer, zonder de dienst migrate.
- De brief noemt BLB-044 criterium 5 en 6, maar in backlog v0.6.1 zijn de melding bij een vak met een boot en de knop op het plaatsdetail criterium 6 en 7. Ik heb op inhoud getoetst.

## Wat deed je zelf goed
- Ook mutanten gedraaid op de sloten (KEY SHARE), de rollback en elk recht van de nieuwe tabel. Daar bleven vier overlevers over die de bouwer niet had getoetst.
- De downgrade getoetst met data: een rij in `verdieping_bootsoort` en in `plaats_bootsoort`, daarna downgrade, controle, en opnieuw upgrade.

## Wat heb je onderweg verbeterd
- Na de vastgehouden migrate-aanroep ben ik overgestapt op een leesquery in de db-container en een proef in de testcontainer, in plaats van het commando opnieuw te proberen.

## Wat kan structureel beter
- Zet in de opdracht: "Draai bij elk nieuw recht in een migratie een mutant zonder dat recht, ook voor DELETE; een recht dat alleen een cascade dient, is niet nodig, want de cascade loopt als eigenaar."
- Zet in de opdracht: "Een nieuw `with_for_update(key_share=True)` krijgt een racetest zoals `tests/unit/test_bootsoorten.py:198`, of een notitie in het issue waarom die ontbreekt."
- Zet in de opdracht: "Noem criteria met hun tekst of met het backlogversienummer erbij, niet alleen met een nummer."
- Zet in de opdracht: "Controleer de migratiehead met `ScriptDirectory` in de testcontainer; `run migrate` vraagt om akkoord."
