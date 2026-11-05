# Terugblik Pipeline: review Dependabot-PR's #75 tot en met #79 (issue #96)

Datum: 2026-11-05. Taak: de vijf Dependabot-updates van `images.yml` toetsen op SHA, brekende wijzigingen en samenhang.

## Wat ging goed

De opdracht noemde de controles en de commando's, waardoor de review in een paar aanroepen klaar was. Alle vijf tags zijn lichtgewicht tags en wijzen direct naar de commit uit de PR. De gebruikte inputs en outputs staan alle nog in `action.yml` op de nieuwe SHA.

## Wat kon beter

`python3` heeft geen PyYAML, dus mijn eerste ontleding van `action.yml` mislukte. Met `grep` en `ruby -ryaml` lukte het daarna wel.

## Wat deed je zelf goed

Ik heb de PR's proefgemerged in een eigen clone in de scratchpad in plaats van op `mergeable` van GitHub te vertrouwen. Daarmee kwam het conflict tussen #79 en #75/#76 boven: dat zijn aangrenzende regels, en GitHub toont elke PR los als mergeable.

## Wat heb je onderweg verbeterd

Ik heb beide volgordes geprobeerd: #79 eerst geeft twee conflicten, #79 als laatste één. De eindtoestand heb ik als YAML gecontroleerd.

## Wat kan structureel beter in de opdracht of de afspraken

Zet in de opdracht: "Bij meerdere PR's op hetzelfde bestand: proefmerge ze in een eigen clone in de volgorde van je advies en meld welke PR een rebase nodig heeft; `mergeable` van GitHub geldt per PR en zegt niets over de reeks."
