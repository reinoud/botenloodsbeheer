"""Elke afbeelding in de README komt uit de map van de handleiding, staat ook in de handleiding en
wordt door schermafbeeldingen.py gemaakt (issue #423). Een nieuwe ronde afbeeldingen werkt de
README zo vanzelf bij."""

import re
from pathlib import Path

README = Path("README.md")
HANDLEIDING = Path("documentatie/gebruikers/handleiding.md")
SCRIPT = Path("documentatie/gebruikers/schermafbeeldingen.py")
MAP = "documentatie/gebruikers/afbeeldingen/"


def afbeeldingen(tekst):
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", tekst)


def problemen(readme, handleiding, script):
    uit = []
    for ref in afbeeldingen(readme):
        if not ref.startswith(MAP):
            uit.append(f"{ref}: niet uit {MAP}")
            continue
        naam = ref[len(MAP):]
        if not Path(ref).is_file():
            uit.append(f"{ref}: bestand ontbreekt")
        if f"(afbeeldingen/{naam})" not in handleiding:
            uit.append(f"{ref}: staat niet in de handleiding")
        if f'maak("{naam[:-4]}"' not in script and naam not in script:
            uit.append(f"{ref}: wordt niet door schermafbeeldingen.py gemaakt")
    return uit


def lees(pad):
    return pad.read_text(encoding="utf-8")


def test_readme_afbeeldingen_kloppen_met_handleiding_en_script():
    assert len(afbeeldingen(lees(README))) >= 3  # leeg zou ook slagen
    assert not problemen(lees(README), lees(HANDLEIDING), lees(SCRIPT))


def test_mutant_afbeelding_niet_in_de_handleiding():
    handleiding = lees(HANDLEIDING).replace("(afbeeldingen/boot.png)", "")
    assert problemen(lees(README), handleiding, lees(SCRIPT)) == [
        f"{MAP}boot.png: staat niet in de handleiding"]


def test_mutant_afbeelding_niet_in_het_script():
    script = lees(SCRIPT).replace('maak("wachtlijst"', 'maak("andere"')
    assert problemen(lees(README), lees(HANDLEIDING), script) == [
        f"{MAP}wachtlijst.png: wordt niet door schermafbeeldingen.py gemaakt"]


def test_mutant_ontbrekend_bestand_en_andere_map():
    readme = lees(README) + f"\n![x]({MAP}bestaat-niet.png)\n![y](elders/boot.png)\n"
    uit = problemen(readme, lees(HANDLEIDING), lees(SCRIPT))
    assert f"{MAP}bestaat-niet.png: bestand ontbreekt" in uit
    assert "elders/boot.png: niet uit " + MAP in uit
