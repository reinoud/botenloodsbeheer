# Terugblik: securityreview pyasn1 0.6.5 (#63)

Datum: 2026-11-03
Taak: securityreview van de gestagede diff in pyproject.toml en uv.lock (pyasn1 0.6.4 naar 0.6.5).

## Wat ging goed

De opdracht noemde de drie toetsvragen, de bron van het besluit en de regels in de overlay. Daardoor bleef de review klein: twee hashes vergelijken met de JSON-API van PyPI, de uitzondering lezen, en de pcre2-vraag uitzoeken.

## Wat kon beter

`uv` stond niet op het PATH van mijn shell, dus `uv lock --check` kon ik niet draaien. Ik heb de lock-hunk met de hand gecontroleerd. Een opruimcommando in de scratchpad werd door een hook vastgehouden; de twee gedownloade wheels staan nog in de scratchpad.

## Wat deed ik zelf goed

Ik heb de pcre2-vraag niet met de scan beantwoord maar met de wheels zelf. De amd64-wheel van psycopg-binary 3.3.6 levert geen pcre2 mee maar libpcre 1 (`libpcre-*.so.1.2.0`, uit de manylinux2014-basis). Trivy herkent pcre2 aan een versiestring in de bibliotheek; libpcre 1 heeft die string niet. Het verdwijnen van de melding op amd64 is dus een gat in de scan, geen oplossing.

## Wat heb ik onderweg zelf verbeterd

Ik wilde eerst trivy opnieuw draaien. Het rechtstreeks vergelijken van de inhoud van `psycopg_binary.libs` per architectuur gaf sneller en harder bewijs.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Verdwijnt een trivy-melding na een wijziging van architectuur of versie, vergelijk dan de inhoud van de meegeleverde `.libs`-map van de wheel per architectuur; een verdwenen melding is pas een oplossing als de bibliotheek zelf is vervangen."

Zet in de opdracht: "Noem het pad naar `uv` (of de Python-omgeving) zodat een reviewer `uv lock --check` kan draaien."
