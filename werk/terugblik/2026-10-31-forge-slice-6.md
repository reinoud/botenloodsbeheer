# Terugblik forge, slice 6

**Datum:** 2026-10-31
**Taak:** slice 6 bouwen: integratiecontainer, import van leden via `PUT /api/v1/leden`, beheerdocumentatie, overzicht van boten van leden die gaan opzeggen (BLB-039, 040, 041; BLB-006 tot en met 008; issue #21)

## Wat ging goed

De brief noemde de bronnen met hun voorrang, de images en de herhaalregels. Daardoor kon ik zonder vragen bouwen. ADR-012 gaf per aanroep argumenten en antwoord; het contract in `openapi.yaml` volgde daar direct uit. De E2E-run met de echte container en de stub vond binnen een minuut een fout die de unittests misten (zie hieronder).

## Wat kon beter

De unittests draaiden met `WTF_CSRF_ENABLED=False` voor elke dienst. Daardoor slaagde elke PUT in de tests, terwijl de echte API met 500 antwoordde: de blueprint was niet vrijgesteld van CSRF. Pas de proef met de draaiende stack liet het zien. Verder botste BLB-040 ("vijf aanroepen") met de slicetabel (bootaantallen in slice 9) en architectuur §6.2 (seed in `api`) met ADR-012 (alleen `api` schrijft leden, dus ook geen rek en boot). Dat kostte afwegingen die in de brief hadden kunnen staan.

## Wat deed ik zelf goed

Ik heb mutanten gedraaid op de vergrendeling, de grens van 2 MB en de CSRF-vrijstelling; alle drie laten een test falen. Ik heb de voorbeeldcode uit de beheerdocumentatie letterlijk uitgevoerd in de integratiecontainer tegen de stack, en met een socketproef vastgesteld dat de container `db` en `api` niet bereikt.

## Wat heb ik onderweg zelf verbeterd

De `app`-fixture zet CSRF nu aan voor tests met de markering `api`, zodat een ontbrekende vrijstelling in de suite faalt. Nginx houdt het verzoek van 2 MB in het geheugen (`client_body_buffer_size`), zodat er geen extra regel in de foutlog komt. De wachtlus in `draai.sh` gebruikt `grep` zonder `-q`, want met `pipefail` geeft `grep -q` een vals negatief door SIGPIPE.

## Wat kan structureel beter

Zet in de opdracht: "Draai na elke nieuwe schrijfroute in de API één aanroep via Nginx tegen de draaiende stack voordat je unittests als bewijs telt; de unittests zetten CSRF en de proxy niet altijd zoals productie."

Zet in de opdracht: "Noem bij een story die een aanroep uit een latere slice beschrijft (zoals BLB-040 en de bootaantallen) of die aanroep in deze slice gebouwd wordt."
