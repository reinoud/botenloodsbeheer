"""Beheercommando's: flask beheerder uitnodigen, flask seed, flask taken draai en gezond."""

import sys

import click
from flask import current_app

from app import seed as seed_module
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

    @app.cli.command("seed")
    def seed():
        """Synthetische loods voor ontwikkeling en tests; weigert in productie."""
        try:
            seed_module.seed(click.echo)
        except seed_module.SeedFout as fout:
            raise click.ClickException(str(fout)) from None

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
