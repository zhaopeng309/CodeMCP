# Tasks API 认证指南

## 问题描述
用户报告 `/tasks` 端点需要认证，但不知道正确的认证方式。

## 解决方案

### 1. 认证机制
CodeMCP API 使用 Bearer Token 认证。默认的演示令牌是 `demo-token`。

### 2. 正确的认证头
在 HTTP 请求头中添加：
```
Authorization: Bearer demo-token
```

### 3. 哪些端点需要认证

根据 `src/codemcp/api/routes/tasks.py` 的分析：

**需要认证的端点（使用 `ProtectedDeps["current_user"]`）：**
- `POST /tasks/` - 创建新任务
- `PUT /tasks/{task_id}` - 更新任务
- `DELETE /tasks/{task_id}` - 删除任务
- `POST /tasks/{task_id}/execute` - 执行任务
- `GET /tasks/next` - 获取下一个待执行任务
- `POST /tasks/{task_id}/cancel` - 取消任务

**不需要认证的端点：**
- `GET /tasks/` - 获取任务列表（支持过滤）
- `GET /tasks/{task_id}` - 获取任务详情
- `GET /tasks/status/{task_id}` - 获取任务状态信息

### 4. API 路径前缀
注意：API 路径前缀取决于 `.env` 文件中的 `API_PREFIX` 设置：
- 如果 `API_PREFIX=`（空），则路径为 `/tasks/`
- 如果 `API_PREFIX=/api/v1`，则路径为 `/api/v1/tasks/`

### 5. 使用示例

#### 使用 curl
```bash
# 获取任务列表（不需要认证）
curl http://localhost:8000/tasks/

# 创建新任务（需要认证）
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "command": "echo Hello World",
    "feature_id": "test-feature-001",
    "description": "测试任务"
  }'

# 获取下一个任务（需要认证）
curl -H "Authorization: Bearer demo-token" http://localhost:8000/tasks/next
```

#### 使用 Python requests
```python
import requests

# 配置
BASE_URL = "http://localhost:8000"
TOKEN = "demo-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 获取任务列表（不需要认证）
response = requests.get(f"{BASE_URL}/tasks/")
print(f"任务列表: {response.status_code} - {response.text}")

# 创建新任务（需要认证）
task_data = {
    "command": "pytest tests/test_example.py",
    "feature_id": "feature-001",
    "description": "运行测试"
}
response = requests.post(
    f"{BASE_URL}/tasks/",
    json=task_data,
    headers=HEADERS
)
print(f"创建任务: {response.status_code} - {response.text}")

# 测试无效令牌
response = requests.post(
    f"{BASE_URL}/tasks/",
    json=task_data,
    headers={"Authorization": "Bearer wrong-token"}
)
print(f"无效令牌: {response.status_code} - {response.text}")
```

#### 使用 Python 测试脚本
```python
import requests

def test_authentication():
    """测试认证机制"""
    base_url = "http://localhost:8000"
    
    print("1. 测试没有认证令牌（应该返回 401）")
    response = requests.post(
        f"{base_url}/tasks/",
        json={"command": "echo test", "feature_id": "test"}
    )
    print(f"   状态码: {response.status_code}, 响应: {response.text}")
    
    print("\n2. 测试错误的认证令牌（应该返回 401）")
    response = requests.post(
        f"{base_url}/tasks/",
        json={"command": "echo test", "feature_id": "test"},
        headers={"Authorization": "Bearer wrong-token"}
    )
    print(f"   状态码: {response.status_code}, 响应: {response.text}")
    
    print("\n3. 测试正确的认证令牌（应该成功或返回其他错误）")
    response = requests.post(
        f"{base_url}/tasks/",
        json={"command": "echo test", "feature_id": "test"},
        headers={"Authorization": "Bearer demo-token"}
    )
    print(f"   状态码: {response.status_code}, 响应: {response.text}")
    
    print("\n4. 测试不需要认证的端点")
    response = requests.get(f"{base_url}/tasks/")
    print(f"   状态码: {response.status_code}, 响应: {response.text}")

if __name__ == "__main__":
    test_authentication()
```

### 6. 常见错误

#### 错误 1: 401 Unauthorized
```
{"detail":"缺少认证凭证"}
```
**原因**: 没有提供认证头
**解决方案**: 添加 `Authorization: Bearer demo-token` 头

#### 错误 2: 401 Unauthorized
```
{"detail":"无效的认证凭证"}
```
**原因**: 提供了错误的令牌
**解决方案**: 使用正确的令牌 `demo-token`

#### 错误 3: 404 Not Found
```
{"detail":"Not Found"}
```
**原因**: API 路径不正确
**解决方案**: 检查 `.env` 文件中的 `API_PREFIX` 设置，或直接尝试 `/tasks/`

### 7. 生产环境配置

对于生产环境，应该修改 `src/codemcp/api/dependencies.py` 中的 `verify_token` 函数，使用更安全的认证机制（如 JWT）。

当前实现（简化版本）：
```python
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少认证凭证")
    
    token = credentials.credentials
    
    # 简化实现：实际项目需要验证 JWT 或其他令牌
    if token != "demo-token":
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    
    return "demo-user"
```

### 8. 故障排除步骤

1. **检查服务器是否运行**
   ```bash
   ps aux | grep uvicorn
   ```

2. **检查 API 路径**
   ```bash
   curl http://localhost:8000/
   curl http://localhost:8000/health
   ```

3. **测试认证**
   ```bash
   # 测试不需要认证的端点
   curl http://localhost:8000/tasks/
   
   # 测试需要认证的端点（不带令牌）
   curl -X POST http://localhost:8000/tasks/ -H "Content-Type: application/json" -d '{}'
   
   # 测试需要认证的端点（带正确令牌）
   curl -X POST http://localhost:8000/tasks/ -H "Content-Type: application/json" -H "Authorization: Bearer demo-token" -d '{"command": "echo test", "feature_id": "test"}'
   ```

4. **检查日志**
   ```bash
   # 查看服务器日志
   tail -f /path/to/server.log
   ```

## 总结

1. `/tasks` 端点使用 Bearer Token 认证
2. 默认令牌是 `demo-token`
3. 只有修改操作（POST/PUT/DELETE）需要认证
4. 读取操作（GET）通常不需要认证
5. 确保使用正确的 API 路径（检查 `API_PREFIX` 设置）