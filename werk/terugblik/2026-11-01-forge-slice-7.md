# Terugblik forge, slice 7: wachtlijst per bootsoort

**Datum:** 2026-11-01
**Taak:** slice 7 bouwen (BLB-013, BLB-014, BLB-008 criterium 3, BLB-011 criterium 3, BLB-019 criterium 1, issue #27), issue #43

## Wat ging goed

De brief noemde de besluiten die vaststaan, ook de afgeleide (andere bootsoort, verwijderde boot). Daardoor hoefde ik niets te vragen voordat ik begon. De bestaande patronen (slot eerst op de boot, `race` uit `tests/unit/hulp.py`, `als_web` en `als_api`) waren direct bruikbaar. Drie mutanten (zonder slot, zonder toekomstcontrole, zonder opruimen bij de import) faalden allemaal tegen hun hele testbestand.

## Wat kon beter

De dienst `migrate` leest de migraties uit het image. Mijn eerste `alembic upgrade` meldde 0006 als head zonder fout. Pas na `up --build` zag de stack 0007. Ook vond ik pas laat dat `flask seed` als de worker draait, waardoor de worker rechten op `wachtlijst` nodig had. De eerste E2E-versie leunde op de volgorde van de gedeelde lijst; een eerdere, mislukte run stond er nog op. In de hele E2E-suite botsten plaatscodes: `test_loods.py` (#39) en `test_overzichten.py` gebruikten allebei `W{STEMPEL}`, en ik koos eerst dezelfde letter. Los slaagt elk bestand, in de suite niet.

## Wat deed ik zelf goed

Ik heb de race tussen erop zetten en een gelijktijdige import (lid wordt oud-lid) bewust niet met een extra databaserecht opgelost. De lijst verbergt boten van oud-leden en elke import ruimt alle oud-leden op, niet alleen nieuwe. Dat staat als `shortcut:` in `app/domein/wachtlijst.py`. De webrol heeft geen UPDATE op `wachtlijst`, zodat de database zelf afdwingt dat de aanmelddatum niet te wijzigen is.

## Wat heb ik onderweg verbeterd

Een hernoeming van `tokens._actor` naar `actor` overschaduwde een lokale variabele; ik heb hem `als_actor` genoemd. De E2E-test controleert de volgorde nu op de datums in de kolom, niet op de eerste rij. Een unittest die de webrol een lid liet wijzigen, gebruikt nu een monkeypatch op `leden.vandaag`.

## Wat kan structureel beter

- Zet in de opdracht: "Na een nieuwe migratie eerst `docker compose -f docker-compose.yml -f compose.dev.yml up --build -d --wait`; de dienst migrate leest de migraties uit het image."
- Zet in de opdracht: "`flask seed` draait als de worker (botenloods_taken); een nieuwe tabel die seed vult, krijgt rechten voor die rol."
- Zet in de opdracht: "Een nieuwe plaatscode in een E2E-test krijgt een letter die nog niet voorkomt; controleer met `grep -rn 'f\"[A-Z]{STEMPEL}\"' tests/e2e`."
- Zet in de opdracht: "Een E2E-test op een gedeelde lijst controleert de volgorde over de hele kolom, niet op de eerste rij; eerdere runs laten rijen achter."
