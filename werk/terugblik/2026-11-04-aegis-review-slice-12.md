# Terugblik Aegis, securityreview slice 12 (issue #80)

Datum: 2026-11-04. Taak: securityreview van de gestagede diff van slice 12.

## Wat ging goed

De brief noemde vier toetspunten, de stand van de gedeelde database (al op 0011) en wat ik niet mocht draaien. Daardoor kon ik de rechten direct live lezen en hoefde ik niets af te stemmen met Sentinel.

## Wat kon beter

Dynamisch kon ik de inlogplicht van de nieuwe route niet los aantonen: een POST zonder sessie strandt eerst op CSRF (400). Zonder testaccount blijft dat een statische controle van de decorator, aangevuld met de unittests.

## Wat deed ik zelf goed

Ik heb het UPDATE-recht van `botenloods_taken` op `bootsoort` herleid naar migratie 0010 (FOR KEY SHARE). Zo werd het niet ten onrechte als nieuw extra recht van 0011 gemeld.

## Wat heb ik onderweg verbeterd

Eerst wilde ik de escaping zelf via de proxy proeven. Na de grep bleek dat de unittests dat al toetsen met `<b>` op de openbare pagina, het plaatsdetail en het kaartje, en dat er geen `|safe` op de nieuwe velden staat. Een eigen proef voegde dan niets toe.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Wil je dat de reviewer een webroute positief via de proxy toetst, geef dan een testaccount of een sessiecookie voor de lokale stack mee. Anders blijft de controle op de inlogplicht statisch."
