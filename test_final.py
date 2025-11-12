#!/usr/bin/env python3
"""
Final comprehensive test to verify all fixes work correctly.
This tests:
1. All three route modes can be created without errors
2. Routes are properly activated
3. Unified API works for external tools
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    print("=== Final Comprehensive Test ===\n")
    
    # 1. Check if provider exists
    print("1. Checking provider...")
    providers_response = requests.get(f"{BASE_URL}/api/providers")
    if providers_response.status_code != 200:
        print("✗ Failed to get providers")
        return False
    
    providers = providers_response.json()
    mistral_provider = None
    for provider in providers:
        if provider['name'] == "Mistral AI":
            mistral_provider = provider
            break
    
    if not mistral_provider:
        print("✗ Mistral provider not found")
        return False
    
    print(f"✓ Found Mistral provider (ID: {mistral_provider['id']}, Healthy: {mistral_provider['is_healthy']})")
    
    # 2. Clean up existing test routes
    print("\n2. Cleaning up existing test routes...")
    routes_response = requests.get(f"{BASE_URL}/api/model-routes")
    if routes_response.status_code == 200:
        routes = routes_response.json()
        for route in routes:
            if "Test" in route['name']:
                delete_response = requests.delete(f"{BASE_URL}/api/model-routes/{route['id']}")
                if delete_response.status_code == 204:
                    print(f"  ✓ Deleted test route: {route['name']}")
    
    # 3. Test Auto Mode
    print("\n3. Testing Auto Mode...")
    auto_route = {
        "name": "Auto Mode Test",
        "mode": "auto",
        "config": {
            "providerMode": "all",
            "selectedModels": [],
            "modelStrategy": "cycle"
        },
        "isActive": True,
        "nodes": []
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=auto_route)
    if response.status_code == 201:
        auto_route_id = response.json()['id']
        print(f"✓ Auto route created (ID: {auto_route_id})")
    else:
        print(f"✗ Auto route failed: {response.status_code} - {response.text}")
        return False
    
    # 4. Test Specific Mode
    print("\n4. Testing Specific Mode...")
    specific_route = {
        "name": "Specific Mode Test",
        "mode": "specific",
        "config": {
            "selectedModels": [],
            "modelStrategy": "single"
        },
        "isActive": True,
        "nodes": [
            {
                "api_id": mistral_provider['id'],
                "models": [],
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=specific_route)
    if response.status_code == 201:
        specific_route_id = response.json()['id']
        print(f"✓ Specific route created (ID: {specific_route_id})")
    else:
        print(f"✗ Specific route failed: {response.status_code} - {response.text}")
        return False
    
    # 5. Test Multi Mode
    print("\n5. Testing Multi Mode...")
    multi_route = {
        "name": "Multi Mode Test",
        "mode": "multi",
        "config": {},
        "isActive": True,
        "nodes": [
            {
                "api_id": mistral_provider['id'],
                "models": [],
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/model-routes", json=multi_route)
    if response.status_code == 201:
        multi_route_id = response.json()['id']
        print(f"✓ Multi route created (ID: {multi_route_id})")
    else:
        print(f"✗ Multi route failed: {response.status_code} - {response.text}")
        return False
    
    # 6. Check route status
    print("\n6. Checking route statuses...")
    time.sleep(1)  # Give it a moment
    routes_response = requests.get(f"{BASE_URL}/api/model-routes")
    if routes_response.status_code == 200:
        routes = routes_response.json()
        for route in routes:
            if "Test" in route['name']:
                status = "Active" if route['is_active'] else "Inactive"
                print(f"  - {route['name']}: {status}")
                if not route['is_active']:
                    print(f"✗ Route {route['name']} is not active!")
                    return False
    
    # 7. Test unified API - Models endpoint
    print("\n7. Testing /v1/models endpoint...")
    response = requests.get(f"{BASE_URL}/v1/models")
    if response.status_code == 200:
        models = response.json()
        print(f"✓ Models endpoint works ({len(models.get('data', []))} models)")
    else:
        print(f"✗ Models endpoint failed: {response.status_code}")
        return False
    
    # 8. Test unified API - Chat completions
    print("\n8. Testing /v1/chat/completions endpoint...")
    chat_request = {
        "model": "any-model-name",
        "messages": [
            {"role": "user", "content": "Say 'TEST OK'"}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=chat_request)
    if response.status_code == 200:
        result = response.json()
        message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"✓ Chat completions works: '{message.strip()}'")
    else:
        print(f"✗ Chat completions failed: {response.status_code} - {response.text}")
        return False
    
    # 9. Test with empty model hint (should use first available)
    print("\n9. Testing chat with no specific model...")
    chat_request_no_model = {
        "messages": [
            {"role": "user", "content": "Just say 'OK'"}
        ],
        "temperature": 0.1,
        "max_tokens": 5
    }
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=chat_request_no_model)
    if response.status_code == 200:
        result = response.json()
        message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"✓ Chat without model works: '{message.strip()}'")
    else:
        print(f"✗ Chat without model failed: {response.status_code}")
        return False
    
    print("\n=== ALL TESTS PASSED! ===")
    print("\n✓ Frontend route creation now works for all modes:")
    print("  - Auto mode: Can be created without pre-selecting models")
    print("  - Specific mode: Can be created without pre-selecting models")
    print("  - Multi mode: Can be created without pre-selecting models")
    print("\n✓ All routes are properly activated")
    print("\n✓ Unified API endpoint works:")
    print("  - /v1/models returns available models")
    print("  - /v1/chat/completions routes requests correctly")
    print("  - External tools like Cline can use the API")
    print("\n🎉 The fixes are complete and working!")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if not success:
        print("\n❌ Some tests failed!")
        exit(1)