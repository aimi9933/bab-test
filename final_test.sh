#!/bin/bash

echo "============================================"
echo "  Mistral AI 配置 - 最终测试报告"
echo "============================================"
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
    local name="$1"
    local cmd="$2"
    echo -n "测试: $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ 通过"
        ((PASSED++))
    else
        echo "❌ 失败"
        ((FAILED++))
    fi
}

# 1. 服务健康检查
echo "=== 1. 服务健康检查 ==="
test_endpoint "后端 Ping" "curl -sf http://localhost:8000/ping"
test_endpoint "前端服务" "curl -sf http://localhost:5173/"
echo ""

# 2. Provider API 测试
echo "=== 2. Provider API 测试 ==="
test_endpoint "获取 Providers 列表" "curl -sf http://localhost:8000/api/providers"
test_endpoint "获取单个 Provider" "curl -sf http://localhost:8000/api/providers/1"
test_endpoint "Provider 连接测试" "curl -sf -X POST http://localhost:8000/api/providers/1/test"
echo ""

# 3. 验证 Provider 状态
echo "=== 3. Provider 状态验证 ==="
PROVIDER_STATUS=$(curl -s http://localhost:8000/api/providers/1 | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$PROVIDER_STATUS" = "online" ]; then
    echo "✅ Provider 状态: Online"
    ((PASSED++))
else
    echo "❌ Provider 状态: $PROVIDER_STATUS"
    ((FAILED++))
fi

HEALTH_STATUS=$(curl -s http://localhost:8000/api/providers/1 | python3 -c "import sys, json; print(json.load(sys.stdin)['is_healthy'])")
if [ "$HEALTH_STATUS" = "True" ]; then
    echo "✅ 健康状态: Healthy"
    ((PASSED++))
else
    echo "❌ 健康状态: Unhealthy"
    ((FAILED++))
fi
echo ""

# 4. 验证 API 密钥加密
echo "=== 4. API 密钥安全验证 ==="
API_KEY_MASKED=$(curl -s http://localhost:8000/api/providers/1 | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key_masked'])")
if [[ $API_KEY_MASKED == *"***"* ]]; then
    echo "✅ API 密钥已脱敏: $API_KEY_MASKED"
    ((PASSED++))
else
    echo "❌ API 密钥未脱敏"
    ((FAILED++))
fi
echo ""

# 5. 验证数据持久化
echo "=== 5. 数据持久化验证 ==="
if [ -f "backend/data/providers.db" ]; then
    echo "✅ 数据库文件存在"
    ((PASSED++))
else
    echo "❌ 数据库文件不存在"
    ((FAILED++))
fi

if [ -f "backend/config_backup.json" ]; then
    echo "✅ 备份文件存在"
    ((PASSED++))
else
    echo "❌ 备份文件不存在"
    ((FAILED++))
fi
echo ""

# 6. 前端代理测试
echo "=== 6. 前端代理测试 ==="
test_endpoint "前端 API 代理" "curl -sf http://localhost:5173/api/providers"
test_endpoint "前端 Ping 代理" "curl -sf http://localhost:5173/ping"
echo ""

# 总结
echo "============================================"
echo "  测试总结"
echo "============================================"
echo "✅ 通过: $PASSED"
echo "❌ 失败: $FAILED"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 所有测试都通过了！"
    echo "项目运行正常，可以开始使用了！"
    echo ""
    echo "访问地址:"
    echo "  - 前端: http://localhost:5173"
    echo "  - 后端: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    exit 0
else
    echo "⚠️  有 $FAILED 个测试失败"
    echo "请检查日志文件了解详情"
    exit 1
fi
