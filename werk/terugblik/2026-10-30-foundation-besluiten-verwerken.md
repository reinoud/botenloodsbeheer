# Terugblik Foundation: besluiten verwerken

Datum: 2026-10-30. Taak: vijf stakeholderbesluiten verwerken in docs/architecture/ en docs/product/backlog.md.

## Wat ging goed
De opdracht noemde de leidende bron, de af te wijken punten en de grenzen (woordaantal, geen code, geen nieuwe open vragen). Daardoor was geen enkele vraag nodig.

## Wat kon beter
De opdracht liet open of het beheerdersmodel van herstel (wat de tweede beheerder mag) alles intrekt of alleen een link maakt. Dat ontwerpbesluit nam ik zelf.

## Wat deed je zelf goed
Eerst met grep alle plekken met oude termen gevonden, ook buiten de genoemde ADR's (datamodel, E2E-accounts, dreigingentabel, slice 1). Woordaantallen gecontroleerd met wc -w.

## Wat heb je onderweg zelf verbeterd
Een eerste vervangingsscript bevatte een nutteloze voorwaardelijke vervanging; vervangen door een eenduidige. Een mislukte sed -i op macOS vervangen door python.

## Structureel beter in opdracht of afspraken
Zet in de opdracht: "Bij een besluit dat een ontwerpdetail openlaat (zoals de reikwijdte van herstel), kies foundation de veiligste eenvoudige variant en meldt die in het antwoord."
Zet in de opdracht: "Nieuwe omgevingsvariabelen en afhankelijkheden die een besluit nodig maakt (hier TOTP_SLEUTEL, argon2-cffi, pyotp) mag foundation toevoegen en moet ze melden."
