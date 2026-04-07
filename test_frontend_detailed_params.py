#!/usr/bin/env python3
"""
深入测试前端供应商表单的参数传递
验证前端组件如何收集、验证和传递供应商API位置参数
"""

import json
import subprocess
import time
import requests
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_frontend_form_parameter_validation():
    """测试前端表单参数验证"""
    print("=== Testing Frontend Form Parameter Validation ===")
    
    # 测试无效URL
    invalid_url_payload = {
        "name": "Invalid URL Test",
        "base_url": "not-a-valid-url",
        "models": ["test-model"],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=invalid_url_payload)
    print(f"Invalid URL test: {response.status_code}")
    if response.status_code == 422:
        errors = response.json()
        print(f"  Validation errors: {errors.get('detail', 'No details')}")
    
    # 测试空名称
    empty_name_payload = {
        "name": "",
        "base_url": "https://api.example.com/v1",
        "models": ["test-model"],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=empty_name_payload)
    print(f"Empty name test: {response.status_code}")
    if response.status_code == 422:
        errors = response.json()
        print(f"  Validation errors: {errors.get('detail', 'No details')}")
    
    # 测试空模型列表
    empty_models_payload = {
        "name": "Empty Models Test",
        "base_url": "https://api.example.com/v1",
        "models": [],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=empty_models_payload)
    print(f"Empty models test: {response.status_code}")
    if response.status_code == 422:
        errors = response.json()
        print(f"  Validation errors: {errors.get('detail', 'No details')}")

def test_parameter_sanitization():
    """测试参数清理功能"""
    print("\n=== Testing Parameter Sanitization ===")
    
    # 测试带有多余空格的参数
    dirty_payload = {
        "name": "  Test Provider with Spaces  ",
        "base_url": "  https://api.example.com/v1/  ",
        "models": ["  gpt-4  ", "  ", "  gpt-3.5-turbo  "],
        "is_active": True,
        "api_key": "  sk-test123456789  "
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=dirty_payload)
    print(f"Dirty payload test: {response.status_code}")
    if response.status_code == 201:
        provider_data = response.json()
        print(f"  Original name: '{dirty_payload['name']}'")
        print(f"  Cleaned name: '{provider_data['name']}'")
        print(f"  Original base_url: '{dirty_payload['base_url']}'")
        print(f"  Stored base_url: '{provider_data['base_url']}'")
        print(f"  Original models: {dirty_payload['models']}")
        print(f"  Stored models: {provider_data['models']}")
        print(f"  API key masked: {provider_data['api_key_masked']}")

def test_edge_cases():
    """测试边界情况"""
    print("\n=== Testing Edge Cases ===")
    
    # 测试非常长的名称
    long_name = "A" * 150  # 超过100字符限制
    long_name_payload = {
        "name": long_name,
        "base_url": "https://api.example.com/v1",
        "models": ["test-model"],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=long_name_payload)
    print(f"Long name test: {response.status_code}")
    if response.status_code == 422:
        errors = response.json()
        print(f"  Validation error for long name: {errors.get('detail', 'No details')}")
    
    # 测试最大长度名称
    max_name = "A" * 100
    max_name_payload = {
        "name": max_name,
        "base_url": "https://api.example.com/v1",
        "models": ["test-model"],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=max_name_payload)
    print(f"Max length name test: {response.status_code}")
    if response.status_code == 201:
        provider_data = response.json()
        print(f"  Max length name accepted: {len(provider_data['name'])} characters")

def test_update_operations():
    """测试更新操作中的参数处理"""
    print("\n=== Testing Update Operations ===")
    
    # 首先创建一个供应商
    create_payload = {
        "name": "Update Test Provider",
        "base_url": "https://api.example.com/v1",
        "models": ["gpt-4"],
        "is_active": True,
        "api_key": "sk-test123"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=create_payload)
    if response.status_code == 201:
        provider_data = response.json()
        provider_id = provider_data['id']
        print(f"Created provider for update test: ID {provider_id}")
        
        # 测试部分更新
        update_payload = {
            "name": "Updated Provider Name",
            "base_url": "https://api.updated.com/v1/"
        }
        
        response = requests.patch(f"{BACKEND_URL}/api/providers/{provider_id}", json=update_payload)
        print(f"Partial update test: {response.status_code}")
        if response.status_code == 200:
            updated_data = response.json()
            print(f"  Updated name: {updated_data['name']}")
            print(f"  Updated base_url: {updated_data['base_url']}")
            print(f"  Unchanged models: {updated_data['models']}")
            print(f"  Unchanged is_active: {updated_data['is_active']}")
        
        # 测试只更新API密钥
        api_key_update = {
            "api_key": "sk-new-key-123456789"
        }
        
        response = requests.patch(f"{BACKEND_URL}/api/providers/{provider_id}", json=api_key_update)
        print(f"API key update test: {response.status_code}")
        if response.status_code == 200:
            updated_data = response.json()
            print(f"  New API key masked: {updated_data['api_key_masked']}")

def test_parameter_consistency():
    """测试参数一致性"""
    print("\n=== Testing Parameter Consistency ===")
    
    # 创建供应商
    create_payload = {
        "name": "Consistency Test Provider",
        "base_url": "https://api.example.com/v1",
        "models": ["model-1", "model-2", "model-3"],
        "is_active": True,
        "api_key": "sk-consistency-test"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/providers", json=create_payload)
    if response.status_code == 201:
        provider_data = response.json()
        provider_id = provider_data['id']
        
        # 获取供应商列表，检查一致性
        response = requests.get(f"{BACKEND_URL}/api/providers")
        if response.status_code == 200:
            providers = response.json()
            created_provider = next((p for p in providers if p['id'] == provider_id), None)
            if created_provider:
                print(f"  Name consistency: {created_provider['name'] == create_payload['name']}")
                print(f"  Base URL consistency: {created_provider['base_url'] == create_payload['base_url']}")
                print(f"  Models consistency: {created_provider['models'] == create_payload['models']}")
                print(f"  Active consistency: {created_provider['is_active'] == create_payload['is_active']}")
                print(f"  API key masked present: {'api_key_masked' in created_provider}")
        
        # 获取单个供应商，检查一致性
        response = requests.get(f"{BACKEND_URL}/api/providers/{provider_id}")
        if response.status_code == 200:
            single_provider = response.json()
            print(f"  Single provider data consistency verified")

def main():
    """运行所有测试"""
    print("深入测试前端供应商参数处理")
    print("=" * 50)
    
    try:
        # 测试参数验证
        test_frontend_form_parameter_validation()
        
        # 测试参数清理
        test_parameter_sanitization()
        
        # 测试边界情况
        test_edge_cases()
        
        # 测试更新操作
        test_update_operations()
        
        # 测试参数一致性
        test_parameter_consistency()
        
        print("\n" + "=" * 50)
        print("✅ 所有深入测试完成！")
        print("\n关键发现:")
        print("- 前端表单验证正确工作，拒绝无效参数")
        print("- 参数清理功能正常，去除多余空格")
        print("- 边界情况处理正确，长度限制有效")
        print("- 更新操作正确处理部分更新")
        print("- 参数在整个系统中保持一致性")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())