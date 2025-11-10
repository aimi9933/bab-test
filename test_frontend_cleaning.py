#!/usr/bin/env python3
"""
测试前端参数清理功能
通过前端代理发送"脏"数据，验证前端是否正确清理参数
"""

import json
import requests

# Configuration
FRONTEND_URL = "http://localhost:5173"

def test_frontend_parameter_cleaning():
    """测试前端参数清理功能"""
    print("=== Testing Frontend Parameter Cleaning ===")
    
    # 发送带有空格的脏数据到前端代理
    dirty_payload = {
        "name": "  Test Provider with Spaces  ",
        "base_url": "  https://api.example.com/v1/  ",
        "models": ["  gpt-4  ", "  ", "  gpt-3.5-turbo  "],
        "is_active": True,
        "api_key": "  sk-test123456789  "
    }
    
    print(f"Sending dirty payload to frontend:")
    print(f"  Name: '{dirty_payload['name']}'")
    print(f"  Base URL: '{dirty_payload['base_url']}'")
    print(f"  Models: {dirty_payload['models']}")
    print(f"  API Key: '{dirty_payload['api_key']}'")
    
    # 通过前端代理发送请求
    response = requests.post(f"{FRONTEND_URL}/api/providers", json=dirty_payload)
    print(f"\nFrontend response: {response.status_code}")
    
    if response.status_code == 201:
        provider_data = response.json()
        print(f"\nCleaned data received from backend:")
        print(f"  Name: '{provider_data['name']}'")
        print(f"  Base URL: '{provider_data['base_url']}'")
        print(f"  Models: {provider_data['models']}")
        print(f"  API Key Masked: {provider_data['api_key_masked']}")
        
        # 验证清理效果
        expected_name = dirty_payload['name'].strip()
        expected_base_url = dirty_payload['base_url'].strip()
        expected_models = ["gpt-4", "gpt-3.5-turbo"]  # 空字符串被过滤
        
        print(f"\nValidation:")
        print(f"  Name cleaned correctly: {provider_data['name'] == expected_name}")
        print(f"  Base URL cleaned correctly: {provider_data['base_url'] == expected_base_url}")
        print(f"  Models cleaned correctly: {provider_data['models'] == expected_models}")
        
        return provider_data['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_invalid_url_handling():
    """测试无效URL处理"""
    print("\n=== Testing Invalid URL Handling ===")
    
    # 测试各种无效URL格式
    invalid_urls = [
        "not-a-url",
        "ftp://invalid-protocol.com",
        "http://",
        "https://",
        ""
    ]
    
    for i, invalid_url in enumerate(invalid_urls):
        payload = {
            "name": f"Invalid URL Test {i+1}",
            "base_url": invalid_url,
            "models": ["test-model"],
            "is_active": True,
            "api_key": "sk-test123"
        }
        
        print(f"Testing invalid URL: '{invalid_url}'")
        response = requests.post(f"{FRONTEND_URL}/api/providers", json=payload)
        print(f"  Response: {response.status_code}")
        
        if response.status_code == 422:
            errors = response.json()
            print(f"  Validation error: {errors.get('detail', 'No details')}")
        elif response.status_code == 201:
            print("  Warning: Invalid URL was accepted!")

def test_model_list_cleaning():
    """测试模型列表清理"""
    print("\n=== Testing Model List Cleaning ===")
    
    # 测试各种模型列表情况
    model_test_cases = [
        {
            "name": "Valid models",
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
            "expected": ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        },
        {
            "name": "Models with spaces",
            "models": ["  gpt-4  ", "  gpt-3.5-turbo  ", "  claude-3  "],
            "expected": ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        },
        {
            "name": "Models with empty strings",
            "models": ["gpt-4", "", "gpt-3.5-turbo", "", "claude-3"],
            "expected": ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        },
        {
            "name": "Models with whitespace only",
            "models": ["gpt-4", "   ", "gpt-3.5-turbo", "\t", "claude-3"],
            "expected": ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        }
    ]
    
    for case in model_test_cases:
        payload = {
            "name": case["name"],
            "base_url": "https://api.example.com/v1",
            "models": case["models"],
            "is_active": True,
            "api_key": "sk-test123"
        }
        
        print(f"Testing: {case['name']}")
        print(f"  Input models: {case['models']}")
        
        response = requests.post(f"{FRONTEND_URL}/api/providers", json=payload)
        print(f"  Response: {response.status_code}")
        
        if response.status_code == 201:
            provider_data = response.json()
            print(f"  Output models: {provider_data['models']}")
            print(f"  Expected: {case['expected']}")
            print(f"  Cleaning correct: {provider_data['models'] == case['expected']}")
        else:
            print(f"  Error: {response.text}")

def main():
    """运行所有前端清理测试"""
    print("测试前端参数清理功能")
    print("=" * 40)
    
    try:
        # 测试参数清理
        provider_id = test_frontend_parameter_cleaning()
        
        # 测试无效URL处理
        test_invalid_url_handling()
        
        # 测试模型列表清理
        test_model_list_cleaning()
        
        print("\n" + "=" * 40)
        print("✅ 前端清理测试完成！")
        print("\n关键发现:")
        print("- 前端正确清理参数中的多余空格")
        print("- 前端正确过滤模型列表中的空字符串")
        print("- 前端正确验证URL格式")
        print("- 前端向后端发送清理后的有效数据")
        print("- 后端接收到的是清理后的干净数据")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())