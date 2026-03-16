# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeMCP is an AI orchestration and execution server based on the Model Context Protocol (MCP). It coordinates multiple AI agents to perform software development tasks through a four-layer data model (System → Block → Feature → Test) and provides a self‑healing capability via automatic failure handling and replanning.

The system consists of four core components:
- **Planner** – external AI that creates structured plans via MCP
- **Gateway** – FastAPI server that manages state machines, task windows, and persistence
- **Console** – interactive CLI (Typer + prompt‑toolkit) for monitoring and manual intervention
- **Executor** – external agent that executes individual test tasks

## Architecture Highlights

### Data Model (SQLAlchemy ORM)
- **System**: top‑level business domain or project instance
- **Block**: functional module belonging to a System
- **Feature**: concrete feature point belonging to a Block
- **Test**: physical verification unit belonging to a Feature

### Core Modules (planned structure under `src/codemcp/`)
- `models/` – SQLAlchemy ORM definitions for the four layers
- `database/` – session management, engine, Alembic migrations
- `api/` – FastAPI routes, schemas (Pydantic), WebSocket events
- `core/` – state machine, task‑window scheduler, executor interface, failure handler
- `cli/` – Typer CLI with interactive UI (prompt‑toolkit) and command modules
- `mcp/` – MCP protocol implementation for Planner/Executor communication
- `utils/` – logging, validation, serialization, time helpers

### State Management
- Tasks flow through `pending` → `running` → `passed`/`failed`
- A fixed‑size execution window (default depth 5) limits concurrent running tasks
- Failed tasks trigger automatic retries (max 3) and may cascade abort the owning Block
- Console allows human‑in‑the‑loop pause, resume, abort, and retry

### External Interfaces
- **Gateway REST API** – `POST /api/v1/plans`, `GET /api/v1/tasks/next`, etc.
- **MCP protocol endpoints** – `mcp://codemcp/plan/create`, `mcp://codemcp/task/fetch`, etc.
- **Console CLI** – `codemcp monitor`, `codemcp queue`, `codemcp status`, etc.

## Development Setup

### Dependencies
- Python ≥ 3.9
- Dependencies are listed in `pyproject.toml`; optional groups `dev` and `docs`.

```bash
# Install with development extras
pip install -e .[dev]

# Or use uv / pipx as preferred
```

### Environment Configuration
Copy `.env.example` to `.env` and adjust variables:
- `DATABASE_URL` (SQLite default, PostgreSQL supported)
- `HOST`, `PORT`, `DEBUG`, `LOG_LEVEL`
- `TASK_WINDOW_SIZE`, `MAX_RETRIES`, etc.

### Database Migrations
Alembic is configured for SQLAlchemy migrations.

```bash
# Create the database and apply migrations
alembic upgrade head

# After model changes, generate a new migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Common Development Tasks

### Running the Gateway Server
```bash
codemcp-server
# or directly:
uvicorn codemcp.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Using the Console CLI
```bash
codemcp                     # start interactive console
codemcp monitor --follow    # real‑time monitoring
codemcp queue --block       # pause task distribution
codemcp status --system <ID> # system‑level statistics
```

### Testing
```bash
# Run all tests (asyncio‑mode auto‑detected)
pytest

# With coverage report
pytest --cov=src/codemcp

# Run a specific test file
pytest tests/test_models/test_system.py -xvs

# Run tests matching a pattern
pytest -k "test_window" --tb=short
```

### Code Quality
```bash
# Format with Black and isort
black src/
isort src/

# Lint with ruff
ruff check src/
ruff format --check src/

# Type checking with mypy
mypy src/
```

### Building Documentation
```bash
# Install docs extras first
pip install -e .[docs]

# Serve MkDocs locally
mkdocs serve
```

## Configuration Files

- `pyproject.toml` – project metadata, dependencies, tool configurations (Black, isort, mypy, ruff, pytest)
- `alembic.ini` – Alembic migration settings (script location, database URL)
- `.env.example` – template for environment variables
- `Dockerfile` – container definition for production deployment

## Notes for Contributors

- The source code is planned to reside under `src/codemcp/`. The actual implementation may not yet be present; refer to `doc/` for detailed design documents.
- All new features should include unit tests (pytest‑asyncio for async code).
- Follow the existing code style (Black line length 88, isort with Black profile).
- Database schema changes must be accompanied by an Alembic migration.
- The Gateway API uses Pydantic v2 for request/response schemas.
- The CLI uses Typer; interactive components use prompt‑toolkit and Rich.

## Useful References

- `doc/` – comprehensive design documents (architecture, API spec, CLI design, testing strategy)
- `pyproject.toml` – complete toolchain configuration
- FastAPI, SQLAlchemy 2.0, Typer, and MCP documentation for external libraries