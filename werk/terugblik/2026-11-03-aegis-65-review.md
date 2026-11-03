# Terugblik Aegis, securityreview issue #65 (gecodeerd pad)

Datum: 2026-11-03. Taak: securityreview van de gestagede diff voor #65 en PRB-01.

## Wat ging goed

De opdracht noemde de leidende norm (ADR-013, alinea "Gecodeerd pad"), de grens voor proeven op de gedeelde proxy en de proef van de bouwer. Door de uitkomst van die proef (`scratchpad/bedrock-65/uitkomst.txt`) hoefde ik geen losse Traefik met een lege bucket op te zetten.

## Wat kon beter

De vraag of de opties "volledig" zijn, had ik pas te beantwoorden na een blik in de binary van Traefik. Daarin staan zeven opties, de diff zet er vier. De ADR zegt niet waarom de andere drie ontbreken.

## Wat deed ik zelf goed

Ik heb de optienamen uit de binary van v3.7.17 gehaald en niet uit mijn geheugen. Op de gedeelde proxy heb ik alleen GET-verzoeken gestuurd (de router `inloggen` geldt alleen voor POST), dus de bucket voor inloggen bleef ongemoeid. Ik heb ook nagelopen of een codering vóór of achter `/inloggen` buiten de app om een route zou bereiken. Dat lukt niet: een achtervoegsel valt nog onder `PathPrefix`, een voorvoegsel geeft 404 in Werkzeug.

## Wat heb ik onderweg zelf verbeterd

Eerst wilde ik een losse Traefik starten voor `;`, `%3F` en de absolute URI. Dat bleek niet nodig: elk van die varianten geeft al 400 onder de grens, en zonder 400 had ik het verschil met een lege bucket toch niet kunnen zien.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bij een optie of vlag van een externe component worden de namen en de volledige lijst uit de gebruikte versie gehaald (binary of `--help`), en de ADR zegt welke opties bewust ontbreken."
