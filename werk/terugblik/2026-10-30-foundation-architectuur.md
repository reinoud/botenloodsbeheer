# Terugblik Foundation, architectuur en ADR's botenloodsbeheer

Datum: 2026-10-30. Taak: `docs/architecture/architectuur.md` en ADR-001 tot en met ADR-011 schrijven.

## Wat ging goed

De bronvolgorde en de vaste kaders stonden in de opdracht, dus de stack, de API-regels en de tenancy stonden niet ter discussie. De lijst met verplichte ADR's gaf direct de indeling. De backlog had zijn open vragen al besloten, waardoor ik bij de bewaartermijn en de tokens op concrete regels kon ontwerpen.

## Wat kon beter

De gevolgen van de bewaartermijn bleken pas tijdens het schrijven groter dan de intake laat zien: een opgeschoond oud-lid kan via de synchronisatie terugkomen, namen in het log overleven het lid, en back-ups houden alles langer vast. Die punten heb ik verwerkt, maar ze hadden in de business outline al als vraag kunnen staan. De architectuur kwam op 3243 woorden, dicht bij de bovengrens.

## Wat deed ik zelf goed

Ik heb de botsingen tussen intake en backlog benoemd in een tabel in plaats van ze stil op te lossen, vooral de schrijfcriteria in BLB-024 en BLB-034 tegenover de alleen-lezen-API. Besluiten die iets van beheerders of hosting vragen (passkeys, domeinnaam) staan bij de stakeholder. Elke ADR noemt de afgewezen alternatieven met reden.

## Wat heb ik onderweg zelf verbeterd

Ik heb het aantal tabellen tussen §4 en §5 gelijkgetrokken, een onjuiste zin over de TOTP-terugval in ADR-001 gecorrigeerd, en woorden en gedachtestreepjes met `wc -w` en `grep` gecontroleerd.

## Wat kan structureel beter in de opdracht of de afspraken

- Zet in de opdracht: "Loop bij elke bewaartermijn na wat er gebeurt met kopieën: logs, back-ups, de externe bron die opnieuw synchroniseert, en verwijzingen in andere tabellen."
- Zet in de opdracht: "Geef bij de omvang van een architectuurdocument ook een woordbudget per hoofdstuk, bijvoorbeeld datamodel 500, slices 300."
- Zet in de opdracht aan apex: "Toets elk acceptatiecriterium aan de besluiten in de intake; een criterium dat een besluit tegenspreekt, gaat terug als vraag."
