# Terugblik foundation: integratiecontainer en interne API

**Datum:** 2026-10-31
**Taak:** architectuur en ADR's bijwerken voor de besluiten van de stakeholder van 2026-10-31 (integratiecontainer, API standaard aan, logo uit de installatie)

## Wat ging goed

De brief noemde de leidende bron, de te raken ADR's, de code die verdwijnt en de oude termen om op te zoeken. Daardoor kon ik in één ronde lezen, ontwerpen en bijwerken. De code van slice 1 tot en met 3 liet precies zien wat er wegvalt (`app/ledenbron/`, de synchronisatie in `app/taken/`, `logo_vervangen`, de Nginx-locatie voor het logo).

## Wat kon beter

ADR-012 kwam in de eerste versie uit op 1007 woorden en moest in drie rondes terug naar 897. Ik had de contracttabel eerder als vast blok moeten tellen en de rest daaromheen schrijven. De overlay (§3 "koppelmodule", §6 "achtergrondwerk zoals de ledensynchronisatie") gebruikt nog oude termen; die heb ik niet aangepast, omdat de overlay bij de regie hoort.

## Wat deed je zelf goed

Ik koos een aparte dienst `api` met een eigen databaserol in plaats van de API in `web` te laten. Zo blijft de bestaande scheiding in de database (alleen één rol schrijft leden) staan en krijgt het internetgerichte `web` geen schrijfrecht op leden. De integratiecontainer loopt via een interne Nginx-server, zodat de rate limit en de vertrouwde `X-Forwarded-For` uit ADR-005 ongewijzigd gelden.

## Wat heb je onderweg zelf verbeterd

De statuspagina toonde "terugschrijven aan of uit", maar de applicatie weet dat niet meer. Ik heb het vervangen door wat de applicatie wel ziet: wanneer de bootaantallen voor het laatst zijn opgehaald en de laatste aanroep per robottoken. De reden bij een gemelde fout heb ik beperkt tot een vaste lijst, zodat geen tekst van buiten op de statuspagina komt.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Als een besluit van de stakeholder ook de overlay raakt, noemt foundation de regels in de overlay die verouderd zijn; de regie werkt ze bij." Zet in de opdracht: "Tel een nieuw ADR met `wc -w` vóór de eerste oplevering aan jezelf, en houd 10 procent marge onder het budget."
