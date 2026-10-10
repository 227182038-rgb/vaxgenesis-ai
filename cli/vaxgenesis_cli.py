"""VaxGenesis AI — Command-line interface.

Usage:
    vaxgenesis login --email admin@vaxgenesis.ai
    vaxgenesis projects list
    vaxgenesis candidates create --project <id> --name "Candidate v1"
    vaxgenesis candidates run-pipeline <candidate-id>
    vaxgenesis surveillance status
    vaxgenesis modules list
    vaxgenesis xai explain <prediction-id>

Configuration:
    The CLI reads its configuration from ~/.vaxgenesis/config.json,
    created by `vaxgenesis login`. Override with --base-url and --token.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import click

CONFIG_DIR = Path.home() / ".vaxgenesis"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def _save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    os.chmod(CONFIG_FILE, 0o600)


def _get_client():
    """Construct an SDK client from saved config or env vars."""
    config = _load_config()
    base_url = (
        os.environ.get("VAXGENESIS_URL")
        or config.get("base_url")
        or "http://localhost:8000"
    )
    token = os.environ.get("VAXGENESIS_TOKEN") or config.get("token")
    if not token:
        click.echo("Not logged in. Run `vaxgenesis login` first.", err=True)
        sys.exit(1)
    from vaxgenesis_sdk.client import VaxGenesisClient
    return VaxGenesisClient(base_url=base_url, token=token)


# ============================================================
# CLI commands
# ============================================================

@click.group()
@click.version_option(version="2.0.0")
def cli() -> None:
    """VaxGenesis AI CLI."""


@cli.command()
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--base-url", default="http://localhost:8000")
def login(email: str, password: str, base_url: str) -> None:
    """Authenticate and save credentials."""
    from vaxgenesis_sdk.client import VaxGenesisClient

    async def _login():
        async with VaxGenesisClient(base_url=base_url) as client:
            token = await client.login(email, password)
            return token

    token = asyncio.run(_login())
    _save_config({"base_url": base_url, "token": token.access_token, "email": email})
    click.echo(f"Logged in as {email}. Config saved to {CONFIG_FILE}")


@cli.group()
def projects() -> None:
    """Manage projects."""


@projects.command("list")
def projects_list() -> None:
    """List your projects."""
    client = _get_client()

    async def _list():
        data = await client.projects.list()
        for p in data.get("items", []):
            click.echo(f"  {p['id']}  {p['name']}  [{p['status']}]")
        click.echo(f"\nTotal: {data.get('total', 0)}")

    asyncio.run(_list())


@projects.command("create")
@click.option("--name", prompt=True)
@click.option("--description", default=None)
def projects_create(name: str, description: str | None) -> None:
    """Create a new project."""
    client = _get_client()

    async def _create():
        project = await client.projects.create(name=name, description=description)
        click.echo(f"Created project: {project.id}")

    asyncio.run(_create())


@cli.group()
def candidates() -> None:
    """Manage vaccine candidates."""


@candidates.command("create")
@click.option("--project", required=True, help="Project ID")
@click.option("--name", required=True)
@click.option("--platform", default="multi_epitope")
def candidates_create(project: str, name: str, platform: str) -> None:
    """Create a new candidate."""
    client = _get_client()

    async def _create():
        c = await client.candidates.create(project_id=project, name=name, platform=platform)
        click.echo(f"Created candidate: {c.id}")

    asyncio.run(_create())


@candidates.command("run-pipeline")
@click.argument("candidate_id")
@click.option("--max-iterations", default=3)
def candidates_run(candidate_id: str, max_iterations: int) -> None:
    """Trigger the reasoning pipeline for a candidate."""
    client = _get_client()

    async def _run():
        job = await client.candidates.run_pipeline(candidate_id, max_iterations=max_iterations)
        click.echo(f"Pipeline started. Job ID: {job.get('job_id')}")

    asyncio.run(_run())


@cli.group()
def surveillance() -> None:
    """Surveillance subsystem."""


@surveillance.command("status")
def surveillance_status() -> None:
    """Show surveillance status."""
    client = _get_client()

    async def _status():
        s = await client.surveillance.status()
        click.echo(f"Running: {s.is_running}")
        click.echo(f"Sequences (24h): {s.sequences_seen_24h}")
        click.echo(f"Sequences (7d): {s.sequences_seen_7d}")
        click.echo(f"Active alerts: {s.active_alerts}")
        click.echo(f"Critical alerts: {s.critical_alerts}")

    asyncio.run(_status())


@cli.group()
def modules() -> None:
    """Pipeline modules."""


@modules.command("list")
def modules_list() -> None:
    """List all pipeline modules."""
    client = _get_client()

    async def _list():
        mods = await client.modules.list()
        for m in mods:
            status = "✓" if m.is_implemented else "✗"
            click.echo(f"  {status} {m['id']:40s} {m['name']}")

    asyncio.run(_list())


@cli.group()
def xai() -> None:
    """Explainable AI."""


@xai.command("explain")
@click.argument("prediction_id")
def xai_explain(prediction_id: str) -> None:
    """Get the XAI explanation for a prediction."""
    client = _get_client()

    async def _explain():
        data = await client.xai.get_explanation(prediction_id)
        click.echo(data.get("narrary", "No explanation available."))

    asyncio.run(_explain())


@cli.command()
def health() -> None:
    """Check backend health."""
    client = _get_client()

    async def _health():
        data = await client.health()
        click.echo(json.dumps(data, indent=2))

    asyncio.run(_health())


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
