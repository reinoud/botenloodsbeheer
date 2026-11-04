# Terugblik sentinel: review volgorde verdiepingen Rekoverzicht

Datum: 2026-11-04
Taak: review van de gestagede diff (verdieping 1 onderaan op `/rekoverzicht`, vervolg op issue #87)

## Wat ging goed

De brief was klein en compleet: doel, diff, wat de regie al had gedraaid (mutant met het oude template, E2E) en welke suite ik zelf moest draaien. Daardoor bleef de review bij lezen, één suiterun (704 geslaagd) en het vergelijken van twee schermafbeeldingen.

## Wat kon beter

De brief noemde niet of andere schermen met verdiepingen (`/indeling`) dezelfde volgorde horen te krijgen. Ik heb dat zelf nagezocht en als observatie gemeld; vooraf benoemd was sneller geweest.

## Wat deed ik zelf goed

De oude schermafbeelding uit `HEAD` naast de nieuwe gelegd in plaats van alleen de nieuwe te bekijken, zodat de omkering aantoonbaar is en verder niets in het beeld veranderde.

## Wat heb ik onderweg verbeterd

Ik heb de mutant van de regie niet opnieuw gedraaid: de brief noemde de falende assert, en de overlay vraagt alleen dat die genoemd wordt. Dat scheelde een containerrun.

## Wat kan structureel beter

Zet in de opdracht: "Verandert een wijziging de volgorde of weergave op één scherm, noem dan de andere schermen die hetzelfde gegeven tonen en of die bewust ongewijzigd blijven."
