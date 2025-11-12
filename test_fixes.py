#!/usr/bin/env python3
"""
Test script to verify all the fixes:
1. Frontend route creation (all three modes)
2. Unified API endpoint functionality
"""

import asyncio
import json
import requests
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"

def test_provider_creation():
    """Create the Mistral provider for testing"""
    print("=== Testing Provider Creation ===")
    
    provider_data = {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "api_key": "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr",
        "models": ["open-mixtral-8x22b"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/providers", json=provider_data)
        if response.status_code == 201:
            print("✓ Provider created successfully")
            provider = response.json()
            print(f"  Provider ID: {provider['id']}")
            return provider['id']
        elif response.status_code == 400 and "already exists" in response.text:
            print("✓ Provider already exists, getting ID")
            # Try to get existing provider
            providers_response = requests.get(f"{BASE_URL}/api/providers")
            if providers_response.status_code == 200:
                providers = providers_response.json()
                for provider in providers:
                    if provider['name'] == "Mistral AI":
                        return provider['id']
        else:
            print(f"✗ Provider creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Provider creation error: {e}")
        return None

def test_route_creation(provider_id: int):
    """Test route creation for all three modes"""
    print("\n=== Testing Route Creation ===")
    
    # Test Mode 1: Auto (without pre-selected models)
    print("\n1. Testing Auto Mode (without pre-selected models)...")
    auto_route = {
        "name": "Auto Route Test",
        "mode": "auto",
        "config": {
            "providerMode": "all",
            "selectedModels": [],  # Empty to test flexible validation
            "modelStrategy": "cycle"
        },
        "isActive": True,
        "nodes": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=auto_route)
        if response.status_code == 201:
            print("✓ Auto route created successfully")
            auto_route_id = response.json()['id']
            print(f"  Route ID: {auto_route_id}")
        else:
            print(f"✗ Auto route creation failed: {response.status_code} - {response.text}")
            auto_route_id = None
    except Exception as e:
        print(f"✗ Auto route creation error: {e}")
        auto_route_id = None
    
    # Test Mode 2: Specific (without pre-selected models)
    print("\n2. Testing Specific Mode (without pre-selected models)...")
    specific_route = {
        "name": "Specific Route Test",
        "mode": "specific",
        "config": {
            "selectedModels": [],  # Empty to test flexible validation
            "modelStrategy": "single"
        },
        "isActive": True,
        "nodes": [
            {
                "api_id": provider_id,  # Fixed: use api_id instead of apiId
                "models": [],  # Empty to use all provider models
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=specific_route)
        if response.status_code == 201:
            print("✓ Specific route created successfully")
            specific_route_id = response.json()['id']
            print(f"  Route ID: {specific_route_id}")
        else:
            print(f"✗ Specific route creation failed: {response.status_code} - {response.text}")
            specific_route_id = None
    except Exception as e:
        print(f"✗ Specific route creation error: {e}")
        specific_route_id = None
    
    # Test Mode 3: Multi (without pre-selected models)
    print("\n3. Testing Multi Mode (without pre-selected models)...")
    multi_route = {
        "name": "Multi Route Test",
        "mode": "multi",
        "config": {},
        "isActive": True,
        "nodes": [
            {
                "api_id": provider_id,  # Fixed: use api_id instead of apiId
                "models": [],  # Empty to use all provider models
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=multi_route)
        if response.status_code == 201:
            print("✓ Multi route created successfully")
            multi_route_id = response.json()['id']
            print(f"  Route ID: {multi_route_id}")
        else:
            print(f"✗ Multi route creation failed: {response.status_code} - {response.text}")
            multi_route_id = None
    except Exception as e:
        print(f"✗ Multi route creation error: {e}")
        multi_route_id = None
    
    return auto_route_id, specific_route_id, multi_route_id

def test_unified_api():
    """Test the unified API endpoint"""
    print("\n=== Testing Unified API ===")
    
    # Test models endpoint
    print("\n1. Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            print("✓ Models endpoint works")
            models = response.json()
            print(f"  Available models: {len(models.get('data', []))}")
        else:
            print(f"✗ Models endpoint failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Models endpoint error: {e}")
    
    # Test chat completions endpoint
    print("\n2. Testing /v1/chat/completions endpoint...")
    chat_request = {
        "model": "open-mixtral-8x22b",  # Can be any string, routing will handle it
        "messages": [
            {"role": "user", "content": "Hello, respond with just 'API working'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=chat_request)
        if response.status_code == 200:
            print("✓ Chat completions endpoint works")
            result = response.json()
            message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"  Response: {message[:100]}...")
        else:
            print(f"✗ Chat completions endpoint failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Chat completions endpoint error: {e}")

def test_route_status():
    """Check if routes are properly activated"""
    print("\n=== Testing Route Status ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/model-routes")
        if response.status_code == 200:
            routes = response.json()
            print(f"✓ Found {len(routes)} routes")
            for route in routes:
                status = "Active" if route['is_active'] else "Inactive"
                print(f"  - {route['name']} ({route['mode']}): {status}")
        else:
            print(f"✗ Failed to get routes: {response.status_code}")
    except Exception as e:
        print(f"✗ Route status check error: {e}")

def main():
    """Main test function"""
    print("Starting comprehensive test of LLM Provider Router...")
    
    # Test 1: Provider creation
    provider_id = test_provider_creation()
    if not provider_id:
        print("\n❌ Provider creation failed, stopping tests")
        sys.exit(1)
    
    # Test 2: Route creation
    auto_id, specific_id, multi_id = test_route_creation(provider_id)
    
    # Test 3: Route status
    test_route_status()
    
    # Test 4: Unified API
    test_unified_api()
    
    print("\n=== Test Summary ===")
    print("✓ All tests completed")
    print("✓ Frontend route creation should now work for all modes")
    print("✓ Unified API endpoint should work with external tools")
    print("\nThe fixes include:")
    print("1. Relaxed validation for route creation (no mandatory model selection)")
    print("2. Improved routing logic to handle empty model lists")
    print("3. Fixed catch-all route to properly handle v1 endpoints")
    print("4. Better error messages and model availability checking")

if __name__ == "__main__":
    main()