# Mistral Routing Integration Guide

This guide demonstrates how to use the LLM Provider Router with Mistral AI as a configured provider and test all three routing modes.

## Overview

The routing system now supports three modes for selecting LLM providers:
1. **Auto Mode**: Cycles through active providers
2. **Specific Mode**: Uses a single designated provider
3. **Multi Mode**: Manages multiple providers with priority and failover strategies

## Setup

### 1. Add Mistral Provider

```bash
curl -X POST http://localhost:8000/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mistral",
    "base_url": "https://api.mistral.ai/v1/",
    "api_key": "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr",
    "models": ["open-mixtral-8x22b", "mistral-small", "mistral-medium", "mistral-large"]
  }'
```

Response:
```json
{
  "id": 1,
  "name": "Mistral",
  "base_url": "https://api.mistral.ai/v1/",
  "models": ["open-mixtral-8x22b", "mistral-small", "mistral-medium", "mistral-large"],
  "is_active": true,
  "is_healthy": true,
  "status": "unknown",
  ...
}
```

## Mode Examples

### Auto Mode - Use All Providers

Creates a route that cycles through all active providers:

```bash
curl -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto Route",
    "mode": "auto",
    "is_active": true,
    "config": {
      "providerMode": "all",
      "selectedModels": ["open-mixtral-8x22b"],
      "modelStrategy": "single"
    },
    "nodes": []
  }'
```

**Key Points:**
- No route_nodes required (empty array)
- Models specified in config.selectedModels
- When providerMode="all", routes through all active providers
- When providerMode="provider_N", uses specific provider

**Frontend Usage:**
- Mode: "Auto - Cycle through providers"
- Provider Selection dropdown shows "Use all enabled providers (cycle)" or specific provider
- Models displayed as checkboxes from provider list
- Auto strategy determined: 1 model = "Single", 2+ = "Cycle"

### Specific Mode - Fixed Provider

Routes requests to a specific provider:

```bash
curl -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Specific Route",
    "mode": "specific",
    "is_active": true,
    "config": {
      "selectedModels": ["mistral-large"],
      "modelStrategy": "single"
    },
    "nodes": [{
      "api_id": 1,
      "models": ["mistral-large"],
      "strategy": "round-robin",
      "priority": 0,
      "node_metadata": {}
    }]
  }'
```

**Key Points:**
- Must specify route_nodes with provider
- Models can be in config OR in node
- Always routes to the specified provider

**Frontend Usage:**
- Mode: "Specific - Use single provider"
- Provider Selection dropdown
- Models displayed as checkboxes from selected provider
- Auto strategy: 1 model = "Single", 2+ = "Cycle"

### Multi Mode - Priority Failover

Routes to multiple providers with priority-based failover:

```bash
curl -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Multi Route",
    "mode": "multi",
    "is_active": true,
    "config": {},
    "nodes": [
      {
        "api_id": 1,
        "models": ["mistral-small", "mistral-medium"],
        "strategy": "round-robin",
        "priority": 0,
        "node_metadata": {}
      }
    ]
  }'
```

**Key Points:**
- Multiple nodes each with own provider
- Priority determines order (lower number = higher priority)
- Strategy per node: "round-robin" or "failover"
- Falls back to next priority on failure

**Frontend Usage:**
- Mode: "Multi - Multiple providers with priority"
- Add Provider button to create multiple provider cards
- Each card: Provider selector, Priority, Strategy, Models
- Models displayed as checkboxes per provider

## Testing All Modes

Run the comprehensive test suite:

```bash
# Test all three modes with Mistral
python test_routes_mistral.py

# Test Cline-style external client integration
python test_cline_integration.py
```

### Manual Testing with curl

**Test Auto Mode:**
```bash
# Create auto route
ROUTE_ID=$(curl -s -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Auto",
    "mode": "auto",
    "is_active": true,
    "config": {"providerMode": "all", "selectedModels": ["open-mixtral-8x22b"], "modelStrategy": "single"},
    "nodes": []
  }' | jq -r '.id')

# Select provider
curl -X POST http://localhost:8000/api/model-routes/$ROUTE_ID/select
```

**Test Specific Mode:**
```bash
# Create specific route
ROUTE_ID=$(curl -s -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Specific",
    "mode": "specific",
    "is_active": true,
    "config": {"selectedModels": ["mistral-large"], "modelStrategy": "single"},
    "nodes": [{"api_id": 1, "models": ["mistral-large"], "strategy": "round-robin", "priority": 0, "node_metadata": {}}]
  }' | jq -r '.id')

# Select provider
curl -X POST http://localhost:8000/api/model-routes/$ROUTE_ID/select
```

**Test Multi Mode:**
```bash
# Create multi route
ROUTE_ID=$(curl -s -X POST http://localhost:8000/api/model-routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Multi",
    "mode": "multi",
    "is_active": true,
    "config": {},
    "nodes": [{"api_id": 1, "models": ["mistral-small", "mistral-medium"], "strategy": "round-robin", "priority": 0, "node_metadata": {}}]
  }' | jq -r '.id')

# Select provider
curl -X POST http://localhost:8000/api/model-routes/$ROUTE_ID/select
```

