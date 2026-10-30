# Terugblik Sentinel: review herstelpunten slice 1b (#9)

Datum: 2026-10-30
Taak: review van de gestagede diff voor issue #9, met testrun en controle op migratiehead en downgrade.

## Wat ging goed
De opdracht noemde per acceptatiecriterium de verwachte uitkomst en hoe de stack start. Daardoor kon ik elk punt direct afvinken. De suite (128) en de E2E (6) slaagden zonder overgeslagen tests.

## Wat kon beter
Voor de downgradecontrole stond niet in de opdracht welke dienst de eigenaarsrol heeft. Ik vond zelf dat de dienst `migrate` dat is.

## Wat deed ik zelf goed
Ik heb de test voor gelijktijdig toewijzen met een mutant gecontroleerd: zonder `with_for_update` faalt de test. Ook heb ik na de upgrade de rechten van de webrol en de nieuwe index in de database bekeken, in plaats van alleen op `alembic current` te vertrouwen.

## Wat heb ik onderweg verbeterd
Mijn eerste mutant-plugin importeerde de app te vroeg. Ik heb de import naar de fixture verplaatst, zodat de plugin laadt voordat pytest de app kent.

## Wat kan structureel beter
Zet in de opdracht: "Downgrade en upgrade gaan via `docker compose -f docker-compose.yml -f compose.dev.yml run --rm migrate alembic ...`; controleer daarna de rechten in de database."
