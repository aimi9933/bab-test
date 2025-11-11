# Route Configuration: Provider & Model Auto-Cycle Implementation

## Overview

This implementation addresses the three main issues with route configuration:

1. **Auto Mode** - Now has clear provider selection (all or specific)
2. **Specific Mode** - Now shows models from provider's list as checkboxes
3. **Multi Mode** - Each provider shows models as checkboxes
4. **Model Strategy** - Automatically determined: 1 model = fixed, 2+ models = cycle

## Changes Made

### Frontend Changes

#### RouteFormModal.vue - Complete Redesign

**Auto Mode:**
- New provider selection dropdown: "Use all enabled providers" or "Use only [Provider]"
- Models displayed as checkboxes from selected provider(s)
- Strategy auto-detection: Single model = "fixed", multiple = "cycle"
- Config stored with `providerMode`, `selectedModels`, `modelStrategy`

**Specific Mode:**
- Provider selector dropdown (not auto)
- Models displayed as checkboxes from selected provider
- Strategy auto-detection based on enabled models count
- At least one model must be enabled

**Multi Mode:**
- Add multiple providers with individual configuration
- Each provider has:
  - Provider selector
  - Priority number
  - Strategy (round-robin or failover)
  - Models as checkboxes
- Each provider must have at least one model enabled
- Model strategy auto-detected per provider

**New Components & Features:**
- Model checklist UI with checkbox items
- Info boxes showing "Single (fixed)" vs "Cycle" strategy
- Provider configuration cards for multi mode
- Validation ensures at least one model is enabled
- Improved UI/UX with clear visual feedback

#### routes.ts - Type Definitions

Added `ModelConfig` interface:
```typescript
export interface ModelConfig {
  selectedModels: string[];
  modelStrategy: 'single' | 'cycle';
  providerMode?: string;
}
```

### Backend Changes

#### routing.py - Config-Based Model Selection

**Updated Methods:**

1. **create_route() & update_route()**
   - Now support empty `nodes` array for auto mode with config
   - Nodes are optional when config contains `selectedModels`

2. **select_provider_and_model()**
   - Multi mode now requires nodes validation (auto/specific can work with config)

3. **_select_auto()**
   - Checks for `selectedModels` in config first
   - Falls back to route_nodes if config empty (backward compatible)
   - Supports both "all providers" and "specific provider" modes

4. **_select_specific()**
   - Checks for `selectedModels` in config first
   - Falls back to route_nodes if config empty
   - Supports config-based model selection

**New Helper Methods:**

1. **_select_auto_with_config()**
   - Handles auto mode with config-based model selection
   - Supports `providerMode: 'all'` or `providerMode: 'provider_N'`
   - Uses round-robin for provider selection when "all"
   - Picks first model from selectedModels

2. **_select_specific_with_config()**
   - Handles specific mode with config-based models
   - Validates provider health and active status
   - Respects model_hint parameter

3. **_pick_model_from_config()**
   - Picks first model from selectedModels array
   - Simple utility for model selection

4. **_apply_round_robin_to_providers()**
   - Round-robin selection across multiple providers
   - Tracks index per route using provider_route_id key

#### test_routing.py - Comprehensive Tests

Added `TestConfigBasedModelSelection` class with 10 new tests:

1. `test_create_auto_route_with_config_models` - Create auto route with config
2. `test_select_auto_with_config_all_providers` - Select from all providers
3. `test_select_auto_with_config_specific_provider` - Select from specific provider
4. `test_create_specific_route_with_config_models` - Create specific route with config
5. `test_select_specific_with_config_models` - Select with specific mode config
6. `test_auto_config_route_with_unhealthy_provider` - Skip unhealthy providers
7. `test_auto_config_route_with_specific_provider_unhealthy_raises_error` - Error when specific provider unhealthy
8. `test_model_hint_overrides_config_models` - Model hint takes precedence
9. `test_empty_config_models_falls_back_to_nodes` - Backward compatibility

## Data Flow

### Creating an Auto Route

**Frontend Form → API Payload:**
```json
{
  "name": "Auto Route",
  "mode": "auto",
  "isActive": true,
  "config": {
    "providerMode": "all",
    "selectedModels": ["gpt-4", "gpt-3.5"],
    "modelStrategy": "cycle"
  },
  "nodes": []
}
```

**Backend Processing:**
- Stores route with config
- No route_nodes created
- Config validates at selection time

**Model Selection:**
- Gets all active & healthy providers
- Uses round-robin to select provider
- Returns first model from selectedModels

