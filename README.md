# LLM Provider Management Backend

This repository now includes a FastAPI backend for managing external Large Language Model (LLM) provider configurations alongside the existing Cloudflare Worker utilities. The backend persists provider data in SQLite, encrypts API keys at rest, and maintains a JSON backup that can be restored through an API endpoint or CLI command.

## Features

- CRUD API for managing external LLM providers
- Encrypted storage for provider API keys using a secret key
- **Automated health checks** with background task scheduling and health status tracking
- **Routing with health awareness** - automatically skips unhealthy providers and triggers failover
- Automated JSON backups of provider inventory on create/update/delete
- Connectivity test endpoint that reports status and latency
- Manual health overrides for provider enable/disable
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
| `BACKEND_HEALTH_CHECK_ENABLED` | Enable automatic background health checks | `true` |
| `BACKEND_HEALTH_CHECK_INTERVAL_SECONDS` | Interval between health checks | `60.0` |
| `BACKEND_HEALTH_CHECK_TIMEOUT_SECONDS` | Timeout for individual health check requests | `5.0` |
| `BACKEND_HEALTH_CHECK_FAILURE_THRESHOLD` | Consecutive failures before marking unhealthy | `3` |

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
| `POST` | `/api/providers/test-direct` | Test a provider configuration without saving to database |
| `POST` | `/api/providers/{id}/test` | Run a connectivity/health check against the provider |
| `PATCH` | `/api/providers/{id}/health` | Manually override provider health status |

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

#### Test Direct Payload

Test a provider configuration without saving it to the database:

```json
{
  "base_url": "https://api.example.com/v1",
  "api_key": "sk-test-key",
  "models": ["test-model-1", "test-model-2"]
}
```

The response uses the same format as the test endpoint response above. This endpoint is useful for validating provider configurations before saving them.

#### Health Override Payload

```json
{
  "is_healthy": false
}
```

### Health Monitoring

The system includes automated health checking that periodically probes each active provider and updates its health status:

#### How It Works

1. **Background Task**: On startup, a health check background task is initiated and runs at the configured interval (`BACKEND_HEALTH_CHECK_INTERVAL_SECONDS`).
2. **Probing**: Each active provider is pinged using an HTTP GET request to its base URL with appropriate authentication headers.
3. **Status Updates**: Provider status is updated based on the probe result:
   - `online`: HTTP 2xx response
   - `degraded`: HTTP 3xx/4xx/5xx response
   - `timeout`: Request exceeded timeout
   - `unreachable`: Connection error
   - `error`: Unexpected error during check
4. **Failure Tracking**: Consecutive failures are tracked. Once failures exceed the threshold (`BACKEND_HEALTH_CHECK_FAILURE_THRESHOLD`), the provider is marked as unhealthy.
5. **Recovery**: A successful check resets the failure count to 0.

#### Provider Response Fields

Each provider includes health-related fields:

```json
{
  "id": 1,
  "name": "OpenAI",
  "base_url": "https://api.openai.com/v1",
  "models": ["gpt-4", "gpt-3.5-turbo"],
  "is_active": true,
  "status": "online",
  "latency_ms": 45.2,
  "last_tested_at": "2024-01-15T10:30:00+00:00",
  "consecutive_failures": 0,
  "is_healthy": true,
  "created_at": "2024-01-10T08:00:00+00:00",
  "updated_at": "2024-01-15T10:30:00+00:00"
}
```

#### Routing Integration

Routing automatically considers health status:

- **Round-robin and Specific modes**: Skip unhealthy providers; if all providers are unhealthy, routing fails with an error.
- **Multi mode**: Prioritizes healthy providers; falls back through priority order, skipping unhealthy ones.
- **Failover strategy**: If a provider becomes unhealthy, the next provider in order is automatically selected.

#### Manual Overrides

To manually override a provider's health status (e.g., for maintenance):

```bash
PATCH /api/providers/{id}/health
Content-Type: application/json

{
  "is_healthy": false
}
```

