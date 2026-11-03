# Terugblik apex, backlog bijwerken voor issue #80

Datum: 2026-11-03. Taak: BLB-001, BLB-004 en de nieuwe BLB-044 in `docs/product/backlog.md` afstemmen op rek, verdieping en vak (issue #80).

## Wat ging goed

Issue #80 was volledig: grenzen, standaardkeuzes en een route voor een mens. Daardoor waren de criteria zonder overleg te schrijven. De volgorde van bronnen in de opdracht maakte duidelijk dat #80 voorgaat.

## Wat kon beter

De opdracht vroeg om een regel in het wijzigingslog "als dat er is". Het backlog heeft geen wijzigingslog; ik heb alleen de versie (v0.3.23 naar v0.4.0) en de statusregel bijgewerkt. De gezondheidstabel stond al op 42 stories terwijl er 43 waren (BLB-043 ontbrak bij Should); dat heb ik meegenomen.

## Wat deed ik zelf goed

Ik heb de woorden geteld met `git diff --word-diff=porcelain` in plaats van `wc -w` op hele gewijzigde regels. Die laatste telt ongewijzigde woorden in een aangepaste regel mee en gaf 1420 in plaats van de werkelijke 742. Daarna ingekort tot 599.

## Wat heb ik onderweg zelf verbeterd

Een criterium "1 of 5 verdiepingen" las als een keuze tussen twee waarden; aangepast naar "1 tot en met 5". Een eigen sectie "Besluiten van apex" en een uitleg boven BLB-001 heb ik geschrapt om binnen het budget te blijven; de inhoud staat al in de criteria.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Tel het woordbudget met `git diff --word-diff=porcelain <bestand> | grep '^+' | grep -v '^+++' | wc -w`; `wc -w` op de plusregels telt ongewijzigde woorden in aangepaste regels mee."
