#!/bin/bash

echo "============================================"
echo "  启动 LLM Provider Manager 服务"
echo "============================================"
echo ""

# 停止现有服务
echo "停止现有服务..."
pkill -f "uvicorn backend.app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# 启动后端
echo "启动后端服务..."
cd /home/engine/project
source venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "等待后端服务就绪..."
for i in {1..10}; do
    if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
        echo "✅ 后端服务就绪"
        break
    fi
    sleep 1
done

# 启动前端
echo "启动前端服务..."
cd /home/engine/project/frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "等待前端服务就绪..."
sleep 3

# 验证服务
echo ""
echo "============================================"
echo "  服务状态检查"
echo "============================================"

# 检查后端
if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
    echo "✅ 后端服务: 运行正常 (http://localhost:8000)"
else
    echo "❌ 后端服务: 启动失败"
    echo "   请查看日志: tail -f backend.log"
fi

# 检查前端
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "✅ 前端服务: 运行正常 (http://localhost:5173)"
else
    echo "❌ 前端服务: 启动失败"
    echo "   请查看日志: tail -f frontend.log"
fi

echo ""
echo "============================================"
echo "  服务已启动"
echo "============================================"
echo ""
echo "访问地址:"
echo "  - 前端界面: http://localhost:5173"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "查看日志:"
echo "  - 后端日志: tail -f backend.log"
echo "  - 前端日志: tail -f frontend.log"
echo ""
echo "停止服务:"
echo "  pkill -f 'uvicorn backend.app.main:app'"
echo "  pkill -f 'vite'"
echo ""
