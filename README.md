# LLM Provider Management Backend

This repository now includes a FastAPI backend for managing external Large Language Model (LLM) provider configurations alongside the existing Cloudflare Worker utilities. The backend persists provider data in SQLite, encrypts API keys at rest, and maintains a JSON backup that can be restored through an API endpoint or CLI command.

## Features

- CRUD API for managing external LLM providers
- Encrypted storage for provider API keys using a secret key
- Automated JSON backups of provider inventory on create/update/delete
- Connectivity test endpoint that reports status and latency
- Backup restore via admin API or CLI helper
- SQLite persistence with environment-driven configuration
- **OpenAI-compatible `/v1/chat/completions` endpoint** with routing engine integration
- Support for multiple providers (OpenAI, Anthropic Claude, Google Gemini) with automatic adapter selection
- Streaming and non-streaming chat completion modes
- Automatic retry/failover on provider failures
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

### OpenAI Chat Completions

The backend exposes an OpenAI-compatible `/v1/chat/completions` endpoint that leverages the routing engine to intelligently select providers and handle failover.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/v1/chat/completions` | Create a chat completion (streaming or non-streaming) |

#### Request Body

```json
{
  "model": "llm-auto-route",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false
}
```

The `model` parameter should reference a route name configured in the routing engine. The routing engine will select an appropriate provider/model based on the route configuration.

#### Response (Non-Streaming)

```json
{
  "id": "chatcmpl-123abc",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  }
}
```

#### Streaming Response

When `stream: true` is set, the endpoint returns Server-Sent Events (SSE) with chunks in OpenAI format:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

#### Provider Adapters

The backend automatically detects and uses the appropriate adapter based on the provider configuration:

- **OpenAI Adapter**: For OpenAI and OpenAI-compatible APIs
- **Anthropic Adapter**: For Claude models (translates between OpenAI and Anthropic message formats)
- **Gemini Adapter**: For Google Gemini models (translates to Gemini API format)

Provider detection is based on the provider name or base URL. Custom providers are treated as OpenAI-compatible by default.

#### Authentication

The endpoint supports optional API key authentication via the `Authorization` header:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llm-auto-route",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

#### Retry and Failover

The chat completions service automatically retries failed requests up to 3 times (configurable), selecting different providers via the routing engine. This provides automatic failover when a provider is unavailable or returns an error.

4xx errors from providers are not retried, as they typically indicate client errors (invalid request, authentication issues, etc.).

#### Usage with Cline

To use this endpoint with Cline or other OpenAI-compatible clients:

1. Set the API base URL to your backend: `http://127.0.0.1:8000/v1`
2. Set the model to your route name (e.g., `llm-auto-route`)
3. Optionally provide an API key if authentication is enabled

Example Cline configuration:

```json
{
  "openai": {
    "apiUrl": "http://127.0.0.1:8000/v1",
    "apiKey": "optional-key",
    "model": "llm-auto-route"
  }
}
```

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
