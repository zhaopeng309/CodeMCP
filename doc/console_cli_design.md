# Console CLI 命令规范

## 概述
Console 是 CodeMCP 的管理控制台，提供人类干预与实时审计功能。采用 Typer 框架构建 CLI，结合 python-prompt-toolkit 实现"常驻终端"交互体验。

## 设计理念
1. **常驻终端**: 类似 `htop` 或 `k9s` 的交互式界面
2. **实时更新**: 自动刷新显示任务状态和事件
3. **多面板布局**: 同时显示队列状态、任务日志、系统统计等信息
4. **快捷键操作**: 支持键盘快捷键快速执行命令
5. **颜色编码**: 使用颜色区分不同状态（成功/失败/进行中）

## 技术栈
- **CLI框架**: Typer（基于 Click）
- **交互式界面**: python-prompt-toolkit
- **异步支持**: asyncio
- **颜色输出**: rich 或 colorama
- **配置管理**: pydantic-settings

## 运行模式

### 1. 交互式常驻模式（默认）
```bash
codemcp
```
启动全屏交互式终端，包含多个面板：
- 顶部状态栏：系统概览
- 左侧面板：任务队列
- 中间面板：实时日志
- 右侧面板：系统统计
- 底部命令栏：快捷键提示

### 2. 命令行模式
```bash
codemcp <command> [options]
```
传统的命令行接口，适合脚本化操作。

## 命令设计

### 核心命令

#### `codemcp monitor`
实时监控任务执行情况

**选项**:
- `--follow, -f`: 实时流式输出（类似 `tail -f`）
- `--system <id>`: 只监控指定系统
- `--interval <seconds>`: 刷新间隔，默认 2 秒
- `--format <format>`: 输出格式（text, json, table）

**交互模式特性**:
- 使用 `j/k` 键上下滚动
- 使用 `f` 键切换 follow 模式
- 使用 `s` 键选择不同系统
- 使用 `q` 键退出

#### `codemcp queue`
队列管理命令

**子命令**:
- `queue status`: 显示队列状态
- `queue pause [--reason <text>]`: 暂停任务分发
- `queue resume`: 恢复任务分发
- `queue clear [--system <id>] [--block <id>]`: 清空队列
- `queue stats`: 队列统计信息

#### `codemcp task`
任务管理命令

**子命令**:
- `task list [--status <status>]`: 列出任务
- `task show <task_id>`: 显示任务详情
- `task retry <task_id> [--force]`: 重试失败任务
- `task abort <task_id> [--reason <text>]`: 中止任务
- `task prioritize <task_id> --priority <level>`: 调整任务优先级

#### `codemcp system`
系统管理命令

**子命令**:
- `system list`: 列出所有系统
- `system create <name> [--description <text>]`: 创建新系统
- `system show <system_id>`: 显示系统详情
- `system stats <system_id>`: 系统统计信息
- `system archive <system_id>`: 归档系统

#### `codemcp status`
状态统计命令

**选项**:
- `--system <id>`: 指定系统
- `--detailed, -d`: 显示详细信息
- `--format <format>`: 输出格式

#### `codemcp config`
配置管理命令

**子命令**:
- `config show`: 显示当前配置
- `config set <key> <value>`: 设置配置项
- `config reset`: 重置为默认配置

## 交互式界面设计

### 布局结构
```
┌─────────────────────────────────────────────────────────────────────┐
│ CodeMCP Console v1.0.0                    [Q]退出 [H]帮助 [R]刷新   │
├─────────────────────────────────────────────────────────────────────┤
│ 系统: 用户管理系统 (ID:1) │ 完成率: 40% │ 队列: 15待处理 │ 窗口: 2/5 │
├──────┬──────────────────────────────────────────────────────┬──────┤
│      │                                                      │      │
│ 任务 │                      实时日志                        │ 统计 │
│ 队列 │                                                      │ 面板 │
│      │  [10:00:01] 任务 #101 开始执行: 创建用户表           │      │
│ 1. #101 │               [10:00:45] 测试通过: 10 passed     │ ████ │
│   创建用│               [10:01:00] 任务 #101 完成 (45.2s)  │ ████ │
│ 2. #102 │               [10:01:30] 任务 #102 开始执行      │ ████ │
│   用户CR│                                                    │      │
│ 3. #103 │                                                    │      │
│   用户注│                                                    │      │
│      │                                                      │      │
├──────┴──────────────────────────────────────────────────────┴──────┤
│ 命令: monitor | queue | task | system | status | config | help     │
└─────────────────────────────────────────────────────────────────────┘
```