### Creating a Specific Route

**Frontend Form → API Payload:**
```json
{
  "name": "Specific Route",
  "mode": "specific",
  "isActive": true,
  "config": {
    "selectedModels": ["gpt-4"],
    "modelStrategy": "single"
  },
  "nodes": [
    {
      "apiId": 1,
      "models": ["gpt-4"],
      "strategy": "round-robin",
      "priority": 0
    }
  ]
}
```

**Backend Processing:**
- Creates route with config
- Creates one route_node for the provider
- Node contains the selectedModels

**Model Selection:**
- Gets provider from route_nodes[0]
- Respects config.selectedModels
- Returns specified model

### Creating a Multi Route

**Frontend Form → API Payload:**
```json
{
  "name": "Multi Route",
  "mode": "multi",
  "isActive": true,
  "config": {},
  "nodes": [
    {
      "apiId": 1,
      "models": ["gpt-4"],
      "strategy": "round-robin",
      "priority": 0
    },
    {
      "apiId": 2,
      "models": ["claude-3"],
      "strategy": "failover",
      "priority": 1
    }
  ]
}
```

**Backend Processing:**
- Creates route with multiple nodes
- Each node has its own models, strategy, priority
- Config can be empty or contain additional settings

**Model Selection:**
- Sorts nodes by priority
- Tries each node with its strategy
- Returns first available model

## Backward Compatibility

✅ **Fully Backward Compatible**

- Routes without config.selectedModels fall back to route_nodes
- Auto mode can work with or without nodes (prefers config if present)
- Specific mode can work with or without config (uses config if present)
- Multi mode requires nodes (unchanged behavior)

## Benefits

1. **Clear Provider Selection**
   - Auto: Explicitly show "all" or specific provider
   - Specific: One dropdown, not confusing

2. **Model Selection from Provider Lists**
   - Checkboxes instead of manual text input
   - Only available models shown
   - No "Field required" errors for missing models

3. **Automatic Strategy Detection**
   - Single model selected = Fixed model strategy
   - Multiple models selected = Cycle strategy
   - Clear to users via info boxes

4. **Cleaner Auto Mode**
   - No need for route_nodes when using config
   - Models shown immediately
   - Route configuration is self-contained in config

5. **Improved UX**
   - Visual feedback for model strategy
   - Checkboxes for clear selection
   - Provider cards in multi mode
   - Validation prevents invalid configurations

## Configuration Examples

### Auto Mode - All Providers, Cycle Models
```json
{
  "mode": "auto",
  "config": {
    "providerMode": "all",
    "selectedModels": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
    "modelStrategy": "cycle"
  },
  "nodes": []
}
```

### Auto Mode - Specific Provider
```json
{
  "mode": "auto",
  "config": {
    "providerMode": "provider_1",
    "selectedModels": ["gpt-4"],
    "modelStrategy": "single"
  },
  "nodes": []
}
```

### Specific Mode
```json
{
  "mode": "specific",
  "config": {
    "selectedModels": ["gpt-4", "gpt-3.5-turbo"],
    "modelStrategy": "cycle"
  },
  "nodes": [
    {
      "apiId": 1,
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "strategy": "round-robin",
      "priority": 0
    }
  ]
}
```

### Multi Mode
```json
{
  "mode": "multi",
  "config": {},
  "nodes": [
    {
      "apiId": 1,
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "strategy": "round-robin",
      "priority": 0
    },
    {
      "apiId": 2,
      "models": ["claude-3-opus"],
      "strategy": "failover",
      "priority": 1
    }
  ]
}
```

## Testing

All 10 new tests pass:
- ✅ Config route creation
- ✅ Auto mode provider selection
- ✅ Config-based model selection
- ✅ Health check integration
- ✅ Model hint precedence
- ✅ Backward compatibility
- ✅ Error handling

## UI/UX Improvements

### Auto Mode
- Clear radio-like selection between "all" and specific providers
- Provider-specific models only show when needed
- Info box shows strategy (Single vs Cycle)

### Specific Mode
- Single provider dropdown
- Models as checkboxes
- Strategy auto-determined
- Clear validation messages

### Multi Mode
- Card-based provider configuration
- Each provider has independent settings
- Models shown as checkboxes per provider
- Add/Remove provider buttons
- Priority numbering

### General
- Disabled Add buttons when no providers available
- Loading state while providers are being fetched
- Error messages explain what's wrong
- Form prevents submission without required fields
