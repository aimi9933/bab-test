#!/usr/bin/env python3
"""
Create a test provider for Mistral API
"""
import requests
import json

# Create provider data
provider_data = {
    "name": "Mistral Test",
    "base_url": "https://api.mistral.ai/v1",
    "api_key": "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr",
    "models": ["open-mixtral-8x22b"],
    "is_active": True
}

try:
    response = requests.post("http://localhost:8000/api/providers", json=provider_data)
    if response.status_code == 201:
        print("✅ Provider created successfully")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed to create provider: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")