### 面板说明

#### 1. 任务队列面板（左侧）
- 显示当前执行窗口中的任务
- 颜色编码：绿色（进行中）、黄色（待处理）、红色（失败）、灰色（完成）
- 显示任务ID、简要描述、状态、优先级

#### 2. 实时日志面板（中间）
- 流式显示任务执行日志
- 包含时间戳、事件类型、详细信息
- 支持过滤和搜索

#### 3. 统计面板（右侧）
- 系统完成率图表
- 今日任务统计
- 成功率/失败率
- 平均执行时间

### 快捷键设计

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Q` | 退出 | 退出应用程序 |
| `H` | 帮助 | 显示快捷键帮助 |
| `R` | 刷新 | 手动刷新界面 |
| `F` | 跟随模式 | 切换自动滚动 |
| `J/K` | 上下滚动 | 在面板间导航 |
| `TAB` | 切换面板 | 在三个面板间切换 |
| `1-5` | 选择任务 | 选择任务进行操作 |
| `P` | 暂停队列 | 暂停任务分发 |
| `S` | 恢复队列 | 恢复任务分发 |
| `C` | 清空队列 | 清空待处理任务 |
| `M` | 监控模式 | 进入全屏监控 |

## 配置系统

### 配置文件位置
- `~/.config/codemcp/config.toml` (Linux/macOS)
- `%APPDATA%\codemcp\config.toml` (Windows)

### 配置项示例
```toml
[server]
url = "http://localhost:8000"
api_key = ""  # 可选

[ui]
refresh_interval = 2
theme = "dark"
show_timestamps = true
log_level = "INFO"

[monitor]
default_system = 1
follow_mode = true
max_log_lines = 1000

[colors]
success = "green"
failure = "red"
warning = "yellow"
info = "blue"
```

## 命令实现示例

### Typer + prompt-toolkit 集成
```python
import typer
from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.key_binding import KeyBindings

app = typer.Typer()

class InteractiveConsole:
    def __init__(self):
        self.running = True
        self.layout = self.create_layout()
        self.kb = self.create_key_bindings()
        
    def create_layout(self):
        # 创建多面板布局
        header = Label("CodeMCP Console - 按 [Q] 退出, [H] 帮助")
        task_panel = TextArea(text="任务队列...", read_only=True)
        log_panel = TextArea(text="实时日志...", read_only=True)
        stats_panel = TextArea(text="统计信息...", read_only=True)
        
        # 使用HSplit和VSplit创建复杂布局
        # ...
        
    def create_key_bindings(self):
        kb = KeyBindings()
        
        @kb.add("q")
        def _(event):
            "退出应用程序"
            event.app.exit()
            
        @kb.add("r")
        def _(event):
            "刷新界面"
            self.refresh()
            
        return kb
    
    def run(self):
        application = Application(
            layout=self.layout,
            key_bindings=self.kb,
            full_screen=True,
            refresh_interval=2  # 每2秒自动刷新
        )
        application.run()

@app.command()
def monitor(
    follow: bool = typer.Option(False, "--follow", "-f"),
    system_id: int = typer.Option(None, "--system"),
):
    """实时监控任务执行情况"""
    if typer.get_terminal_size().columns < 80:
        # 终端太小，使用简单输出
        run_simple_monitor(follow, system_id)
    else:
        # 启动交互式界面
        console = InteractiveConsole()
        console.run()

# 其他命令实现...
```

## 错误处理

### 错误类型
1. **连接错误**: 无法连接到 Gateway
2. **API错误**: Gateway 返回错误响应
3. **配置错误**: 配置文件格式错误
4. **权限错误**: 无权限执行操作

### 错误显示
- 在交互式界面中显示红色错误消息
- 在命令行模式中返回非零退出码
- 提供详细的错误信息和解决建议

## 日志系统

### 日志级别
- `DEBUG`: 调试信息
- `INFO`: 常规信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 日志输出
- 控制台：彩色输出
- 文件：`~/.cache/codemcp/console.log`
- 支持日志轮转

## 安装与使用

### 安装
```bash
pip install codemcp-console
```

### 快速开始
```bash
# 启动交互式控制台
codemcp

# 监控特定系统
codemcp monitor --system 1 --follow

# 暂停队列
codemcp queue pause --reason "人工代码审查"

# 查看系统状态
codemcp status --detailed
```

## 下一步
1. 设计具体的 UI 组件和布局
2. 实现异步数据获取和更新
3. 设计主题系统（深色/浅色模式）
4. 实现配置管理
5. 编写完整的快捷键处理逻辑