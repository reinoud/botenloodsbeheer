# Terugblik aegis: review rijbeleid op taakrun (issue #24)

**Datum:** 2026-11-05
**Taak:** securityreview van migratie 0014, de test en ADR-012 v1.7.0 vóór de commit

## Wat ging goed

De brief noemde de rollen, de code per rol en de migraties met de rechten. Daardoor kon ik de live ACL, de policies, de rolattributen, foreign keys, triggers en functies in één leesronde toetsen. De gedeelde database stond al op 0014, zoals gemeld.

## Wat kon beter

De brief vroeg om een toets van `RETURNING` en het wijzigen van de taaknaam, maar liet alleen leesquery's toe. Die gedragingen heb ik uit de semantiek van PostgreSQL afgeleid en niet met een proef bevestigd. Een eigen wegwerpdatabase voor schrijfproeven had dat opgelost.

## Wat deed je zelf goed

Ik heb de rijen in de live tabel nagelopen en zag een taak `ledensynchronisatie` die geen code meer schrijft. Het beleid verbergt die voor de API; dat is juist, en het laat zien dat de lijst in het beleid met de constanten in de code mee moet.

## Wat heb je onderweg verbeterd

Ik heb het risico van `LOCK TABLE` (de API heeft UPDATE) meegenomen, dat niet in de brief stond. Dat geeft geen vervalsing: de statuspagina blokkeert of toont een oude hartslag, dus een fout.

## Wat kan structureel beter

Zet in de opdracht: wil je dat de reviewer een schrijfgedrag van een rijbeleid of recht bevestigt (wijzigen van de sleutelkolom, `RETURNING`), geef dan een eigen database via `nieuwe_database` vrij voor proeven met `ROLLBACK`, of zeg dat afleiden uit de documentatie volstaat.
