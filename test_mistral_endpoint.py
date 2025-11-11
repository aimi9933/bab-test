#!/usr/bin/env python3
"""
Test script to verify Mistral API endpoint configuration.
"""
import sys
import httpx
from backend.app.services.providers import construct_api_url, normalize_base_url


def test_url_construction():
    """Test URL construction with and without trailing slashes."""
    print("Testing URL construction...")
    
    # Test case 1: URL without trailing slash
    base_url1 = "https://api.mistral.ai/v1"
    result1 = construct_api_url(base_url1, "/models")
    expected1 = "https://api.mistral.ai/v1/models"
    assert result1 == expected1, f"Expected {expected1}, got {result1}"
    print(f"✅ Without trailing slash: {result1}")
    
    # Test case 2: URL with trailing slash
    base_url2 = "https://api.mistral.ai/v1/"
    result2 = construct_api_url(base_url2, "/models")
    expected2 = "https://api.mistral.ai/v1/models"
    assert result2 == expected2, f"Expected {expected2}, got {result2}"
    print(f"✅ With trailing slash: {result2}")
    
    # Test case 3: Multiple trailing slashes
    base_url3 = "https://api.mistral.ai/v1///"
    result3 = construct_api_url(base_url3, "/models")
    expected3 = "https://api.mistral.ai/v1/models"
    assert result3 == expected3, f"Expected {expected3}, got {result3}"
    print(f"✅ Multiple trailing slashes: {result3}")
    
    print("\n✅ All URL construction tests passed!\n")


def test_mistral_api_connectivity():
    """Test actual connectivity to Mistral API."""
    print("Testing Mistral API connectivity...")
    
    base_url = "https://api.mistral.ai/v1/"
    api_key = "3lRFhl3we7t0uM8tF1jYCDPiQqBXvblr"
    
    # Construct URL
    url = construct_api_url(base_url, "/models")
    print(f"Testing URL: {url}")
    
    # Make request
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        print(f"Status code: {response.status_code}")
        
        if response.is_success:
            print("✅ Connection successful!")
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                print(f"✅ Found {len(data['data'])} models")
                print(f"   First model: {data['data'][0]['id']}")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def main():
    print("=" * 60)
    print("Mistral API Endpoint Configuration Test")
    print("=" * 60)
    print()
    
    # Test URL construction
    test_url_construction()
    
    # Test actual API connectivity
    success = test_mistral_api_connectivity()
    
    print()
    print("=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
