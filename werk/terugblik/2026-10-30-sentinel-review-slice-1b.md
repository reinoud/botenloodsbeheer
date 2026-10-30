# Terugblik: review van slice 1b

Datum: 2026-10-30
Taak: review van de gestagede wijziging voor slice 1b (issue #8, met #3, #4 en #7) door Sentinel.

## Wat ging goed

De opdracht noemde de verwachte waarden en de leidende bron bij een botsing. Daardoor kon ik gericht toetsen op de grens van de helft, de grens van 5 jaar en de regels voor clubplaatsen. De stack draaide al, en de testcommando's stonden in de opdracht.

## Wat kon beter

Voor gelijktijdig toewijzen bestaat geen test. Ik heb de vergrendeling beoordeeld door de code te lezen: eerst de plaats, dan de boot, onder READ COMMITTED. Een test met twee verbindingen had dat bewijs sterker gemaakt.

## Wat deed ik zelf goed

Ik heb de unitsuite en de hele E2E-suite zelf gedraaid en niet alleen de uitkomst van de regie overgenomen. Daarnaast draaide ik twee E2E-tests los, ook `-k bezoeker` voor #4.

## Wat heb ik onderweg verbeterd

Eerst wilde ik een eigen test voor gelijktijdigheid schrijven. Ik heb gekeken naar de unieke constraint op `plaats.boot_id` en naar de volgorde van de locks. Op basis daarvan heb ik het als laag punt gemeld, in plaats van uren aan een harnas te besteden.

## Wat kan structureel beter

Zet in de opdracht: "Vraagt een domeinfunctie om `FOR UPDATE`, lever dan een test met twee sessies die de race laat zien, of noteer in het issue waarom die test ontbreekt."
