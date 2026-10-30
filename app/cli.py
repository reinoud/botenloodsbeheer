"""Beheercommando's: flask beheerder uitnodigen, flask taken draai en flask taken gezond."""

import sys

import click
from flask import current_app

from app import taken
from app.domein import CLI, Regelfout, beheerders


def registreer(app):
    @app.cli.group()
    def beheerder():
        """Beheerders."""

    @beheerder.command("uitnodigen")
    @click.argument("gebruikersnaam")
    def uitnodigen(gebruikersnaam):
        """Maakt een beheerder en toont een eenmalige link (24 uur geldig)."""
        try:
            code = beheerders.uitnodigen(gebruikersnaam, CLI)
        except Regelfout as fout:
            raise click.ClickException(str(fout)) from None
        click.echo(f"{current_app.config['BASIS_URL']}/uitnodiging/{code}")

    @app.cli.group("taken")
    def taken_groep():
        """Achtergrondtaken (ADR-007)."""

    @taken_groep.command("draai")
    def draai():
        """De lus van de worker."""
        taken.draai()

    @taken_groep.command("gezond")
    def gezond():
        """Exitcode 0 als de heartbeat van de worker jonger is dan 2 minuten."""
        sys.exit(0 if taken.gezond() else 1)
