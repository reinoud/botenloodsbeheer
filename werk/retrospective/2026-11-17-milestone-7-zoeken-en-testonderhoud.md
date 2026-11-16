# Retrospective milestone 7 "Zoeken en testonderhoud na v1.2.0"

Datum: 2026-11-17. Gesloten: #275, #162, #268, #279, #285, #283 en #278. Geen release binnen de milestone: #275 en #268 zijn zichtbaar voor de beheerder en staan nog niet in een versie. Input: de zeven terugblikken van 2026-11-16 in `werk/terugblik/`.

## Wat werkte

- Opdrachten die het criterium, het draaicommando en de mutanten noemden, gaven korte reviews (#268, #283, #279 en #285). De reviewer hoefde niet te zoeken en draaide direct de mutanten.
- Bij #283 vond de bouwer waarom de bestaande slottests de mutant lieten overleven: een latere stap nam hetzelfde slot. De nieuwe test roept `_vergrendel` direct aan, zonder thread en zonder wachttijd.
- Bij #278 telde de bouwer vóór de oplevering wat de verruimde regex in de echte database raakt. Zo vond hij een tweede lek: clubrekken uit `test_loods.py`.

## Wat beter kan

- Twee keer hield de vangrail een commando met `rm` tien minuten vast (#268, #275). Reviewers werken nu met verse mapnamen en vergelijken met `cmp` zonder tijdelijke bestanden.
- Een telling uit de staart van het log van `draai.sh` gaf 40 in plaats van 52 (#278). Tellen gaat nu met een script over alle samenvattingen.
- Een reviewer wachtte op de monitor en gaf daarna geen eindoordeel; de regie moest erom vragen (#278). Een bouwer liet een run van een heel bestand in de voorgrond verlopen (#283).
- `ruff` staat niet op de host, en een mutant op globale staat (het logo) vroeg een tweede poging omdat de opdracht niet zei hoe je die staat zet en uitleest (#279, #285).

## Waar de lessen landen

De lessen staan in `docs/PROJECT-OVERLAY.md` v0.5.88 tot en met v0.5.91. Restpunten uit de reviews staan als issue voor de volgende afstemming: #300 (twijfelregels in `opruimen.sql`). De 91 oude clubrekken met een onbekende stempel heeft de regie bij #278 eenmalig uit de lokale database verwijderd; #300 zorgt dat zo'n rest voortaan in een twijfelregel verschijnt.
