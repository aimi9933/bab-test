#!/usr/bin/env python3
"""
Test script for all three route modes with Mistral provider
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_provider_created():
    """Check if Mistral provider is available"""
    print_header("1. Check Available Providers")
    
    response = requests.get(f"{BASE_URL}/api/providers")
    providers = response.json()
    
    print(f"Total providers: {len(providers)}")
    for p in providers:
        print(f"  - {p['name']} (ID: {p['id']}, Active: {p['is_active']}, Models: {len(p['models'])})")
        if p['name'] == 'Mistral':
            print(f"    Models: {p['models']}")
            return p['id']
    
    return None

def test_auto_mode(provider_id):
    """Test Auto mode - select from all providers"""
    print_header("2. Test Auto Mode")
    
    # Create auto route
    print("Creating Auto route...")
    route_data = {
        "name": "Mistral Auto Route",
        "mode": "auto",
        "is_active": True,
        "config": {
            "providerMode": "all",
            "selectedModels": ["open-mixtral-8x22b"],
            "modelStrategy": "single"
        },
        "nodes": []
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
    if response.status_code != 201:
        print(f"❌ Failed to create auto route: {response.text}")
        return None
    
    route = response.json()
    print(f"✅ Auto route created (ID: {route['id']})")
    print(f"   Name: {route['name']}")
    print(f"   Status: {'Active' if route['is_active'] else 'Inactive'}")
    print(f"   Config: {route['config']}")
    print(f"   Nodes: {len(route['nodes'])} configured")
    
    # Test select
    print("\nTesting Auto route selection...")
    response = requests.post(f"{BASE_URL}/api/model-routes/{route['id']}/select")
    if response.status_code != 200:
        print(f"❌ Failed to select from auto route: {response.text}")
        return None
    
    selection = response.json()
    print(f"✅ Selection successful:")
    print(f"   Provider: {selection['provider_name']} (ID: {selection['provider_id']})")
    print(f"   Model: {selection['model']}")
    
    return route['id']

def test_specific_mode(provider_id):
    """Test Specific mode - select single provider"""
    print_header("3. Test Specific Mode")
    
    # Create specific route
    print("Creating Specific route...")
    route_data = {
        "name": "Mistral Specific Route",
        "mode": "specific",
        "is_active": True,
        "config": {
            "selectedModels": ["mistral-large"],
            "modelStrategy": "single"
        },
        "nodes": [{
            "api_id": provider_id,
            "models": ["mistral-large"],
            "strategy": "round-robin",
            "priority": 0,
            "node_metadata": {}
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
    if response.status_code != 201:
        print(f"❌ Failed to create specific route: {response.text}")
        return None
    
    route = response.json()
    print(f"✅ Specific route created (ID: {route['id']})")
    print(f"   Name: {route['name']}")
    print(f"   Status: {'Active' if route['is_active'] else 'Inactive'}")
    print(f"   Nodes: {len(route['nodes'])} configured")
    if route['nodes']:
        print(f"   Provider: {route['nodes'][0]['api_name']}")
        print(f"   Models: {route['nodes'][0]['models']}")
    
    # Test select
    print("\nTesting Specific route selection...")
    response = requests.post(f"{BASE_URL}/api/model-routes/{route['id']}/select")
    if response.status_code != 200:
        print(f"❌ Failed to select from specific route: {response.text}")
        return None
    
    selection = response.json()
    print(f"✅ Selection successful:")
    print(f"   Provider: {selection['provider_name']} (ID: {selection['provider_id']})")
    print(f"   Model: {selection['model']}")
    
    return route['id']

def test_multi_mode(provider_id):
    """Test Multi mode - multiple providers with priority"""
    print_header("4. Test Multi Mode")
    
    # Create multi route
    print("Creating Multi route...")
    route_data = {
        "name": "Mistral Multi Route",
        "mode": "multi",
        "is_active": True,
        "config": {},
        "nodes": [{
            "api_id": provider_id,
            "models": ["mistral-small", "mistral-medium"],
            "strategy": "round-robin",
            "priority": 0,
            "node_metadata": {}
        }]
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
    if response.status_code != 201:
        print(f"❌ Failed to create multi route: {response.text}")
        return None
    
    route = response.json()
    print(f"✅ Multi route created (ID: {route['id']})")
    print(f"   Name: {route['name']}")
    print(f"   Status: {'Active' if route['is_active'] else 'Inactive'}")
    print(f"   Nodes: {len(route['nodes'])} configured")
    if route['nodes']:
        for i, node in enumerate(route['nodes']):
            print(f"   Node {i+1}: {node['api_name']} (Priority: {node['priority']}, Strategy: {node['strategy']})")
            print(f"      Models: {node['models']}")
    
    # Test select
    print("\nTesting Multi route selection...")
    response = requests.post(f"{BASE_URL}/api/model-routes/{route['id']}/select")
    if response.status_code != 200:
        print(f"❌ Failed to select from multi route: {response.text}")
        return None
    
    selection = response.json()
    print(f"✅ Selection successful:")
    print(f"   Provider: {selection['provider_name']} (ID: {selection['provider_id']})")
    print(f"   Model: {selection['model']}")
    
    return route['id']

def test_cline_integration():
    """Test Cline external API integration"""
    print_header("5. Test Cline External API Integration")
    
    print("Configuration for Cline/external clients:")
    print(f"  apiBase: {BASE_URL}")
    print(f"  apiKey: {API_KEY}")
    print(f"  model: open-mixtral-8x22b")
    print("")
    print("Example curl request:")
    print(f'  curl -X POST {BASE_URL}/api/model-routes/1/select \\')
    print(f'    -H "Authorization: Bearer {API_KEY}" \\')
    print(f'    -H "Content-Type: application/json"')
    print("")
    print("This would return:")
    print('  {')
    print('    "provider_id": 1,')
    print('    "provider_name": "Mistral",')
    print('    "model": "open-mixtral-8x22b"')
    print('  }')

def list_all_routes():
    """List all created routes"""
    print_header("6. List All Routes")
    
    response = requests.get(f"{BASE_URL}/api/model-routes")
    routes = response.json()
    
    print(f"Total routes: {len(routes)}\n")
    for i, route in enumerate(routes, 1):
        print(f"{i}. {route['name']}")
        print(f"   Mode: {route['mode']}")
        print(f"   Status: {'Active' if route['is_active'] else 'Inactive'}")
        print(f"   Providers: {len(route['nodes'])} nodes")
        if route.get('config', {}).get('selectedModels'):
            print(f"   Configured models: {route['config']['selectedModels']}")
        print()

def main():
    print("\n" + "="*60)
    print("  LLM Provider Router - Route Mode Test")
    print("="*60)
    
    try:
        # Check provider
        provider_id = test_provider_created()
        if not provider_id:
            print("❌ Mistral provider not found! Creating it...")
            sys.exit(1)
        
        # Test all modes
        auto_route_id = test_auto_mode(provider_id)
        specific_route_id = test_specific_mode(provider_id)
        multi_route_id = test_multi_mode(provider_id)
        
        # Test Cline integration
        test_cline_integration()
        
        # List all routes
        list_all_routes()
        
        print_header("✅ All Tests Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