This marks the provider as unhealthy and resets its failure count, allowing graceful degradation during maintenance windows.

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

## Docker Deployment

The application includes Docker support for containerized deployment with both backend and frontend services.

### Quick Start with Docker Compose

1. **Prepare environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and change BACKEND_API_KEY_SECRET to a secure value
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Check logs:**
   ```bash
   docker-compose logs -f backend  # Backend logs
   docker-compose logs -f frontend # Frontend logs
   ```

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Docker Build Details

#### Backend Dockerfile
- Uses multi-stage build for minimal final image size
- Based on `python:3.10-slim`
- Installs runtime dependencies (SQLite3)
- Includes health checks
- Automatically initializes database and restores from backup on startup

#### Frontend Dockerfile
- Uses multi-stage build (Node.js builder → Nginx server)
- Based on `nginx:alpine` for production serving
- Includes Gzip compression
- Serves static assets with proper caching headers
- Proxies API calls to backend service
- Includes health checks

#### Nginx Configuration
- Handles SPA routing (all non-asset routes serve index.html)
- Proxies `/api/` and `/ping` endpoints to backend
- Sets security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Enables Gzip compression for text-based assets
- Caches static assets with 1-year expiration

### Environment Variables for Docker

See `.env.example` for a complete list. Key variables:

```bash
# Core settings
BACKEND_DATABASE_URL=sqlite:///./data/providers.db
BACKEND_API_KEY_SECRET=your-strong-secret-key
BACKEND_BACKUP_FILE=./data/config_backup.json

# Health checks
BACKEND_HEALTH_CHECK_ENABLED=true
BACKEND_HEALTH_CHECK_INTERVAL_SECONDS=60.0
BACKEND_HEALTH_CHECK_TIMEOUT_SECONDS=5.0
BACKEND_HEALTH_CHECK_FAILURE_THRESHOLD=3

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### Volume Persistence

The docker-compose configuration creates two named volumes:

- `backend-data`: Persists SQLite database and backup files
- `backend-logs`: Persists application logs

These volumes ensure data persists across container restarts.

### Production Considerations

When deploying to production:

1. **Change secrets:** Update `BACKEND_API_KEY_SECRET` to a strong, unique value (minimum 32 characters)
2. **TLS/HTTPS:** Configure a reverse proxy (nginx, Traefik, or AWS ALB) for TLS termination
3. **Secrets management:** Use Docker secrets or environment variable services instead of .env files
4. **Scaling:** Use orchestration tools (Docker Swarm, Kubernetes) for multi-replica deployments
5. **Monitoring:** Integrate with monitoring solutions (Prometheus, ELK, DataDog)
6. **Backup strategy:** Configure automated backup of the backend-data volume
7. **Logging:** Centralize logs using Docker logging drivers or log aggregation services

## Observability & Monitoring

The application includes comprehensive observability features for monitoring performance, health, and debugging.

### Structured Logging

All application events are logged with structured JSON format to `backend/logs/app.log`:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "logger": "app.services.routing",
  "message": "Selected provider for route",
  "request_id": "a1b2c3d4-e5f6-7890",
  "method": "POST",
  "path": "/api/model-routes/1/select",
  "status_code": 200,
  "duration_ms": 45.2
}
```

#### Features
- **Sensitive data redaction**: API keys, passwords, and tokens are automatically redacted
- **Request tracing**: Correlation IDs are included in all log entries for request tracking
- **Context information**: HTTP method, path, status code, and duration are captured
- **Log rotation**: Logs are rotated when reaching 10MB (10 backup files retained)
- **Dual output**: JSON to files for structured processing, plain text to console for development

#### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for failures

### Metrics API

Access application metrics at the `/api/admin/stats` endpoint:

```bash
curl http://localhost:8000/api/admin/stats
```

Response includes:

