# Terugblik sentinel, review issue #88 en #89

Datum: 2026-11-04
Taak: review van de gestagede wijziging voor #88 (ruff op `docker/maak_plaatjes.py`, test op `{{ v.tekst }}` met escaping) en #89 (alle verdiepingen in het rekoverzicht).

## Wat ging goed

De brief noemde de doelen, de omgeving en wat de regie al had gedraaid. Daardoor kon ik steekproeven kiezen die iets toevoegen, in plaats van het werk van de regie te herhalen.

## Wat kon beter

De brief noemde niet of er niet-gestagede bestanden in de werkmap stonden. Ik heb dat zelf gecontroleerd met `git diff --stat` (leeg).

## Wat deed je zelf goed

Twee mutanten gekozen die de regie niet had gedraaid: `{{ v.tekst|safe }}` (toetst de escaping, niet alleen de aanwezigheid van de tekst) en een loop zonder verdieping 1. Beide vallen op een assert met een eigen melding of een herkenbare string.

## Wat heb je onderweg verbeterd

Na de mutantrun gezien dat `test_pagina_zet_verdieping_1_onderaan` nu altijd alle vijf rijen ziet; hij vangt nog steeds het weglaten van `reverse`, dus geen punt, wel genoteerd.

## Wat kan structureel beter

Zet in de opdracht: "Noem bij een escapingtest de mutant met `|safe` op het veld en of de regie die al heeft gedraaid."
