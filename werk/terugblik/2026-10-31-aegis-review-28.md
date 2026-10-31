# Terugblik Aegis, securityreview issue #28

Datum: 2026-10-31
Taak: securityreview van de gestagede diff voor issue #28 (verzoek van een beheerder na een fout).

## Wat ging goed

De opdracht noemde de drie toetspunten (stroom geweigerde aanroepen, rate limit, log) en de omvang. Daardoor kon ik gericht lezen: de diff, de API-decorator `aanroep` en de afhandeling van het verzoek in `app/domein/leden.py`.

## Wat kon beter

Of een open verzoek na een fout openblijft, staat niet in de diff. Ik moest de API lezen om te zien dat alleen `import-mislukt` en de veiligheidsgrens het verzoek sluiten, en een 5xx of 422 niet.

## Wat deed je zelf goed

Ik heb nagelopen welke statuscodes de API in het log zet (alleen weigeringen van `tokens.controleer`), zodat het oordeel over de logstroom op code rust en niet op aanname.

## Wat heb je onderweg zelf verbeterd

Eerst dacht ik dat een kapotte bron elke minuut een mislukte import zou opleveren. De API sluit het verzoek bij `import-mislukt`, dus die herhaling ontstaat niet. Dat punt heb ik laten vallen.

## Wat kan structureel beter

Zet in de opdracht: noem bij een wijziging in de herhaallogica van de container welke API-uitkomsten een open importverzoek sluiten en welke het openlaten.
