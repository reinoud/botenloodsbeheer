# Terugblik sentinel, 2026-11-25

Taak: review vóór commit van #425 (test die de Traefik in `tests/proxy/compose.traefik.yml` gelijk houdt aan die in `compose.dev.yml`).

## Wat ging goed

De brief noemde de gekozen route, het commando, het ene testbestand en de mutant die de regie al had gedraaid. Ik hoefde alleen de andere kant te toetsen. Het testbestand slaagde (68 passed), en een mutant op de digest in `compose.dev.yml` viel op de nieuwe test (1 failed, 67 passed).

## Wat kon beter

De brief zei niet waarom `compose.dev.yml` de bron van de stack is en niet `documentatie/beheer/voorbeelden/traefik/compose.yml`, waar dezelfde digest staat. Dat heb ik zelf in het issue en in de commentaarregel boven de dienst nagelezen.

## Wat deed ik zelf goed

Ik heb de mutant op de kant gezet die de regie niet had gedraaid: de stack in plaats van `tests/proxy`. Zo is de vergelijking in beide richtingen bewezen. Ik heb ook nagegaan dat de regex in `compose.dev.yml` precies één regel vangt en dat een regel die hij mist (aanhalingstekens, commentaar) de test laat falen in plaats van vals groen.

## Wat heb ik onderweg verbeterd

Ik heb vóór de mutantrun met `cmp` gecontroleerd dat `compose.dev.yml` in de werkmap gelijk is aan de index, en de mutant uit `git show :compose.dev.yml` gemaakt.

## Wat kan structureel beter in de opdracht

Zet in de opdracht: bij een test die twee bestanden vergelijkt, noem welke mutant de regie al heeft gedraaid en laat de reviewer de mutant op het andere bestand draaien.
