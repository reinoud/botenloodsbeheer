# Terugblik Sentinel: review blok 3 deel B (#150)

Datum: 2026-11-08
Taak: review van de gestagede diff op `feature/150-blok3b` (detail Boot en Lid, 2B).

## Wat ging goed

De opdracht noemde het toetsingskader, de antwoorden van de toets van het designsystem en de mutantenmap. Daardoor kon ik gericht zoeken naar toestanden zonder test. De unitsuite (1040 geslaagd, 0 overgeslagen) en de E2E-tests van de wachtlijst (3 geslaagd) liepen zonder storing.

## Wat kon beter

`commando.txt` stond niet in de mutantenmap, alleen `lijst.txt`. Ik heb de commando's zelf opgebouwd uit de opdracht.

## Wat deed je zelf goed

Ik heb naast de mutanten van de bouwer eigen mutanten gemaakt voor de toestanden uit "Toets bouw deel B". De mutant op `verwijderen_in_taak` overleefde: een oud-lid met een boot op een plaats is niet getest. Ik heb ook de bestaande toestand uit #137 (oud-lid nog op de wachtlijst) naast het nieuwe sjabloon gelegd.

## Wat heb je onderweg zelf verbeterd

Ruff faalde op de cache in de container; met `--no-cache` liep het wel.

## Wat kan structureel beter

Zet in de opdracht: elk antwoord uit een toets van het designsystem krijgt een eigen unittest en een mutant, ook als er geen preview voor is.

Zet in de opdracht: controleer bij een nieuwe tak in een sjabloon welke bestaande toestanden uit eerdere issues (bijvoorbeeld #137) erdoor anders worden getoond.
