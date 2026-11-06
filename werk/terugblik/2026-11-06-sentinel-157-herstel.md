# Terugblik sentinel, herreview issue #157 (lege cel bootsoorten, stuurtekens)

Datum: 2026-11-06. Taak: review van de gestagede diff voor issue #157 na het herstel van de lege cel `bootsoorten` en de stuurtekens in `_naam` en `_omschrijving`.

## Wat ging goed

De brief noemde het besluit van de regie letterlijk, wat al gepland is en dat de suites niet gedraaid worden. Daardoor kon ik gericht op het herstel toetsen. Het herstel zelf is klein en precies: een lege cel geeft een lege lijst, `/`, `Kajak/` en `/Kajak` blijven een fout, en de bezette plaats valt via `controleer_plaats` af. De tests dekken de rondgang met een lege plaats en de bezette plaats.

## Wat kon beter

Het besluit zei "zoals op het scherm". Op het scherm weigert `plaats_wijzigen` een plaats zonder bootsoort ("Kies minstens één bootsoort"). De import mag een vrije plaats met bootsoorten nu leegmaken, en een test legt dat vast. Die premisse had vóór het herstel tegen de bestaande regel getoetst kunnen worden.

## Wat deed ik zelf goed

Ik heb de bewering "zoals op het scherm" nagelopen in `_soorten` en in de bestaande tests, en niet op het woord van de brief aangenomen. De parser heb ik met een puur script (zonder database) in de web-container nagelopen voor negen celvarianten, zonder de gedeelde testdatabase te raken.

## Wat heb ik onderweg verbeterd

Eerst zocht ik een lokale `.venv`; de overlay zegt dat losse controles in de container draaien. Ik ben daarop overgestapt en heb het script via stdin gegeven, zodat er niets in de werkmap kwam.

## Wat kan structureel beter

Zet in de opdracht: wie een besluit motiveert met "zoals op het scherm", noemt de functie en de test van die schermregel, en het agent toetst het herstel daartegen vóór de bouw.
