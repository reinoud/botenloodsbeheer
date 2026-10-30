# Terugblik foundation: vragen 9 en 10 (BLB-038)

**Datum:** 2026-10-30
**Taak:** open vragen 9 en 10 uit backlog §7 beantwoorden en vastleggen in ADR-001.

## Wat ging goed

De code gaf het antwoord direct. De sessie bewaart al `ingelogd_op` en het account heeft al een sessieversie, dus beide besluiten passen zonder nieuw veld, scherm of tabel.

## Wat kon beter

ADR-001 had geen versie en geen wijzigingslog, terwijl de opdracht vroeg die bij te werken. Ik heb v1.0.0 als vertrekpunt genomen en v1.1.0 toegevoegd. De andere ADR's hebben ook geen versie.

## Wat deed je zelf goed

De woorden heb ik met `wc -w` over de toegevoegde regels van de diff geteld, wijzigingslog en tabelrijen meegeteld: 236 van de 250. Een eerste versie van 267 woorden heb ik ingekort.

## Wat heb je onderweg verbeterd

Een terugsprong naar het profiel na opnieuw inloggen heb ik weggelaten. Die vraagt een `next`-parameter, en daarmee een risico op een open redirect, voor weinig winst.

## Wat kan structureel beter

Zet in de opdracht: "Heeft het document nog geen versie of wijzigingslog, begin dan op v1.0.0 en voeg een wijzigingslog toe onderaan."

Zet in de opdracht aan apex na een besluit van foundation: "Voeg voor elk besluit uit ADR-001 een acceptatiecriterium toe aan de story, of meld waarom niet."
