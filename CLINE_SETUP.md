# Cline Configuration Guide

This guide explains how to configure Cline (or any OpenAI-compatible client) to use the unified API endpoint provided by this LLM Gateway system.

## Prerequisites

1. You have the LLM Gateway system running and accessible
2. You have configured at least one provider and one route
3. The route is active and has healthy providers

## Configuration Steps

### 1. Add API Providers

First, add your LLM providers through the web interface:

1. Navigate to the Providers page
2. Click "Add provider"
3. Configure each provider with:
   - Name (e.g., "OpenAI", "Mistral", "Anthropic")
   - Base URL (e.g., `https://api.openai.com/v1`)
   - API Key
   - Available models (e.g., `gpt-4`, `gpt-3.5-turbo`)
   - Set as active

### 2. Configure Routes

Next, set up routing to determine how requests are distributed:

1. Navigate to the Routes page
2. Click "Add route"
3. Choose a routing mode:
   - **Auto**: Round-robin through all providers
   - **Specific**: Use provider based on model hint
   - **Multi**: Priority-based with failover
4. Set the route as active

### 3. Configure Cline

In Cline (or any OpenAI-compatible client), use these settings:

#### API Base URL
```
http://your-gateway-host:8000
```

#### API Key
```
any-key-or-empty
```
Note: The gateway doesn't validate API keys for external clients by default. You can add authentication if needed.

#### Model Selection
- Leave model field empty to use automatic routing
- Or specify a model name that exists in your providers

## Example Cline Configuration

```json
{
  "apiBase": "http://localhost:8000",
  "apiKey": "gateway-key",
  "model": "gpt-4"  // Optional - leave empty for auto-routing
}
```

## Routing Behavior

### Auto Mode
- Requests are distributed evenly across all healthy providers
- Good for load balancing and cost optimization

### Specific Mode
- Specify a model name in your request
- Gateway routes to the provider that supports that model
- Example: `model: "gpt-4"` routes to the provider with gpt-4

### Multi Mode
- Providers are tried in priority order
- If primary provider fails, fails over to secondary
- Supports different strategies per provider

## Testing the Configuration

1. Test your providers individually using the "Test" button
2. Test route selection using the "Test" button on the Routes page
3. Make a simple API call:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Troubleshooting

### "No active routes configured"
- Make sure you have created at least one route
- Ensure the route is marked as active

### "Provider is currently unhealthy"
- Check the provider status on the Providers page
- Test the provider connection
- Check health check logs in the Observability page

### "Routing failed"
- Verify your route configuration matches your providers
- Check that models specified in requests exist in your providers
- Review route state using the "State" button

### Connection Issues
- Ensure the gateway is accessible from your client
- Check firewall settings
- Verify the correct port (default: 8000)

## Advanced Configuration

### Custom Authentication
You can add API key validation by modifying the chat endpoint to check against a database of allowed clients.

### Model Mapping
Create custom model mappings to translate between different provider model names.

### Request/Response Transformation
Add custom logic to transform requests or responses for specific providers.

## Monitoring

Use the Observability page to monitor:
- Request volumes and response times
- Error rates and types
- Provider health status
- Recent request logs

This helps ensure your gateway is performing optimally and quickly identify any issues.