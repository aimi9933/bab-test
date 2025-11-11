#!/usr/bin/env python3
"""
Test Cline-style external client integration
Simulates how Cline would call the unified routing endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"
MISTRAL_API_KEY = "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr"

def test_cline_use_case():
    """
    Simulate how Cline would use the router:
    1. Configure apiBase, apiKey, and model
    2. Call the router to get the best provider and model
    3. Use that information to call the actual provider
    """
    
    print("\n" + "="*70)
    print("  CLINE EXTERNAL CLIENT INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Step 1: Show configuration
    print("STEP 1: Configuration for Cline Client")
    print("-" * 70)
    print("""
Cline configuration:
  apiBase: http://localhost:8000
  apiKey: 3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr
  model: open-mixtral-8x22b (any value, router decides)

The router is configured with routes that map models to providers.
""")
    
    # Step 2: Get routes
    print("STEP 2: List Available Routes")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/api/model-routes")
    routes = response.json()
    print(f"Available routes: {len(routes)}")
    for route in routes:
        print(f"  - {route['name']}: {route['mode']} mode, Status: {'Active' if route['is_active'] else 'Inactive'}")
    
    # Step 3: Select provider for a specific route
    print("\nSTEP 3: Query Routes for Provider Selection")
    print("-" * 70)
    
    test_routes = [r for r in routes if r['is_active']][:3]
    for route in test_routes:
        print(f"\nRoute: {route['name']} ({route['mode']} mode)")
        
        # Call select endpoint
        response = requests.post(f"{BASE_URL}/api/model-routes/{route['id']}/select")
        if response.status_code == 200:
            selection = response.json()
            print(f"  ✅ Provider: {selection['provider_name']}")
            print(f"     Model: {selection['model']}")
            print(f"     Provider ID: {selection['provider_id']}")
        else:
            print(f"  ❌ Error: {response.text}")
    
    # Step 4: Simulate actual request to provider
    print("\n\nSTEP 4: Simulate Provider Endpoint Call")
    print("-" * 70)
    print("""
Once router returns the provider and model, Cline would:

1. Get the provider's API endpoint:
   - For Mistral: https://api.mistral.ai/v1/
   
2. Call the provider's models endpoint:
   curl https://api.mistral.ai/v1/models \\
     -H "Authorization: Bearer {api_key}"

3. Use the model for chat completions:
   curl https://api.mistral.ai/v1/chat/completions \\
     -H "Authorization: Bearer {api_key}" \\
     -H "Content-Type: application/json" \\
     -d '{
       "model": "open-mixtral-8x22b",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
""")
    
    # Step 5: Show routing strategy details
    print("\nSTEP 5: Routing Strategy Details")
    print("-" * 70)
    
    auto_route = next((r for r in routes if r['mode'] == 'auto' and r['is_active']), None)
    if auto_route:
        print(f"\nAuto Route: {auto_route['name']}")
        print(f"  Config: {json.dumps(auto_route['config'], indent=2)}")
        print("  Behavior: Cycles through all active providers with configured models")
    
    specific_route = next((r for r in routes if r['mode'] == 'specific' and r['is_active']), None)
    if specific_route:
        print(f"\nSpecific Route: {specific_route['name']}")
        print(f"  Config: {json.dumps(specific_route['config'], indent=2)}")
        if specific_route['nodes']:
            print(f"  Provider: {specific_route['nodes'][0]['api_name']}")
            print(f"  Models: {specific_route['nodes'][0]['models']}")
        print("  Behavior: Always uses specified provider")
    
    multi_route = next((r for r in routes if r['mode'] == 'multi' and r['is_active']), None)
    if multi_route:
        print(f"\nMulti Route: {multi_route['name']}")
        print(f"  Nodes configured: {len(multi_route['nodes'])}")
        for i, node in enumerate(multi_route['nodes'], 1):
            print(f"  Node {i}: {node['api_name']} (Priority: {node['priority']}, Strategy: {node['strategy']})")
        print("  Behavior: Uses priority and failover strategy")
    
    # Step 6: Show complete request/response example
    print("\n\nSTEP 6: Complete Request/Response Example")
    print("-" * 70)
    
    route_id = auto_route['id'] if auto_route else routes[0]['id']
    response = requests.post(f"{BASE_URL}/api/model-routes/{route_id}/select")
    selection = response.json()
    
    print(f"""
Request:
  POST {BASE_URL}/api/model-routes/{route_id}/select

Response:
{json.dumps(selection, indent=2)}

Cline would then:
  1. Use provider_id={selection['provider_id']} to get provider details
  2. Use model='{selection['model']}' for the API call
  3. Continue with the chat completion request
""")
    
    print("="*70)
    print("✅ CLINE INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_cline_use_case()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
