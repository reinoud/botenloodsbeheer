# Terugblik: review herstel slice 4

Datum: 2026-10-31
Taak: review van het herstel op slice 4 (geschikt voor, ICC-profiel logo, ids, docstring)

## Wat ging goed
De opdracht was klein en precies: vier punten, de patch als apart bestand, de testcommando's en de te doden mutant. Daardoor kon ik zonder zoekwerk toetsen. Unit 219 geslaagd, e2e 3 geslaagd, mutant gedood.

## Wat kon beter
De opdracht noemde niet hoe een los script in de testcontainer de app-module vindt. Mijn eerste controle op foto's faalde op een importfout, de tweede met `PYTHONPATH=/app` werkte.

## Wat deed ik zelf goed
Mutant en controlescript via een volume vanuit de scratchpad, zodat de werkmap niet is aangeraakt. Daarna `git status` en `git diff` vergeleken met de stand bij de start. De bewering van aegis over JPEG heb ik niet overgenomen maar gemeten, ook voor PNG- en WebP-bronnen als foto.

## Wat heb ik onderweg zelf verbeterd
Het controlescript breder gemaakt dan gevraagd: alle drie toegestane bronformaten met een ICC-profiel, niet alleen JPEG.

## Wat kan structureel beter
Zet in de opdracht: een los controlescript in de testcontainer draai je met `-e PYTHONPATH=/app` en een volume uit de scratchpad.
