# 基础任务执行示例

本示例演示如何使用 CodeMCP Executor 执行一个完整的开发任务：实现用户登录功能。

## 示例内容

### 1. 任务定义 (`task_example.json`)
- **任务ID**: TASK-001
- **标题**: 实现用户登录功能
- **类型**: feature (功能实现)
- **优先级**: high (高)
- **描述**: 实现用户登录的API接口和前端页面

### 2. 任务包含的命令
1. **环境准备**: 创建源代码目录结构
2. **API开发**: 创建FastAPI登录接口
3. **前端开发**: 创建HTML登录页面
4. **测试编写**: 创建pytest测试用例
5. **测试执行**: 运行测试验证功能

### 3. 预期结果
- 登录API接口正常工作
- 前端登录表单能够提交和显示结果
- 所有测试用例通过
- 代码结构清晰，符合规范

## 使用步骤

### 步骤1: 准备环境
```bash
# 进入示例目录
cd examples/basic_task_execution

# 检查环境
../../scripts/check_environment.sh
```

### 步骤2: 执行任务
```bash
# 使用execute_task.sh执行任务
../../scripts/execute_task.sh run task_example.json TASK-001
```

### 步骤3: 运行测试
```bash
# 运行测试验证
../../scripts/run_tests.sh run /tmp/codemcp-workspace/TASK-001
```

### 步骤4: 提交结果
```bash
# 首先需要生成结果文件
# 执行任务后会自动生成result.json文件
# 然后提交结果
../../scripts/submit_result.sh submit /tmp/codemcp-workspace/TASK-001/result.json
```

## 完整工作流示例

### 使用主脚本自动执行
```bash
# 启动执行器主循环（会自动执行所有步骤）
../../scripts/codemcp_executor.sh start
```

### 使用命令行工具
```bash
# 使用bin/codemcp-executor工具
../../bin/codemcp-executor execute task_example.json
../../bin/codemcp-executor test /tmp/codemcp-workspace/TASK-001
../../bin/codemcp-executor submit /tmp/codemcp-workspace/TASK-001/result.json
```

## 文件说明

### 生成的文件结构
```
/tmp/codemcp-workspace/TASK-001/
├── task.json                 # 任务定义副本
├── description.txt          # 任务描述
├── commands.json           # 命令列表
├── commands.log            # 命令执行日志
├── command_1.log           # 命令1输出
├── command_2.log           # 命令2输出
├── command_3.log           # 命令3输出
├── command_4.log           # 命令4输出
├── test_login.py           # 生成的测试文件
├── src/
│   ├── api/
│   │   └── login.py       # 生成的API代码
│   └── frontend/
│       └── login.html     # 生成的前端代码
├── tests/
│   └── test_login.py      # 测试文件
├── pytest.log             # pytest输出
└── result.json            # 执行结果
```

### 关键文件内容

#### API代码 (`src/api/login.py`)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(request: LoginRequest):
    # 简单验证逻辑
    if request.username == "admin" and request.password == "password":
        return {"message": "登录成功", "token": "fake-jwt-token"}
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
```

#### 测试代码 (`tests/test_login.py`)
```python
import pytest
from fastapi.testclient import TestClient
from src.api.login import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/login",
        json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert response.json()["message"] == "登录成功"
    assert "token" in response.json()

def test_login_failure():
    response = client.post("/api/login",
        json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"
```

## 验证结果

### 检查执行状态
```bash
# 查看命令执行日志
cat /tmp/codemcp-workspace/TASK-001/commands.log

# 查看测试结果
cat /tmp/codemcp-workspace/TASK-001/pytest.log

# 查看最终结果
cat /tmp/codemcp-workspace/TASK-001/result.json | jq .
```

### 手动测试API
```bash
# 启动API服务器（需要安装fastapi和uvicorn）
cd /tmp/codemcp-workspace/TASK-001
uvicorn src.api.login:app --reload --port 8001 &

# 测试API
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 预期输出: {"message":"登录成功","token":"fake-jwt-token"}
```

## 扩展示例

### 自定义任务
修改 `task_example.json` 可以创建不同的任务：
- 修改 `commands` 数组定义不同的执行步骤
- 修改 `dependencies` 指定不同的依赖
- 修改 `success_criteria` 定义不同的验收标准

### 集成到实际工作流
1. 将任务文件保存到版本控制系统
2. 配置持续集成流水线
3. 设置自动触发条件
4. 集成到项目开发流程

## 故障排除

### 常见问题
1. **命令执行失败**: 检查命令语法和工作目录权限
2. **测试失败**: 检查测试代码和依赖安装
3. **API无法启动**: 检查端口占用和依赖安装
4. **结果提交失败**: 检查服务器连接和API密钥

### 调试技巧
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 手动执行命令
cd /tmp/codemcp-workspace/TASK-001
bash -x ../../scripts/execute_task.sh run task_example.json TASK-001

# 查看详细错误信息
tail -f ~/.codemcp-executor.log
```

## 下一步
- 尝试修改任务定义创建不同的功能
- 集成到真实的CodeMCP服务器
- 配置自动化的任务调度
- 扩展执行器支持更多开发语言和框架