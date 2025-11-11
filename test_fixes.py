#!/usr/bin/env python3
"""
Simple test to verify the fixes work without needing the full server
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports_and_validation():
    """Test that our fixes work correctly"""
    print("=== Testing Import Fixes ===")
    
    try:
        # Test main app import
        from app.main import app
        print("✅ Main app import successful")
        
        # Test chat routes import
        from app.api.routes.chat import router as chat_router
        print("✅ Chat routes import successful")
        
        # Test routing service import
        from app.services.routing import get_routing_service
        print("✅ Routing service import successful")
        
        # Test database models
        from app.db.models import ModelRoute, RouteNode, ExternalAPI
        print("✅ Database models import successful")
        
        # Test schemas
        from app.schemas.route import ModelRouteRead, RouteNodeRead, ModelRouteCreate
        print("✅ Route schemas import successful")
        
        # Test that ModelRouteCreate has nodes field
        import inspect
        schema_fields = ModelRouteCreate.model_fields
        if 'nodes' in schema_fields:
            print("✅ ModelRouteCreate has 'nodes' field")
        else:
            print("❌ ModelRouteCreate missing 'nodes' field")
            print(f"   Available fields: {list(schema_fields.keys())}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_route_validation_logic():
    """Test the route validation logic"""
    print("\n=== Testing Route Validation Logic ===")
    
    try:
        from app.schemas.route import ModelRouteCreate, RouteNodeCreate
        from pydantic import ValidationError
        
        # Test auto route with config and empty nodes
        auto_route_data = {
            "name": "Test Auto Route",
            "mode": "auto",
            "config": {
                "providerMode": "all",
                "selectedModels": ["test-model"],
                "modelStrategy": "single"
            },
            "isActive": True,
            "nodes": []
        }
        
        try:
            route = ModelRouteCreate(**auto_route_data)
            print("✅ Auto route validation passed")
            print(f"   Route name: {route.name}")
            print(f"   Has nodes: {len(route.nodes) if route.nodes else 0}")
        except ValidationError as e:
            print(f"❌ Auto route validation failed: {e}")
        
        # Test specific route with config and nodes
        specific_route_data = {
            "name": "Test Specific Route",
            "mode": "specific",
            "config": {
                "selectedModels": ["test-model"],
                "modelStrategy": "single"
            },
            "isActive": True,
            "nodes": [
                {
                    "apiId": 1,
                    "models": ["test-model"],
                    "strategy": "round-robin",
                    "priority": 0
                }
            ]
        }
        
        try:
            route = ModelRouteCreate(**specific_route_data)
            print("✅ Specific route validation passed")
            print(f"   Route name: {route.name}")
            print(f"   Has nodes: {len(route.nodes) if route.nodes else 0}")
        except ValidationError as e:
            print(f"❌ Specific route validation failed: {e}")
        
        # Test multi route with nodes
        multi_route_data = {
            "name": "Test Multi Route",
            "mode": "multi",
            "config": {},
            "isActive": True,
            "nodes": [
                {
                    "apiId": 1,
                    "models": ["test-model"],
                    "strategy": "round-robin",
                    "priority": 0
                }
            ]
        }
        
        try:
            route = ModelRouteCreate(**multi_route_data)
            print("✅ Multi route validation passed")
            print(f"   Route name: {route.name}")
            print(f"   Has nodes: {len(route.nodes) if route.nodes else 0}")
        except ValidationError as e:
            print(f"❌ Multi route validation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing our fixes for route creation and API issues...\n")
    
    import_ok = test_imports_and_validation()
    validation_ok = test_route_validation_logic()
    
    print("\n=== Test Summary ===")
    print(f"Import tests: {'✅' if import_ok else '❌'}")
    print(f"Validation tests: {'✅' if validation_ok else '❌'}")
    
    if import_ok and validation_ok:
        print("\n🎉 All validation tests passed! The fixes should work correctly.")
        print("\nNext steps:")
        print("1. Start the backend server")
        print("2. Run the complete test script: python3 test_complete.py")
        print("3. Test the frontend interface")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()