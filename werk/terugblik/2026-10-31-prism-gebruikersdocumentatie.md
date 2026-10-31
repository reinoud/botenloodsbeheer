# Terugblik Prism, gebruikersdocumentatie (issue #30)

Datum: 2026-10-31. Taak: handleiding, screenshotscript en test op de handleiding.

## Wat ging goed
Templates en routes zijn kort en duidelijk, dus de handleiding kon direct uit de code. Het script slaagde bij de eerste volledige run.

## Wat kon beter
De opdracht zei "tegen de draaiende stack". Die database bevatte honderden e2e-accounts van andere agents, wat de schermen vervuilt. Dat zag ik pas na het lezen van de database.

## Wat deed je zelf goed
Een eigen wegwerpstack (project botenloods-doc) met eigen database en eigen rate limit, zodat de lokale stack en de runs van anderen ongemoeid bleven. QR-code, TOTP-sleutel en uitnodigingscode worden vóór de opname uit het scherm gehaald.

## Wat heb je onderweg zelf verbeterd
De QR-placeholder toonde een kapotte afbeelding; die heeft nu een lege alt. De startpagina-opname is geschrapt omdat ze niets toevoegt.

## Wat kan structureel beter
Zet in de opdracht: "Screenshots en andere opnamen komen uit een eigen stack met een lege, geseede database, nooit uit de gedeelde lokale stack; kies zelf een projectnaam en een vrij subnet."
Zet in de opdracht: "Noem welke functies uit de lijst nog niet bestaan (hier: kaartjes met QR-code, slice 8), zodat het agent ze niet zoekt."
Zet in de checklist: "Een nieuwe map in de repository die een test leest, moet in de testcontainer gemount worden in compose.dev.yml."
