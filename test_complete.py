#!/usr/bin/env python3
"""
Complete test script to verify route creation and API functionality
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_provider_creation():
    """Test creating a provider"""
    print("=== Testing Provider Creation ===")
    
    provider_data = {
        "name": "Mistral Test",
        "base_url": "https://api.mistral.ai/v1",
        "api_key": "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr",
        "models": ["open-mixtral-8x22b"],
        "is_active": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/providers", json=provider_data)
        if response.status_code == 201:
            print("✅ Provider created successfully")
            provider = response.json()
            print(f"   Provider ID: {provider['id']}")
            return provider['id']
        else:
            print(f"❌ Failed to create provider: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating provider: {e}")
        return None

def test_auto_route(provider_id):
    """Test creating auto mode route"""
    print("\n=== Testing Auto Route Creation ===")
    
    route_data = {
        "name": "Auto Test Route",
        "mode": "auto",
        "config": {
            "providerMode": "all",
            "selectedModels": ["open-mixtral-8x22b"],
            "modelStrategy": "single"
        },
        "isActive": True,
        "nodes": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
        if response.status_code == 201:
            print("✅ Auto route created successfully")
            route = response.json()
            print(f"   Route ID: {route['id']}")
            print(f"   Is Active: {route['is_active']}")
            return route['id']
        else:
            print(f"❌ Failed to create auto route: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating auto route: {e}")
        return None

def test_specific_route(provider_id):
    """Test creating specific mode route"""
    print("\n=== Testing Specific Route Creation ===")
    
    route_data = {
        "name": "Specific Test Route",
        "mode": "specific",
        "config": {
            "selectedModels": ["open-mixtral-8x22b"],
            "modelStrategy": "single"
        },
        "isActive": True,
        "nodes": [
            {
                "apiId": provider_id,
                "models": ["open-mixtral-8x22b"],
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
        if response.status_code == 201:
            print("✅ Specific route created successfully")
            route = response.json()
            print(f"   Route ID: {route['id']}")
            return route['id']
        else:
            print(f"❌ Failed to create specific route: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating specific route: {e}")
        return None

def test_multi_route(provider_id):
    """Test creating multi mode route"""
    print("\n=== Testing Multi Route Creation ===")
    
    route_data = {
        "name": "Multi Test Route",
        "mode": "multi",
        "config": {},
        "isActive": True,
        "nodes": [
            {
                "apiId": provider_id,
                "models": ["open-mixtral-8x22b"],
                "strategy": "round-robin",
                "priority": 0
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/model-routes", json=route_data)
        if response.status_code == 201:
            print("✅ Multi route created successfully")
            route = response.json()
            print(f"   Route ID: {route['id']}")
            return route['id']
        else:
            print(f"❌ Failed to create multi route: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating multi route: {e}")
        return None

def test_chat_completion():
    """Test the unified chat completion endpoint"""
    print("\n=== Testing Chat Completion ===")
    
    chat_data = {
        "model": "open-mixtral-8x22b",
        "messages": [
            {"role": "user", "content": "Hello, please say hi back"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=chat_data)
        if response.status_code == 200:
            print("✅ Chat completion successful")
            result = response.json()
            print(f"   Model: {result.get('model')}")
            print(f"   Response: {result['choices'][0]['message']['content'][:100]}...")
            return True
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error with chat completion: {e}")
        return False

def test_models_endpoint():
    """Test the models endpoint"""
    print("\n=== Testing Models Endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            print("✅ Models endpoint successful")
            result = response.json()
            models = result.get('data', [])
            print(f"   Available models: {len(models)}")
            for model in models[:3]:  # Show first 3 models
                print(f"   - {model['id']} (owned by {model['owned_by']})")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error with models endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive test of LLM Provider Router...\n")
    
    # Test provider creation
    provider_id = test_provider_creation()
    if not provider_id:
        print("❌ Cannot proceed without a provider")
        return
    
    # Wait a bit for the provider to be available
    time.sleep(2)
    
    # Test different route modes
    auto_route_id = test_auto_route(provider_id)
    specific_route_id = test_specific_route(provider_id)
    multi_route_id = test_multi_route(provider_id)
    
    # Wait for routes to be processed
    time.sleep(2)
    
    # Test API endpoints
    models_ok = test_models_endpoint()
    chat_ok = test_chat_completion()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Provider creation: {'✅' if provider_id else '❌'}")
    print(f"Auto route creation: {'✅' if auto_route_id else '❌'}")
    print(f"Specific route creation: {'✅' if specific_route_id else '❌'}")
    print(f"Multi route creation: {'✅' if multi_route_id else '❌'}")
    print(f"Models endpoint: {'✅' if models_ok else '❌'}")
    print(f"Chat completion: {'✅' if chat_ok else '❌'}")
    
    if all([provider_id, auto_route_id, specific_route_id, multi_route_id, models_ok, chat_ok]):
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()