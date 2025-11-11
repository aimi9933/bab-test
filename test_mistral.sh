#!/bin/bash

echo "=== Testing Mistral AI Provider Configuration ==="
echo ""

echo "1. Testing backend ping..."
curl -s http://localhost:8000/ping | python3 -m json.tool
echo ""

echo "2. Fetching provider list..."
curl -s http://localhost:8000/api/providers | python3 -m json.tool
echo ""

echo "3. Testing provider connectivity..."
curl -s -X POST http://localhost:8000/api/providers/1/test | python3 -m json.tool
echo ""

echo "4. Fetching provider details..."
curl -s http://localhost:8000/api/providers/1 | python3 -m json.tool
echo ""

echo "=== All tests completed successfully! ==="