```json
{
  "uptime_seconds": 3600.5,
  "total_requests": 1250,
  "total_errors": 15,
  "error_rate": 1.2,
  "average_duration_ms": 45.3,
  "status_codes": {
    "200": 1150,
    "404": 50,
    "500": 15,
    "201": 35
  },
  "endpoints": {
    "GET /api/providers": {
      "count": 250,
      "total_duration_ms": 10000,
      "avg_duration_ms": 40,
      "error_count": 0
    },
    "POST /api/model-routes/1/select": {
      "count": 100,
      "total_duration_ms": 5000,
      "avg_duration_ms": 50,
      "error_count": 2
    }
  },
  "recent_requests": [
    {
      "timestamp": 1705318200.5,
      "method": "GET",
      "path": "/api/providers",
      "status_code": 200,
      "duration_ms": 42.1
    }
  ]
}
```

#### Metrics Tracked
- **Uptime**: Server uptime in seconds
- **Total requests**: Number of requests since startup
- **Total errors**: Number of error responses (4xx, 5xx)
- **Error rate**: Percentage of requests that resulted in errors
- **Average response time**: Average request duration in milliseconds
- **Status code distribution**: Breakdown of response status codes
- **Per-endpoint stats**: Request count, error count, average duration
- **Recent requests**: Last 10 requests for debugging

### Logs API

Access recent logs at `/api/admin/logs`:

```bash
# Get last 50 logs (default)
curl http://localhost:8000/api/admin/logs

# Get last 200 logs
curl http://localhost:8000/api/admin/logs?limit=200
```

Response:

```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "level": "INFO",
      "logger": "backend.app.main",
      "message": "Request completed",
      "request_id": "a1b2c3d4-e5f6",
      "method": "GET",
      "path": "/api/providers",
      "status_code": 200,
      "duration_ms": 45.2
    }
  ],
  "total": 50
}
```

### Observability Dashboard

The frontend includes a comprehensive observability dashboard at `/observability`:

#### Widgets
- **Uptime display**: Server uptime in human-readable format
- **Total requests**: Cumulative request count since startup
- **Error rate**: Current error rate percentage with color coding
- **Average response time**: Mean response time in milliseconds

#### Health Status
Visual badges showing system health:
- **Healthy** (< 5% error rate): Green badge
- **Degraded** (5-20% error rate): Yellow badge
- **Warning** (> 20% error rate): Red badge

#### Top Endpoints
Table showing:
- Most frequently called endpoints
- Request counts
- Average response times
- Error counts per endpoint

#### Recent Logs
Live log viewer showing:
- Last 10 logs (load more button for additional logs)
- Color-coded by log level (DEBUG, INFO, WARNING, ERROR)
- Request context (method, path, status code, duration)
- Request ID for correlation
- Auto-refresh every 30 seconds

### Log Rotation & Persistence

Log files are stored in `backend/logs/` with automatic rotation:

- **Max file size**: 10 MB
- **Max backups**: 10 files (100 MB total)
- **Format**: JSON (parseable by log aggregation tools)
- **Retention**: Oldest logs are automatically removed when backup count exceeded

For Docker deployments, logs persist in the `backend-logs` volume.

## Quick Start Commands

For common development and deployment tasks, use the Makefile:

```bash
make help              # Show all available commands
make install           # Install dependencies
make dev               # Start backend and frontend in dev mode
make test              # Run all tests
make build             # Build application
make docker-build      # Build Docker images
make docker-up         # Start containers
make docker-down       # Stop containers
make docker-logs       # Follow container logs
make lint              # Run linting checks
make format            # Format code
```

## Development Notes

- API keys are encrypted using a key derived from `BACKEND_API_KEY_SECRET`. Changing the secret invalidates existing encrypted keys.
- JSON backups are refreshed on every create/update/delete/test operation to keep the export current.
- When running under Uvicorn, database paths and backup directories are created automatically if they are missing.
- Logs are structured in JSON format and include request correlation IDs for tracing.
- Sensitive data in logs is automatically redacted to prevent accidental exposure.
- Metrics are collected in-memory and reset on application restart.
