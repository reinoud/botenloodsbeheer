# Terugblik apex: backlog bijwerken na ADR-012

Datum: 2026-10-31. Taak: backlog v0.2.1 naar v0.3.0 voor de besluiten van 2026-10-31, ADR-012 en architectuur §7.1.

## Wat ging goed

De bronnen waren compleet en de voorrang was helder. ADR-012 gaf per aanroep argumenten en terugkeerwaarden, zodat elk criterium een toetsbaar antwoord kreeg (409, 413, 422, 403, 429). Architectuur §10.1 noemde de botsingen al, en issue #11 en #13 lieten zien welke criteria eerder waren verschoven.

## Wat kon beter

Tijdens het werk besloot de stakeholder over architectuurvraag 5 en 6 (intake en architectuur v0.3.1, nog niet gecommit). De opdracht zei "markeer als wacht op besluit vraag 5". Ik zag het besluit pas bij een `git diff` aan het eind en moest de markering, de slicetabel en de nummers van de open vragen opnieuw bijwerken. De opdracht noemde ook "BLB-034 criterium 2" voor de geweigerde schrijfaanroep; in de backlog was dat criterium 3. Ik heb het criterium op inhoud gekozen.

## Wat deed ik zelf goed

Ik koos nieuwe vraagnummers (11 tot en met 19) die niet botsen met de vragen 1 tot en met 10 in de backlog, en verwijs naar de architectuurvragen met "architectuur §10.2". Elke nieuwe story heb ik met een script geteld (hoogste 232 woorden), en de prioriteiten ook (42 stories: 34 Must, 7 Should, 1 Could).

## Wat heb ik onderweg zelf verbeterd

Ik zag dat BLB-026 criterium 1 het besluit van 2026-10-30 tegensprak ("geen plaats of boot" tegenover "geen boot met een plaats"), en ik heb het rechtgezet en gelogd. Ook BLB-032 criterium 1 ging uit van een schrijfaanroep die niet meer bestaat. BLB-042 heb ik van Could naar Should gezet, omdat BLB-030 (Should) er anders van zou afhangen. Het robottoken bestaat vanaf slice 5 zonder manier om het in te trekken; dat staat als vraag 17 bij foundation.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Draai vóór de oplevering `git diff` op de leidende bronnen; een besluit dat tijdens je werk is bijgekomen, gaat voor de opdracht. Meld het in je antwoord."

Zet in de opdracht: "Verwijs naar een criterium op inhoud en niet alleen op nummer, bijvoorbeeld 'BLB-034, criterium over schrijfaanroepen'."
