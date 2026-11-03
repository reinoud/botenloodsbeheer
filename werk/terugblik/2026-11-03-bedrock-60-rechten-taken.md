# Terugblik Bedrock, issue #60 (rechten botenloods_taken)

Datum: 2026-11-03. Taak: schrijfrechten van `botenloods_taken` beperken (migratie 0010).

## Wat ging goed

De opdracht noemde de bronnen en de volgorde (eerst zoeken wat de rol schrijft, dan revoke). De overlay-regel over seed als worker was beslissend. De migratie met één dictionary is in beide richtingen uit dezelfde data opgebouwd, zodat upgrade en downgrade niet uit elkaar kunnen lopen.

## Wat kon beter

Ik zag pas na de eerste testrun dat `test_opschonen` een foto als worker aanmaakte. Een grep op `foto=` en `png()` in worker-tests had dat vooraf gevonden. Mijn eerste rechtenquery op `pg_class` faalde door de volgorde van evaluatie; `pg_sequences` was meteen goed geweest.

## Wat deed je zelf goed

Ik heb de rechten per tabel uit de domeincode afgeleid, niet uit de lijst in het issue, en daarbij `FOR KEY SHARE` herkend: dat vraagt UPDATE op `bootsoort`. Ik heb de downgrade op een eigen database getoetst met een vergelijking van de rechtenverzameling (tabellen en reeksen), niet alleen op uitvoeren zonder fout.

## Wat heb je onderweg zelf verbeterd

De testhulp voor de foto in `tests/unit/test_opschonen.py` gebruikt nu de eigenaar, zodat de test de rechten van de worker niet nodig maakt. De reeksquery in de test is vervangen door `pg_sequences`.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bij een rechtenwijziging: grep alle tests met de marker `worker` (of `api`) op setup die de domeinlaag gebruikt voor tabellen die de rol straks niet meer mag schrijven, zoals `foto=` of `png()`, en noem ze vooraf." Zet in de overlay: "`FOR UPDATE` en `FOR KEY SHARE` vragen UPDATE-recht; tel dat mee bij het bepalen van de rechten van een rol."
