# Terugblik apex: story uit issue #2

Datum: 2026-10-30. Taak: issue #2 verwerken als story BLB-038 in `docs/product/backlog.md` en die plannen in slice 2.

## Wat ging goed

De opdracht noemde de bronnen in volgorde van gezag, het storynummer, de slice en het woordbudget met de telmethode. Daardoor hoefde ik niets aan te nemen over scope of omvang. ADR-001 gaf genoeg detail om elk criterium te toetsen: activeren na één juiste TOTP-code, vijf pogingen en 15 minuten, passkey blijft werken.

## Wat kon beter

`gh issue view --comments` toonde alleen het commentaar en niet de tekst van het issue. Ik moest de tekst apart ophalen met `--json body`. De backlog heeft geen wijzigingslog, dus de versieverhoging naar v0.2.0 staat nergens toegelicht.

## Wat deed je zelf goed

Ik heb de aantallen in de gezondheidstabel (38 stories, 27 Must) met een script geteld en niet met de hand bijgehouden. De story telt 189 woorden met `wc -w`. Twee punten die ADR-001 openlaat (opnieuw bewijzen vóór een wijziging, sessies na intrekken) heb ik als vraag 9 en 10 vastgelegd in plaats van zelf in te vullen.

## Wat heb je onderweg verbeterd

Een eerste bewerking van de gezondheidstabel bevatte een tikfout in de te vervangen tekst en sloeg daardoor niet aan. Ik heb de regel opnieuw letterlijk overgenomen en de wijziging daarna gecontroleerd met `git diff --stat`.

## Wat kan structureel beter

Zet in de opdracht: "Haal een issue op met `gh issue view <nr> -R reinoud/botenloodsbeheer --json title,body,comments`; `--comments` alleen toont de tekst van het issue niet." En: "De backlog heeft geen wijzigingslog. Voeg er een toe in §9, of zeg dat de versie zonder logregel omhooggaat."
