"""Command-line interface."""
import click

@click.group()
def cli():
    """VaxGenesis CLI."""
    pass

def main():
    cli()
