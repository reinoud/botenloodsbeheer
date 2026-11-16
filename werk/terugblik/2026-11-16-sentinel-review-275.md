# Terugblik sentinel, review #275 en #162

Datum: 2026-11-16. Taak: review vóór de commit van de vergrootglasknop in de kop (BV-78, #275) en de afgenomen iconen (#162), branch `feature/275-zoekicoon`.

## Wat ging goed

De brief noemde de leidende bron met commit en pad, de verwachte uitkomst van de regie (1375 geslaagd, mutant zonder mediablok faalt) en dat het akkoord van Design System er al was. Daardoor kon ik de byte-vergelijking met 7503a1c gericht doen in plaats van het ontwerp opnieuw te beoordelen.

## Wat kon beter

De brief zei niet of de unitsuite en `draai.sh` tegelijk mochten draaien; ik heb ze na elkaar gedraaid. Een gecombineerd commando met `rm` van een tijdelijk bestand in `/tmp` werd tien minuten vastgehouden door de bevestiging en niet uitgevoerd.

## Wat deed je zelf goed

CSS en alle vijf iconen met `cmp` tegen 7503a1c vergeleken via process substitution, zonder tijdelijke bestanden. Een eigen mutant op de CSS-test gedraaid (iconenmap zonder `zoek.svg` als bind mount) die op de juiste assert viel. De E2E-test twee keer gedraaid.

## Wat heb je onderweg verbeterd

Na de vastgehouden opdracht ben ik overgestapt op vergelijken zonder tijdelijke bestanden, en alle uitvoer naar de eigen submap in de scratchpad geschreven.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: "De unitsuite en `draai.sh -k <test>` mogen tegelijk draaien" of "draai ze na elkaar", en: "vergelijk bestanden met `cmp <(git show :pad) <(git -C <repo> show <commit>:pad)`, zonder tijdelijke bestanden en zonder `rm`."
