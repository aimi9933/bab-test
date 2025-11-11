#!/usr/bin/env python3
"""
Basic test script to verify the application can start without import errors.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all imports work correctly."""
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
        from app.schemas.route import ModelRouteRead, RouteNodeRead
        print("✅ Route schemas import successful")
        
        # Test that app can be created
        print(f"✅ App title: {app.title}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing basic imports and app creation...")
    success = test_imports()
    if success:
        print("\n🎉 All tests passed! The application should start correctly.")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)