## Web UI Testing

1. Navigate to http://localhost:5173
2. Go to "Model Routes" section
3. Click "Add route"

### Test Auto Mode:
- Name: "My Auto Route"
- Mode: "Auto - Cycle through providers"
- Check "Route is active"
- Provider Selection: Choose "Use all enabled providers (cycle)"
- Models to enable: Check "open-mixtral-8x22b"
- Click "Create route"
- Verify Status shows "Active" and Providers shows "1 models configured"

### Test Specific Mode:
- Name: "My Specific Route"
- Mode: "Specific - Use single provider"
- Check "Route is active"
- Select Provider: "Mistral"
- Models to enable: Check "mistral-large"
- Click "Create route"
- Verify nodes show "Mistral" provider

### Test Multi Mode:
- Name: "My Multi Route"
- Mode: "Multi - Multiple providers with priority"
- Check "Route is active"
- Click "Add Provider"
- Provider: "Mistral"
- Priority: 0
- Strategy: "round-robin"
- Models to enable: Check "mistral-small" and "mistral-medium"
- Click "Create route"

## Frontend Changes Summary

### RouteFormModal.vue
- **Auto Mode**: Now shows aggregated models from all active providers when using "all"
- **Specific Mode**: Models displayed as checkboxes from selected provider
- **Multi Mode**: Each provider has models as checkboxes

### RoutesTable.vue
- Shows "X models configured" for Auto routes even without nodes
- Displays nodes with provider name, models, and strategy for other modes
- Status badges show Active/Inactive status

## Backend Changes Summary

### routing.py
- **create_route()**: Validates config-based models for auto/specific modes
- **update_route()**: Same validation as create
- **_select_auto_with_config()**: Handles auto mode with config
- **_select_specific_with_config()**: Handles specific mode with config
- New aggregation logic when providerMode="all"

### routes.py (API endpoints)
- Fixed POST/PATCH serialization to properly return nodes
- Now manually constructs response with all node fields

## Cline Integration

For Cline or other external clients:

```
Configuration:
  apiBase: http://localhost:8000
  apiKey: {your-mistral-api-key}
  model: open-mixtral-8x22b

Usage:
  1. Call: POST /api/model-routes/{route_id}/select
  2. Get: {"provider_id": 1, "provider_name": "Mistral", "model": "..."}
  3. Use: Connect to https://api.mistral.ai/v1/ with returned model
```

## Troubleshooting

### "No providers configured" error
- Ensure at least one provider (Mistral) is created and active
- Check provider health status: `GET /api/providers`

### "Field required" error
- Ensure at least one model is selected for the route
- For Auto mode with "all", models must exist in at least one active provider
- For Specific/Multi modes, each provider must have at least one model

### 404 Error on select
- Verify route ID is correct: `GET /api/model-routes`
- Check route is_active: only active routes can be selected
- Ensure at least one provider is healthy: `GET /api/providers`

### Models not appearing
- Provider must be active and have models
- For Auto mode, must select "all" or specific provider
- Check frontend console for errors

## API Reference

### Create Route (Auto Mode)
```
POST /api/model-routes
{
  "name": "string",
  "mode": "auto",
  "is_active": true,
  "config": {
    "providerMode": "all" | "provider_{id}",
    "selectedModels": ["string"],
    "modelStrategy": "single" | "cycle"
  },
  "nodes": []
}
```

### Create Route (Specific Mode)
```
POST /api/model-routes
{
  "name": "string",
  "mode": "specific",
  "is_active": true,
  "config": {
    "selectedModels": ["string"],
    "modelStrategy": "single" | "cycle"
  },
  "nodes": [{
    "api_id": number,
    "models": ["string"],
    "strategy": "round-robin" | "failover",
    "priority": number,
    "node_metadata": {}
  }]
}
```

### Create Route (Multi Mode)
```
POST /api/model-routes
{
  "name": "string",
  "mode": "multi",
  "is_active": true,
  "config": {},
  "nodes": [{
    "api_id": number,
    "models": ["string"],
    "strategy": "round-robin" | "failover",
    "priority": number,
    "node_metadata": {}
  }]
}
```

### Select Provider
```
POST /api/model-routes/{route_id}/select?model={optional_hint}

Response:
{
  "provider_id": number,
  "provider_name": "string",
  "model": "string"
}
```

## Configuration

### Auto Mode (providerMode = "all")
- Aggregates models from all active providers
- Round-robin cycles through providers
- Selects first available model from config

### Auto Mode (providerMode = "provider_N")
- Always uses specific provider
- Selects model from configured list
- Falls back to first available if not found

### Specific Mode
- Always uses configured provider
- Validates model exists in provider
- Error if provider unhealthy

### Multi Mode
- Uses priority order (0 = highest)
- Applies strategy per node
- Cascades through priorities on failure

## See Also
- test_routes_mistral.py - Comprehensive test suite
- test_cline_integration.py - Cline integration examples
- ROUTE_CONFIG_PROVIDER_MODEL_AUTO_CYCLE.md - Detailed architecture
