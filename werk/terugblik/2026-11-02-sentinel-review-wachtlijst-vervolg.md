# Terugblik Sentinel: review wachtlijst vervolg (slice 7, issue #43)

Datum: 2026-11-02. Taak: review van de gestagede diff na de review van slice 7 (andere eigenaar, racetest `eraf_halen`, clubplaats, lege datum, `vandaag()` in de overzichtentest).

## Wat ging goed

De opdracht noemde de leidende bronnen, de vijf punten en de map met mutanten. De mutanten van de bouwer waren volledige kopieën, zodat ik ze met `diff` kon lezen en direct als bind mount kon draaien. Alle vijf faalden op de bedoelde test. De review viel om 00:35, in het venster waarin de overzichtentest eerder faalde; de suite slaagde nu, dus punt 5 is ook in de praktijk getoetst.

## Wat kon beter

De bouwer leverde geen commando bij de mutanten, alleen de bestanden; ik moest het pad in de container afleiden uit de bestandsnaam. De racehelper draait de actie in een verse sessie, waardoor `populate_existing` in `eraf_halen` niet getoetst wordt (mijn eigen mutant overleefde).

## Wat deed ik zelf goed

Ik heb mutanten tegen het hele testbestand gedraaid, met `cmp` gecontroleerd dat de werkmap niet veranderde, en twee eigen mutanten toegevoegd: de volgorde van `_eraf` en de toewijzing van het nieuwe lid (gedood) en `populate_existing` in `eraf_halen` (overleeft, verklaard).

## Wat heb ik onderweg verbeterd

Ik heb eerst het importverzoek gedaan en daarna pas `draai.sh` gestart, zodat de nachtelijke fout van issue #45 de E2E-uitkomst niet vertroebelde.

## Wat kan structureel beter

Zet in de opdracht: lever bij elke mutant het doelpad in de container en het volledige `docker compose ... run --rm -v` commando in een `commando.txt` naast de mutanten.

Zet in de opdracht: een racetest via `race()` toetst `populate_existing` niet, omdat de actie in een verse sessie draait; laad het object in de actie eerst zonder slot als `populate_existing` getoetst moet worden.
