# Terugblik Aegis, review issue #60

Datum: 2026-11-03. Taak: securityreview van de gestagede diff voor issue #60 (rechten van `botenloods_taken`, migratie 0010).

## Wat ging goed

De gedeelde database stond al op 0010, dus ik kon de rechten na de migratie direct lezen in `pg_class.relacl`, `pg_default_acl`, `pg_auth_members` en de eigenaar van elke relatie. De uitkomst kwam precies overeen met de tabel in ADR-007.

## Wat kon beter

Mijn eerste groeperingsquery faalde door een aggregaat in de GROUP BY. Eén blik op `relacl` per relatie was meteen genoeg geweest en toont tabellen en reeksen in één keer.

## Wat deed je zelf goed

Ik keek verder dan de tabelrechten: defaultrechten, rollidmaatschap, eigenaarschap, kolomrechten, schema- en databaserechten en rolattributen. Het restrecht op `bootsoort` heb ik tegen de code gelegd (`app/domein/boten.py:46`) en niet alleen tegen de uitleg van de bouwer.

## Wat heb je onderweg zelf verbeterd

Ik controleerde ook of `flask seed` geen tabel aanraakt waarvan de reeks nu dicht is (`afbeelding`, `bootsoort`, `lid`). Zo'n tabel zou de seed breken zonder dat het in de review opviel.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Meld of de gedeelde database al op de nieuwe migratie staat; dan toetst de reviewer de rechten op de live ACL en niet alleen op de migratiecode."
