# Terugblik sentinel, review #379 (menuknop in de kop)

Datum: 2026-11-23. Taak: review vóór commit van de gestagede diff op `fix/379-menuknop` (`app/web/static/stijl.css`, `tests/e2e/test_zoeken.py`).

## Oordeel

Akkoord.

- `app/web/static/stijl.css:64-65`: de regel `@media (width < 56.25rem) { .bl-kop .dj-menu { margin-top: 0; } }` heft de algemene regel `details { margin-top }` (regel 31) alleen op voor het menu in de kop. Gemeten op 360, 479, 480, 639, 640, 700 en 899 px: veld, zoekknop en menuknop op middenlijn 88 px, margin-top van het menu 0. Op 900 en 1100 px is de knop weg (`dj-components.css:248-254`) en blijft margin-top 16 px, dus op een breed scherm verandert niets. De bereiksyntaxis `width < 56.25rem` en `min-width: 900px` van de basis sluiten zonder gat op elkaar aan.
- De selector raakt geen andere `details`: `details.dj-menu` staat alleen in `app/web/templates/base.html:41`; de uitklapblokken (`dj-disclosure`, `bl-nieuw`) houden hun marge. Geen basiscomponent gewijzigd (ADR-002).
- `tests/e2e/test_zoeken.py:44-46`: de nieuwe assert vergelijkt de middenlijnen met een marge van 1 px. Mutant zonder de CSS-regel: de test faalt op `(360, [96.0, 96.0, 104.0])`.
- ruff in de testcontainer: geen meldingen.

Tests: met de wijziging 1 geslaagd, 0 gefaald, 0 overgeslagen (58 gedeselecteerd); met de mutant 1 gefaald. Logs: `/private/tmp/claude-502/-Users-reinoud-git-botenloods/7b9e05a9-c349-4d44-9c59-ce5aa45280dd/scratchpad/sentinel-379/na.log` en `mutant.log`. Na het terugzetten is `stijl.css` gelijk aan de gestagede versie (`cmp`, `git diff --stat` leeg) en is `web` opnieuw aangemaakt en healthy.

Niet getoetst: een browser met een andere standaardlettergrootte dan 16 px. Dan valt 56.25rem niet meer samen met de 900px van de basis; dat verschil bestond al vóór deze diff en hoort niet bij #379.

## Wat ging goed

De brief noemde de oorzaak, de getallen van de bouwer, het moment van de laatste recreate en het commando voor `web`. Daardoor kon ik de mutant direct draaien zonder uitzoekwerk.

## Wat kon beter

De brief zei "je wijzigt niets" en tegelijk "CSS-regel tijdelijk weg in een kopie; zet het bestand daarna terug". Een kopie als volume (overlay, mutantregel #268) werkt voor de E2E-suite niet, want die test tegen de draaiende `web`. Ik heb het werkbestand tijdelijk aangepast en teruggezet uit de index.

## Wat deed ik zelf goed

Ik heb de tussenbreedtes gemeten met een eigen script in de scratchpad, op basis van het meetscript van de bouwer, met een eigen stempel die `opruimen.sql` weer opruimt. Zo staat de dekking tussen 40rem en 900px vast als meting en niet alleen als lezing van de CSS.

## Wat heb ik onderweg zelf verbeterd

Vóór de mutant heb ik een kopie van `stijl.css` bewaard en na het terugzetten met `cmp` en beide `git diff --stat` gecontroleerd. Ik heb ook gecontroleerd dat de geserveerde CSS de regel echt mist (curl) voordat de mutantrun telde.

## Wat kan structureel beter in de opdracht of de afspraken

Een mutant op CSS of templates kan niet met een kopie als volume, want de E2E-tests lopen tegen de draaiende `web`. Regel voor de opdracht: "Mutant op CSS of templates: bewaar het bestand in je scratchpad, pas het werkbestand aan, maak `web` opnieuw aan, controleer met curl dat de geserveerde versie de mutant is, en zet daarna terug met `git checkout -- <pad>` (de gestagede versie) en een nieuwe `web`."
