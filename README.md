# LLM Provider Management Backend

This repository now includes a FastAPI backend for managing external Large Language Model (LLM) provider configurations alongside the existing Cloudflare Worker utilities. The backend persists provider data in SQLite, encrypts API keys at rest, and maintains a JSON backup that can be restored through an API endpoint or CLI command.

## Features

- CRUD API for managing external LLM providers
- Encrypted storage for provider API keys using a secret key
- Automated JSON backups of provider inventory on create/update/delete
- Connectivity test endpoint that reports status and latency
- Backup restore via admin API or CLI helper
- SQLite persistence with environment-driven configuration
- Comprehensive pytest-based unit and integration tests

## Project Structure

```
backend/
├── app/
│   ├── api/            # FastAPI route definitions
│   ├── core/           # Settings & security utilities
│   ├── db/             # SQLAlchemy models and session helpers
│   ├── schemas/        # Pydantic request/response models
│   ├── services/       # Business logic & backup utilities
│   └── main.py         # FastAPI application entry point
├── pyproject.toml      # Backend Python dependencies
└── tests/              # pytest suite
```

## Requirements

- Python 3.10+
- SQLite (bundled with Python)

## Configuration

The backend is configured via environment variables (optionally through a `.env` file). The most relevant settings are:

| Variable | Description | Default |
| --- | --- | --- |
| `BACKEND_DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./backend/data/providers.db` |
| `BACKEND_API_KEY_SECRET` | Secret used to encrypt provider API keys | `change-me` |
| `BACKEND_BACKUP_FILE` | Path to the JSON backup | `backend/config_backup.json` |
| `BACKEND_REQUEST_TIMEOUT_SECONDS` | Default timeout for provider tests | `10.0` |

> **Important:** Change `BACKEND_API_KEY_SECRET` in production environments to ensure encrypted API keys can be decrypted between deployments.

Create a `.env` file at the project root if desired:

```
BACKEND_DATABASE_URL=sqlite:///./backend/data/providers.db
BACKEND_API_KEY_SECRET=your-strong-secret
BACKEND_BACKUP_FILE=backend/config_backup.json
BACKEND_REQUEST_TIMEOUT_SECONDS=10
```

## Installation

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install the backend in editable mode with development dependencies:
   ```bash
   pip install -e backend[dev]
   ```

## Running the Application

Launch the FastAPI application with Uvicorn:

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. The automatically generated Swagger UI is accessible at `http://127.0.0.1:8000/docs`.

Database tables are created on startup if they do not yet exist. Provider updates are automatically mirrored to the configured JSON backup file.

## Frontend Management UI

A lightweight management UI powered by Vite + Vue 3 lives under `frontend/`. The UI surfaces provider CRUD actions, validation workflows, and connectivity tests against the backend API.

### Setup

```bash
cd frontend
npm install
```

### Local development

```bash
npm run dev
```

The development server proxies `/api` calls to the FastAPI backend at `http://127.0.0.1:8000` by default. Copy `.env.example` to `.env` in `frontend/` to override `VITE_API_BASE_URL` or `VITE_API_PROXY_TARGET`.

### Testing and builds

```bash
npm run test     # Run the Vitest suite
npm run build    # Generate a production build
npm run preview  # Preview the production build locally
```

Build artefacts are emitted to `frontend/dist/`.

## CLI Utilities

A small CLI is provided for manual backup management:

```bash
python -m backend.app.cli --export   # Write the current inventory to the backup file
python -m backend.app.cli --restore  # Restore providers from the backup file
```

## API Reference

### Provider Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/providers` | List all configured providers |
| `POST` | `/api/providers` | Create a new provider |
| `GET` | `/api/providers/{id}` | Retrieve a single provider |
| `PATCH` | `/api/providers/{id}` | Update provider details (name, URL, models, API key, status) |
| `DELETE` | `/api/providers/{id}` | Remove a provider |
| `POST` | `/api/providers/{id}/test` | Run a connectivity/health check against the provider |

#### Create Provider Payload

```json
{
  "name": "Example Provider",
  "base_url": "https://api.example.com/v1",
  "api_key": "sk-example-key",
  "models": ["example-model-1", "example-model-2"],
  "is_active": true
}
```

#### Test Endpoint Response

```json
{
  "status": "online",
  "status_code": 200,
  "latency_ms": 123.45,
  "detail": null
}
```

### Model Route Management

Model routes define strategies for selecting providers and models based on different selection modes.

#### Route Modes

- **`auto`**: Automatically rotate through configured providers using the specified strategy (round-robin or failover)
- **`specific`**: Select a specific provider/model combination based on model name hint
- **`multi`**: Select among multiple providers based on priority and strategy, with fallback behavior

#### Strategies

- **`round-robin`**: Distribute requests evenly across all nodes, cycling through in order
- **`failover`**: Use the first available provider, switching to the next on error or unhealthy status

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/model-routes` | List all configured routes |
| `POST` | `/api/model-routes` | Create a new route |
| `GET` | `/api/model-routes/{id}` | Retrieve a single route |
| `PATCH` | `/api/model-routes/{id}` | Update route configuration |
| `DELETE` | `/api/model-routes/{id}` | Remove a route |
| `POST` | `/api/model-routes/{id}/select` | Get the next provider/model selection for this route |
| `GET` | `/api/model-routes/{id}/state` | Get internal state (e.g., round-robin indices) |

#### Create Route Payload

```json
{
  "name": "llm-auto-route",
  "mode": "auto",
  "is_active": true,
  "config": {},
  "nodes": [
    {
      "api_id": 1,
      "models": [],
      "strategy": "round-robin",
      "priority": 0,
      "metadata": {}
    },
    {
      "api_id": 2,
      "models": [],
      "strategy": "round-robin",
      "priority": 0,
      "metadata": {}
    }
  ]
}
```

#### Route Selection Response

```json
{
  "provider_id": 1,
  "provider_name": "OpenAI",
  "model": "gpt-4"
}
```

#### Route State Response

```json
{
  "route_id": 1,
  "route_name": "llm-auto-route",
  "state": {
    "round_robin_indices": {
      "1": 1
    }
  }
}
```

### Backup Administration

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/admin/providers/restore` | Restore database contents (providers and routes) from the JSON backup |

### Health Check

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/ping` | Simple liveness probe |

## Testing

Run the full pytest suite (unit + integration tests):

```bash
pytest backend
```

Tests automatically provision an isolated SQLite database and backup file for each test case.

## Development Notes

- API keys are encrypted using a key derived from `BACKEND_API_KEY_SECRET`. Changing the secret invalidates existing encrypted keys.
- JSON backups are refreshed on every create/update/delete/test operation to keep the export current.
- When running under Uvicorn, database paths and backup directories are created automatically if they are missing.
