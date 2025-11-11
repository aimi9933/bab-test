# 快速开始指南 🚀

## 📌 当前状态

✅ **后端**: 运行在 http://localhost:8000
✅ **前端**: 运行在 http://localhost:5173
✅ **Mistral AI**: 已配置并测试成功

## 🌐 访问应用

### 前端界面
```
http://localhost:5173
```

在浏览器中打开上面的地址即可访问完整的 Web 界面。

### 功能页面

1. **Providers 管理**: http://localhost:5173/ (首页)
   - 查看所有配置的 API providers
   - 添加、编辑、删除 providers
   - 测试连接
   - 查看健康状态

2. **路由配置**: http://localhost:5173/routes
   - 配置模型路由规则
   - 设置负载均衡策略
   - 管理 failover 策略

3. **系统监控**: http://localhost:5173/observability
   - 查看系统统计信息
   - 实时日志查看
   - 性能监控

### API 文档
```
http://localhost:8000/docs
```

FastAPI 自动生成的交互式 API 文档（Swagger UI）

## 🎯 使用 Mistral AI

### 前端界面操作

1. 打开 http://localhost:5173
2. 你会看到已配置的 "Mistral AI" provider
3. 点击 "Test" 按钮可以测试连接
4. 点击 "Edit" 可以修改配置
5. 健康状态会每60秒自动更新

### API 调用示例

#### 1. 获取 Provider 信息
```bash
curl http://localhost:8000/api/providers/1 | python3 -m json.tool
```

#### 2. 测试连接
```bash
curl -X POST http://localhost:8000/api/providers/1/test | python3 -m json.tool
```

#### 3. 添加新 Provider
```bash
curl -X POST http://localhost:8000/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Provider",
    "base_url": "https://api.example.com/v1/",
    "api_key": "your-api-key",
    "models": ["model-name"],
    "is_active": true
  }'
```

#### 4. 更新 Provider
```bash
curl -X PATCH http://localhost:8000/api/providers/1 \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

## 🔍 监控和调试

### 查看日志

#### 后端日志
```bash
tail -f /home/engine/project/backend.log
```

#### 结构化日志（JSON格式）
```bash
tail -f /home/engine/project/backend/logs/app.log
```

### 查看数据库
```bash
sqlite3 /home/engine/project/backend/data/providers.db
```

```sql
-- 查看所有 providers
SELECT * FROM external_apis;

-- 查看路由配置
SELECT * FROM model_routes;
```

### 查看备份文件
```bash
cat /home/engine/project/backend/config_backup.json | python3 -m json.tool
```

## 🛠️ 常用命令

### 重启服务

#### 重启后端
```bash
pkill -f "uvicorn backend.app.main:app"
cd /home/engine/project
source venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

#### 重启前端
```bash
pkill -f "vite"
cd /home/engine/project/frontend
npm run dev > ../frontend.log 2>&1 &
```

### 运行测试
```bash
# 运行 Mistral 测试脚本
cd /home/engine/project
./test_mistral.sh

# 运行完整测试
source venv/bin/activate
python test_mistral_endpoint.py
```

### 查看服务状态
```bash
# 检查后端
curl http://localhost:8000/ping

# 检查前端
curl http://localhost:5173/

# 检查 provider 状态
curl http://localhost:8000/api/providers
```

## 📚 配置文件位置

```
/home/engine/project/
├── backend/
│   ├── data/
│   │   └── providers.db          # SQLite 数据库
│   ├── logs/
│   │   └── app.log               # 结构化日志
│   └── config_backup.json        # 自动备份
├── frontend/
│   └── src/                      # 前端源代码
├── backend.log                   # 后端服务日志
├── frontend.log                  # 前端服务日志
└── test_mistral.sh              # 测试脚本
```

## 🎨 前端界面功能

### Providers 页面
- ✅ 查看所有 providers 列表
- ✅ 实时健康状态（Healthy/Unhealthy）
- ✅ 在线状态（Online/Degraded/Timeout/Unreachable）
- ✅ 延迟显示（毫秒）
- ✅ 失败计数
- ✅ 最后测试时间
- ✅ 模型列表
- ✅ 添加/编辑/删除操作
- ✅ 连接测试按钮
- ✅ 启用/禁用切换

### Routes 页面
- ✅ 创建模型路由
- ✅ 选择路由模式（Auto/Specific/Multi）
- ✅ 配置节点和策略
- ✅ 测试路由选择
- ✅ 查看路由状态

### Observability 页面
- ✅ 系统统计信息
- ✅ 请求计数和错误率
- ✅ 平均响应时间
- ✅ 端点性能统计
- ✅ 实时日志查看
- ✅ 自动刷新（30秒）

## 🔐 安全说明

1. **API 密钥加密**: 所有 API 密钥都使用加密存储在数据库中
2. **密钥脱敏**: 前端和日志中只显示脱敏后的密钥
3. **日志过滤**: 敏感信息自动从日志中移除
4. **HTTPS**: 生产环境建议配置 HTTPS

## ❓ 故障排除

### Provider 测试失败

1. 检查 base URL 是否正确
2. 验证 API 密钥是否有效
3. 确保网络连接正常
4. 查看后端日志了解详细错误

### 前端无法连接后端

1. 确认后端服务正在运行: `curl http://localhost:8000/ping`
2. 检查后端日志: `tail -f backend.log`
3. 验证端口没有被占用: `netstat -tuln | grep 8000`

### 健康检查不工作

1. 确认 `BACKEND_HEALTH_CHECK_ENABLED=true`
2. 检查健康检查间隔设置
3. 查看后端日志确认健康检查任务正在运行
4. 等待60秒让第一次健康检查完成

## 📞 获取帮助

- 查看完整文档: [README.md](README.md)
- 测试结果详情: [TEST_RESULTS_CN.md](TEST_RESULTS_CN.md)
- 访问信息: [ACCESS_INFO.md](ACCESS_INFO.md)
- API 文档: http://localhost:8000/docs

## 🎉 一切就绪！

你的 LLM Provider Manager 已经完全配置好了，可以开始使用了！

**下一步建议**:
1. 在前端界面中探索各项功能
2. 尝试添加更多的 LLM providers
3. 配置路由规则实现负载均衡
4. 查看监控面板了解系统状态

祝使用愉快！ 🚀
