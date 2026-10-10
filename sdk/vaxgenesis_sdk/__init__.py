"""VaxGenesis AI — Python SDK.

A lightweight, typed Python client for the VaxGenesis AI REST API.
Depends only on `httpx` and `pydantic` — no backend dependencies.

Usage:
    from vaxgenesis_sdk import VaxGenesisClient

    client = VaxGenesisClient(
        base_url="http://localhost:8000",
        email="admin@vaxgenesis.ai",
        password="admin123",
    )

    # Create a project
    project = client.projects.create(name="My Project")

    # Create a candidate
    candidate = client.candidates.create(
        project_id=project.id,
        name="Candidate v1",
    )

    # Run the pipeline
    job = client.candidates.run_pipeline(candidate.id)

    # Get surveillance status
    status = client.surveillance.status()
"""
__version__ = "2.0.0"
