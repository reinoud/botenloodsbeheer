# Terugblik aegis, securityreview issue #83

**Datum:** 2026-11-04
**Taak:** securityreview van de gestagede diff voor issue #83 (route plaats verwijderen weg, bootsoort per verdieping bij "Nieuw rek", migratie 0012).

## Wat ging goed

De brief noemde de leidende ADR, de vijf focuspunten en het verwachte gedrag per invoer (afwijzen of stil negeren). Daardoor kon ik elk punt direct tegen een norm toetsen. De gedeelde database stond al op 0012, dus de live ACL was met één leesquery te controleren.

## Wat kon beter

De brief zei niet of het recht DELETE voor `botenloods_web` nodig is of alleen uit de ADR komt. Ik moest zelf vaststellen dat de cascade met de rechten van de tabeleigenaar draait.

## Wat deed ik zelf goed

Ik heb de bewering "cascade draait als eigenaar" niet uit het hoofd aangenomen, maar een bestaande test gevonden die precies dat bewijst (`tests/unit/test_persoonlijke_tokens.py`, `test_verwijderen_neemt_persoonlijke_tokens_mee_als_web`). Ik heb geen suite gedraaid en niets in de gedeelde database geschreven.

## Wat heb ik onderweg verbeterd

Ik heb ook gecontroleerd of `flask seed` (rol `botenloods_taken`) nog werkt nu `rek_aanmaken` altijd een `FOR KEY SHARE` op `bootsoort` doet: die rol houdt UPDATE op `bootsoort` sinds 0010, dus dat breekt niet.

## Wat kan structureel beter

Zet in de opdracht: "Geeft een migratie een rol een recht op een nieuwe tabel, noem dan per recht de code die het gebruikt; een recht dat alleen via een cascade nodig lijkt, is niet nodig, want de cascade draait als eigenaar van de tabel."
