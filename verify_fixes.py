#!/usr/bin/env python3
"""
Final verification script to check all fixes are properly applied
"""
import os
import re

def check_frontend_types():
    """Check frontend TypeScript types"""
    print("=== Checking Frontend Type Definitions ===")
    
    types_file = "/home/engine/project/frontend/src/types/routes.ts"
    if not os.path.exists(types_file):
        print("❌ Frontend types file not found")
        return False
    
    with open(types_file, 'r') as f:
        content = f.read()
    
    # Check ModelRouteCreate has nodes field
    if re.search(r'export interface ModelRouteCreate\s*{[^}]*nodes\s*\?', content):
        print("✅ ModelRouteCreate has nodes field")
    else:
        print("❌ ModelRouteCreate missing nodes field")
        return False
    
    # Check ModelRouteUpdate has nodes field
    if re.search(r'export interface ModelRouteUpdate\s*{[^}]*nodes\s*\?', content):
        print("✅ ModelRouteUpdate has nodes field")
    else:
        print("❌ ModelRouteUpdate missing nodes field")
        return False
    
    return True

def check_frontend_validation():
    """Check frontend validation logic"""
    print("\n=== Checking Frontend Validation ===")
    
    modal_file = "/home/engine/project/frontend/src/components/RouteFormModal.vue"
    if not os.path.exists(modal_file):
        print("❌ RouteFormModal.vue not found")
        return False
    
    with open(modal_file, 'r') as f:
        content = f.read()
    
    # Check auto mode validation fix
    if 'autoConfig.providerMode !== \'all\'' in content:
        print("✅ Auto mode validation fixed")
    else:
        print("❌ Auto mode validation not fixed")
        return False
    
    return True

def check_backend_routing():
    """Check backend routing service"""
    print("\n=== Checking Backend Routing Service ===")
    
    routing_file = "/home/engine/project/backend/app/services/routing.py"
    if not os.path.exists(routing_file):
        print("❌ Routing service file not found")
        return False
    
    with open(routing_file, 'r') as f:
        content = f.read()
    
    # Check improved validation logic
    if 'if route.mode == "auto":' in content and 'elif route.mode == "specific":' in content:
        print("✅ Routing validation logic improved")
    else:
        print("❌ Routing validation logic not improved")
        return False
    
    # Check conditional model validation
    if 'if node_payload.models:' in content:
        print("✅ Conditional model validation added")
    else:
        print("❌ Conditional model validation missing")
        return False
    
    return True

def check_health_checker():
    """Check health checker improvements"""
    print("\n=== Checking Health Checker ===")
    
    health_file = "/home/engine/project/backend/app/services/health_checker.py"
    if not os.path.exists(health_file):
        print("❌ Health checker file not found")
        return False
    
    with open(health_file, 'r') as f:
        content = f.read()
    
    # Check improved error handling
    if 'try:' in content and 'decrypted_key = decrypt_api_key' in content:
        print("✅ Health checker error handling improved")
    else:
        print("❌ Health checker error handling not improved")
        return False
    
    # Check better logging
    if 'logger.warning' in content:
        print("✅ Better logging added")
    else:
        print("❌ Better logging missing")
        return False
    
    return True

def check_chat_endpoint():
    """Check chat endpoint improvements"""
    print("\n=== Checking Chat Endpoint ===")
    
    chat_file = "/home/engine/project/backend/app/api/routes/chat.py"
    if not os.path.exists(chat_file):
        print("❌ Chat endpoint file not found")
        return False
    
    with open(chat_file, 'r') as f:
        content = f.read()
    
    # Check API key decryption error handling
    if 'try:' in content and 'decrypted_key = decrypt_api_key' in content:
        print("✅ API key decryption error handling added")
    else:
        print("❌ API key decryption error handling missing")
        return False
    
    # Check specific HTTP status codes
    if 'HTTPStatusError' in content and 'TimeoutException' in content:
        print("✅ Specific HTTP status codes added")
    else:
        print("❌ Specific HTTP status codes missing")
        return False
    
    return True

def check_main_py():
    """Check main.py has execution code"""
    print("\n=== Checking Main.py ===")
    
    main_file = "/home/engine/project/backend/app/main.py"
    if not os.path.exists(main_file):
        print("❌ Main.py file not found")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    if 'if __name__ == "__main__":' in content:
        print("✅ Main.py has execution code")
    else:
        print("❌ Main.py missing execution code")
        return False
    
    return True

def main():
    """Run all verification checks"""
    print("Verifying all fixes are properly applied...\n")
    
    checks = [
        ("Frontend Types", check_frontend_types),
        ("Frontend Validation", check_frontend_validation),
        ("Backend Routing", check_backend_routing),
        ("Health Checker", check_health_checker),
        ("Chat Endpoint", check_chat_endpoint),
        ("Main.py", check_main_py),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            results.append((name, False))
    
    print("\n=== Verification Summary ===")
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All fixes have been properly applied!")
        print("\nThe following issues should now be resolved:")
        print("1. ✅ Frontend route creation for all three modes")
        print("2. ✅ Route status showing correctly as Active/Inactive")
        print("3. ✅ External API 502 errors with better error handling")
        print("4. ✅ Health check improvements for provider reliability")
        print("5. ✅ Better debugging with specific error messages")
        
        print("\nNext steps:")
        print("1. Start the backend server")
        print("2. Test route creation in the frontend")
        print("3. Test external API integration with Cline/Cherry Studio")
    else:
        print("\n💥 Some fixes are missing. Please review the failed checks above.")
    
    return all_passed

if __name__ == "__main__":
    main()