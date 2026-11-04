# Terugblik sentinel: review slice 12 (issue #80)

**Datum:** 2026-11-04
**Taak:** review van de gestagede diff van slice 12, met migratiecontrole, mutanten en één E2E-test.

## Wat ging goed

De brief noemde de leidende bron (opmerking van 2026-11-03 18:29), de verwachte grenzen, de rechten van de migratie en het nachtvenster van #45. Daardoor kon ik direct toetsen. De migratiecontrole met `compare_metadata` op een eigen database liet in één run zien dat model en migratie gelijk zijn, en dat rechten, kolommen en checks na upgrade, downgrade en tweede upgrade kloppen.

## Wat kon beter

De mutant zonder `populate_existing` overleefde al bij bedrock, maar dat stond niet als open punt in de oplevering. De racetest houdt de geladen plaats niet vast, zodat de identity map hem opruimt en de test niets toetst. Ook zijn de schermafbeeldingen gemaakt met de ongestagede `compose.dev.yml`, waardoor het echte logo uit `huisstijl/` in een openbare repository terechtkomt. Niemand had dat gemeld.

## Wat deed ik zelf goed

Ik nam de mutantuitkomst van bedrock niet over, draaide zelf twaalf mutanten en zocht bij de overlevende met een probe uit waarom die bleef leven. Ik vergeleek een oude schermafbeelding uit `HEAD` met de nieuwe en zag zo het andere logo.

## Wat heb ik onderweg verbeterd

Ik heb de probe met een vastgehouden verwijzing tegen de gestagede code en tegen de mutant gedraaid, zodat de bouwer een bewezen herstel van één regel krijgt. De E2E-test draaide ik met de omweg voor #45, omdat het 01:44 was.

## Wat kan structureel beter

Zet in de opdracht: een racetest die verouderde attributen toetst, houdt het eerst geladen object vast in een variabele buiten de actie; anders ruimt de identity map het op en overleeft de mutant zonder `populate_existing`.
Zet in de opdracht: schermafbeeldingen voor `documentatie/` gebruiken het testlogo (`tests/fixtures/logo.png`), ook als `compose.dev.yml` lokaal anders staat; de reviewer vergelijkt één afbeelding met de versie in `HEAD`.
