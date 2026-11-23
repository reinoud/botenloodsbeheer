# Terugblik Sentinel, tweede review #380 (herstel na toets Design System)

**Datum:** 2026-11-23
**Taak:** het herstel van #380 toetsen (uitlijning filter, `ds-field__hint`, `aria-describedby` via het script, statusveld, ADR-002 en backlog), unittest en E2E draaien.

## Wat ging goed

De opdracht noemde precies vijf punten, het testcommando en waar proeven mochten staan. Daardoor bleef de review klein. De E2E-selectie (7 geslaagd) en de unittest op een eigen database (33 geslaagd) liepen in één keer.

## Wat kon beter

Voor een schermafbeelding van een pagina met inlog bestaat geen kant-en-klaar hulpmiddel voor reviewers. Ik moest zelf een uitnodiging maken, inloggen met TOTP en daarna met `opruimen.sql` opruimen. Dat kostte drie stappen die bij elke visuele controle terugkomen.

## Wat deed ik zelf goed

Ik heb niet alleen gekeken, maar gemeten: de y-positie van het zoekveld en van Alleen soort, met en zonder script, op 1100 en 360 px, plus de berekende `align-items`. Zo is ook vastgesteld dat zonder script `end` blijft gelden. Het proefaccount heeft een naam die `opruimen.sql` herkent, en het is na afloop verwijderd.

## Wat heb ik onderweg zelf verbeterd

Ik wachtte met de meting tot `draai.sh` klaar was, ook met opruimen. Zo kwam mijn inlog niet boven op de limiet van Traefik en zat ik de integratiecontainer niet in de weg.

## Wat kan structureel beter

Zet in de opdracht: "Voor een visuele controle met inlog: maak een uitnodiging `e2e-<letters>-<stempel>` met `flask beheerder uitnodigen`, meet in de e2e-container met een script uit de scratchpad (`-v <scratchpad>:/proef:ro`), en ruim op met `opruimen.sql -v stempel=<stempel>`; start pas na afloop van `draai.sh`."
