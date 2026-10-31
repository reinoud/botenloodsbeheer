"""Beheercommando's: flask beheerder uitnodigen, flask token robot en intrekken, flask seed,
flask taken draai en gezond."""

import sys

import click
from flask import current_app

from app import seed as seed_module
from app import taken
from app.domein import CLI, Regelfout, beheerders, tokens


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

    @app.cli.group()
    def token():
        """API-tokens (ADR-005, ADR-012)."""

    @token.command("robot")
    @click.argument("naam")
    @click.option("--recht", "rechten", multiple=True,
                  help=f"Herhaalbaar; minstens één van: {', '.join(tokens.RECHTEN)}.")
    @click.option("--whitelist", multiple=True,
                  help="Herhaalbaar, CIDR (IPv4 of IPv6). Standaard KOPPELNET.")
    @click.option("--dagen", type=int,
                  help=f"Geldigheid, standaard {tokens.STANDAARD_DAGEN}, hooguit "
                       f"{tokens.MAX_DAGEN} (3 jaar).")
    def robot(naam, rechten, whitelist, dagen):
        """Maakt een robottoken en toont de waarde één keer."""
        try:
            waarde = tokens.robot_maken(naam, rechten, whitelist, dagen, CLI)
        except Regelfout as fout:
            raise click.ClickException(str(fout)) from None
        click.echo("Het token staat nergens anders; bewaar het nu (bijvoorbeeld in "
                   "secrets/api_token, mode 0600).", err=True)
        click.echo(waarde)

    @token.command("intrekken")
    @click.argument("naam")
    def intrekken(naam):
        """Trekt een token in; de volgende aanroep wordt geweigerd."""
        try:
            tokens.intrekken(naam, CLI)
        except Regelfout as fout:
            raise click.ClickException(str(fout)) from None
        click.echo(f"Token {naam} is ingetrokken.")

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
